"""Testes locais: nenhuma chamada real à API."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "traduz_capitulos", ROOT / "tools/biblech/traduz_capitulos.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.source = {"chapter": 1, "pericopes": [{"id": "P1", "title": "Teste",
            "start_verse": 1, "end_verse": 2,
            "verses": [{"verse": 1, "tokens": [{"lemma": "λόγος"}]},
                       {"verse": 2, "tokens": [{"lemma": "θεός"}]}]}]}
        self.result = {"chapter": 1, "pericopes": [{"id": "P1", "title": "Teste",
            "verses": [{"number": 1, "text": "Uma palavra.", "paragraph_start": False},
                       {"number": 2, "text": "Deus.", "paragraph_start": True}]}],
            "notes": [], "review_points": ["Revisar a tradução."]}

    def test_converter_and_paragraphs(self):
        text, notes = t.render_result(self.result, self.source)
        self.assertEqual(text, "Teste\n1 Uma palavra.\n\n2 Deus.\n")
        self.assertIn("revisão humana pendente", notes)

    def test_rejects_missing_duplicate_extra_and_reordered_verses(self):
        for numbers in ([1], [1, 1], [1, 2, 3], [2, 1]):
            result = copy.deepcopy(self.result)
            result["pericopes"][0]["verses"] = [
                {"number": n, "text": "Texto.", "paragraph_start": False} for n in numbers]
            with self.subTest(numbers=numbers), self.assertRaises(ValueError):
                t.render_result(result, self.source)

    def test_rejects_structure_injection_and_unbalanced_quotes(self):
        for text in ("Texto\n--\nOutro título", "3 Texto", "<script>x</script>", "“Texto"):
            result = copy.deepcopy(self.result)
            result["pericopes"][0]["verses"][0]["text"] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                t.render_result(result, self.source)

    def test_source_divergence_is_not_silently_normalized_away(self):
        morphology = {1: "λογος 3056 {N-NSM}", 2: "θεος 2316 {N-NSM}"}
        t.check_sources(self.source, morphology)
        morphology[2] = "κοσμος 2889 {N-NSM}"
        with self.assertRaises(ValueError):
            t.check_sources(self.source, morphology)

    def test_iota_subscript_is_not_expanded_by_search_normalization(self):
        self.assertEqual(t.normalized("Ἡρῴδης"), t.normalized("ηρωδης"))
        self.assertEqual(t.normalized("τῷ"), t.normalized("τω"))
        self.assertEqual(t.normalized("ὦ "), t.normalized("ω"))

    def test_homographs_are_candidates_not_automatic_choices(self):
        dictionary = {"τίς": {"pt": "quem"}, "τις": {"pt": "alguém"}}
        chapter = {"pericopes": [{"verses": [{"tokens": [{"lemma": "τίς"}]}]}]}
        packet = t.lexical_packet(chapter, dictionary, t.lexical_index(dictionary))
        self.assertEqual(len(packet[0]["candidatos"]), 2)
        self.assertEqual(packet[0]["candidatos"][0]["correspondencia"], "exata")
        self.assertIn("requer conferência", packet[0]["candidatos"][1]["correspondencia"])
        self.assertNotIn("traducao_escolhida", packet[0])

    def test_refusal_and_incomplete_response(self):
        for response in ({"status": "incomplete"}, {"status": "completed", "output": [
                {"type": "message", "content": [{"type": "refusal"}]}]}):
            with self.assertRaises(ValueError):
                t.extract_result(response)

    def test_complete_response_ignores_reasoning_items(self):
        response = {"status": "completed", "output": [{"type": "reasoning"},
            {"type": "message", "content": [{"type": "output_text",
                "text": json.dumps(self.result)}]}]}
        self.assertEqual(t.extract_result(response), self.result)

    def test_resume_rejects_changed_sources_and_edited_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "1.txt").write_bytes(b"original")
            manifest = {"status": "rascunho_validado", "fingerprint": "abc",
                        "files": {"1.txt": t.digest(b"original")}}
            (folder / "manifest.json").write_bytes(t.encoded(manifest))
            t.verify_resume(folder, "abc")
            with self.assertRaises(ValueError):
                t.verify_resume(folder, "changed")
            (folder / "1.txt").write_bytes(b"edited")
            with self.assertRaises(ValueError):
                t.verify_resume(folder, "abc")

    def test_network_failure_is_not_retried(self):
        with patch.object(t.urllib.request, "urlopen", side_effect=urllib.error.URLError("x")) as api:
            with self.assertRaises(ValueError):
                t.call_api({}, "fake-test-key", 1, 2)
            self.assertEqual(api.call_count, 1)

    def test_retry_only_transient_http_errors(self):
        error = urllib.error.HTTPError(t.API_URL, 429, "limit", {}, None)
        with patch.object(t.urllib.request, "urlopen", side_effect=error) as api, patch.object(t.time, "sleep"):
            with self.assertRaises(ValueError):
                t.call_api({}, "fake-test-key", 1, 2)
            self.assertEqual(api.call_count, 3)

    def test_ranges(self):
        self.assertEqual(t.chapter_numbers("14,16-18", range(1, 29)), [14, 16, 17, 18])
        for invalid in ("0", "18-14", "29", "1;2"):
            with self.assertRaises(ValueError):
                t.chapter_numbers(invalid, range(1, 29))

    def test_never_overwrites_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "existing.txt"
            path.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                t.write_new(path, b"replace")
            self.assertEqual(path.read_bytes(), b"keep")

    def test_full_run_and_resume_with_mock_api(self):
        source = next(c for c in json.loads((ROOT / "src/interlinear/nt/MT.json").read_text())
                      if c["chapter"] == 14)
        result = {"chapter": 14, "pericopes": [{"id": p["id"], "title": p["title"],
            "verses": [{"number": v["verse"], "text": "Texto simulado para teste.",
                        "paragraph_start": False} for v in p["verses"]]}
            for p in source["pericopes"]], "notes": [], "review_points": []}
        response = {"status": "completed", "id": "mock-response", "usage": {},
                    "output": [{"type": "message", "content": [{"type": "output_text",
                                "text": json.dumps(result)}]}]}
        dictionary = ROOT / "src/_data/nt/dict_flex_nt-lxx_greek-pt.json"
        before = t.digest(dictionary.read_bytes())
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"OPENAI_API_KEY": "fake-test-key"}), \
                patch.object(t, "call_api", return_value=response) as api:
            options = ["--chapters", "14", "--use-api", "--model", "mock-model", "--output", tmp, "--resume"]
            t.run(t.parser().parse_args(options))
            folder = Path(tmp) / "14"
            self.assertTrue((folder / "14.txt").is_file())
            self.assertIn("pendente", (folder / "manifest.json").read_text())
            self.assertNotIn("fake-test-key", (folder / "request.json").read_text())
            t.run(t.parser().parse_args(options))
            self.assertEqual(api.call_count, 1)
            (folder / "14.txt").write_text("Edição humana", encoding="utf-8")
            with self.assertRaises(ValueError):
                t.run(t.parser().parse_args(options))
            self.assertEqual(api.call_count, 1)
        self.assertEqual(before, t.digest(dictionary.read_bytes()))

    def test_default_local_run_cannot_call_api_even_with_credentials(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
                "OPENAI_API_KEY": "fake-test-key", "OPENAI_MODEL": "unused-model"}), \
                patch.object(t, "call_api", side_effect=AssertionError("Rede proibida")) as api:
            options = ["--chapters", "14", "--output", tmp, "--resume"]
            t.run(t.parser().parse_args(options))
            folder = Path(tmp) / "14"
            manifest = json.loads((folder / "manifest.json").read_text())
            self.assertEqual(manifest["mode"], "local")
            self.assertIsNone(manifest["model"])
            self.assertIn(" | ", (folder / "14.txt").read_text())
            self.assertTrue((folder / "alinhamento.json").is_file())
            t.run(t.parser().parse_args(options))
            api.assert_not_called()

    def test_mechanical_draft_marks_ambiguous_and_missing_forms(self):
        dictionary = {"λόγος": {"pt": "palavra"}, "θεός": {"pt": "deus"},
                      "θεὸς": {"pt": "deus"}}
        morphology = {1: "λογος 3056 {N-NSM}", 2: "θεος 2316 {N-NSM}"}
        text, notes, alignment = t.mechanical_draft(
            self.source, dictionary, t.lexical_index(dictionary), morphology)
        self.assertIn("1 palavra", text)
        self.assertIn("2 [INCERTO: θεός]", text)
        self.assertIn("tradução contínua e revisão pendentes", notes)
        self.assertEqual(alignment["verses"][1]["tokens"][0]["strong_tm"], "2316")


if __name__ == "__main__":
    unittest.main()
