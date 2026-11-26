"""Testes da adaptação estrutural; não validam escolhas lexicais/exegéticas."""
import copy
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import flexiona_io as storage
from tools import flexiona_verbos as verbs
from tools import flexiona_nao_verbos as nonverbs
from tools import flexiona_todas_traducoes as combined

ROOT = Path(__file__).resolve().parents[1]


def flex(greek, code, morphology, **extra):
    return dict(grego=greek, transliteracao="inalterada", ocorrencias="2",
                traducao="original", pt="original", abrev_morf=code,
                morfologia=morphology, lxx=[], ocorrencias_lxx=3, **extra)


def fixture():
    return {
        "2212": {"lema": "ζητέω", "transliteracao": "zētéō", "verbete": "G2212: buscar",
                 "flexoes": [
                     flex("ζητήσεις", "V-FIA-2S", "Verbo - Futuro Indicativo Ativa - 2ª Pessoa Singular"),
                     flex("ζητήσεις", "V-FIA-2S", "Verbo - Futuro Indicativo Ativa - 2ª Pessoa Singular", verbete="G2212: procurar"),
                 ]},
        "2570": {"lema": "καλός", "transliteracao": "kalós", "pendencias": ["preservar"],
                 "verbetes": ["G2570: bom", "G2570: mau"], "flexoes": [
                     flex("καλῶν", "Adj-GMP", "Adjetivo - Genitivo Masculino Plural", verbete="G2570: bom"),
                     flex("καλῶν", "Adj-GMP", "Adjetivo - Genitivo Masculino Plural", verbete="G2570: mau"),
                 ]},
    }


class AdaptationTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()
        self.original = copy.deepcopy(self.data)

    def assert_only_translations_changed(self, changed):
        restored = copy.deepcopy(changed)
        for code, group in restored.items():
            for old, new in zip(self.original[code]["flexoes"], group["flexoes"]):
                for field in ("pt", "traducao"):
                    new[field] = old[field]
        self.assertEqual(restored, self.original)
        self.assertEqual(self.data, self.original)

    def test_verbs_inherit_common_and_respect_override_without_collapsing_forms(self):
        changed = verbs.transform_dictionary(self.data, verbs.PortugueseConjugator())
        self.assertEqual([f["pt"] for f in changed["2212"]["flexoes"]], ["buscarás", "procurarás"])
        self.assertEqual(changed["2570"], self.data["2570"])
        self.assert_only_translations_changed(changed)

    def test_nominals_keep_variants_and_metadata(self):
        changed = nonverbs.transform_dictionary(self.data, None, nonverbs.PortugueseNominalInflector())
        self.assertEqual([f["pt"] for f in changed["2570"]["flexoes"]], ["dos bons", "dos maus"])
        self.assertEqual(changed["2212"], self.data["2212"])
        self.assert_only_translations_changed(changed)

    def test_filters_use_group_strong_without_rewriting_it(self):
        self.data["2212 "] = self.data.pop("2212")
        changed = verbs.transform_dictionary(self.data, verbs.PortugueseConjugator(), {"2570"})
        self.assertEqual(changed, self.data)
        changed = verbs.transform_dictionary(self.data, verbs.PortugueseConjugator(), {"2212"})
        self.assertIn("2212 ", changed)
        self.assertEqual(changed["2212 "]["flexoes"][0]["pt"], "buscarás")
        self.assertEqual(changed["2570"], self.data["2570"])

    def test_legacy_format_has_same_results_for_each_analysis(self):
        for entry in storage.iter_entries(self.data):
            if entry.strong == "2212":
                lexical = verbs.transform_dictionary(self.data, verbs.PortugueseConjugator())
                legacy = verbs.transform_dictionary({"key": entry.payload}, verbs.PortugueseConjugator())["key"]
            else:
                lexical = nonverbs.transform_dictionary(self.data, None, nonverbs.PortugueseNominalInflector())
                legacy = nonverbs.transform_dictionary({"key": entry.payload}, None, nonverbs.PortugueseNominalInflector())["key"]
            index = int(entry.label.split("[", 1)[1].split("]", 1)[0])
            for field in ("pt", "traducao"):
                self.assertEqual(lexical[entry.strong]["flexoes"][index][field], legacy[field])

    def test_fill_handles_all_selected_strongs_common_variants_and_overrides(self):
        definitions = {"G2212": "procurar", "G2570": "excelente"}
        changed = combined.fill_verbetes(self.data, definitions, {"2212", "2570"})
        self.assertEqual(changed["2212"]["verbete"], "G2212: procurar")
        self.assertEqual(changed["2570"]["verbetes"], ["G2570: excelente"] * 2)
        self.assertEqual(changed["2570"]["flexoes"][0]["verbete"], "G2570: excelente")
        self.assertEqual(self.data, self.original)
        filtered = combined.fill_verbetes(self.data, definitions, {"2212"})
        self.assertEqual(filtered["2570"], self.data["2570"])

    def test_unknown_variant_cannot_be_chosen_arbitrarily(self):
        del self.data["2570"]["flexoes"][0]["verbete"]
        with self.assertRaisesRegex(ValueError, "Verbete não definido"):
            nonverbs.transform_dictionary(self.data, None, nonverbs.PortugueseNominalInflector())

    def test_duplicate_forms_across_strongs_are_all_iterated(self):
        self.data["2570"]["flexoes"][0]["grego"] = "ζητήσεις"
        entries = list(storage.iter_entries(self.data))
        self.assertEqual(len(entries), 4)
        self.assertEqual(sum(e.payload["grego"] == "ζητήσεις" for e in entries), 3)

    def test_preview_filters_each_flexion_and_limit(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            storage.preview(self.data, {"2570"}, 1)
        self.assertEqual(len(output.getvalue().splitlines()), 1)
        self.assertIn("2570[0] καλῶν", output.getvalue())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            storage.preview(self.data, None, 0)
        self.assertEqual(output.getvalue(), "")


class WriterTests(unittest.TestCase):
    def test_patch_preserves_formatting_unicode_escapes_bom_and_newlines(self):
        raw = '\ufeff{\r\n\t"κ": { "grego":"\\u03ba", "pt" : "velho", "traducao":"velha" }\r\n}\r\n'
        updated = json.loads(raw.lstrip("\ufeff"))
        updated["κ"]["pt"] = "novo"
        self.assertEqual(storage._patch_json(raw, updated), raw.replace('"velho"', '"novo"'))

    def test_insert_missing_legacy_pt_without_reordering(self):
        for raw in ['{"κ":{"traducao":"original"}}', '{\n  "κ": {\n    "traducao": "original"\n  }\n}\n']:
            updated = json.loads(raw)
            updated["κ"]["pt"] = "nova"
            text = storage._patch_json(raw, updated)
            self.assertEqual(json.loads(text), updated)
            self.assertIn('"traducao"', text)
            self.assertLess(text.index('"traducao"'), text.index('"pt"'))

    def test_in_place_backup_noop_and_output_template(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "lex.json"
            raw = '{ "κ": {"traducao":"a", "pt":"b"} }\n'
            source.write_text(raw, encoding="utf-8")
            updated = storage.load_dictionary(source)
            updated["κ"]["pt"] = "c"
            output = Path(folder) / "result.json"
            storage.write_dictionary(output, updated, template_path=source)
            self.assertEqual(source.read_text(), raw)
            self.assertEqual(output.read_text(), raw.replace('"b"', '"c"'))
            with contextlib.redirect_stderr(io.StringIO()):
                storage.write_dictionary(source, updated)
            backups = list(Path(folder).glob("lex.json.bak-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), raw)
            storage.write_dictionary(source, updated)
            self.assertEqual(len(list(Path(folder).glob("lex.json.bak-*"))), 1)

    def test_refuse_structural_losses_and_duplicate_json_keys(self):
        with self.assertRaisesRegex(ValueError, "remover ou adicionar análises"):
            storage._patch_json('{"flexoes": [1, 2]}', {"flexoes": [1]})
        with self.assertRaisesRegex(ValueError, "remover campos"):
            storage._patch_json('{"pt":"a"}', {})
        with self.assertRaisesRegex(ValueError, "Chave JSON repetida"):
            storage._patch_json('{"pt":"a","pt":"b"}', {"pt": "b"})


class CliTests(unittest.TestCase):
    def run_cli(self, script, *args, cwd=ROOT):
        run = subprocess.run([sys.executable, "-B", str(ROOT / "tools" / script), *map(str, args)],
                             cwd=cwd, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return run

    def test_all_three_clis_can_write_lexical_copies(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "lex.json"
            source.write_text(json.dumps(fixture(), ensure_ascii=False, indent=2) + "\n")
            original = source.read_bytes()
            for script in ("flexiona_verbos.py", "flexiona_nao_verbos.py", "flexiona_todas_traducoes.py"):
                output = Path(folder) / (script + ".json")
                extra = ["--nofill"] if script == "flexiona_todas_traducoes.py" else []
                self.run_cli(script, "--input", source, "--output", output, *extra)
                result = storage.load_dictionary(output)
                self.assertEqual(len(list(storage.iter_entries(result))), 4)
                self.assertEqual(result["2212"]["lema"], "ζητέω")
                self.assertNotIn("strongs", result["2212"]["flexoes"][0])
                self.assertEqual(source.read_bytes(), original)

    def test_dry_run_and_skip_flags_do_not_write_or_create_backups(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "lex.json"
            source.write_text(json.dumps(fixture(), ensure_ascii=False, indent=2) + "\n")
            original = source.read_bytes()
            for script in ("flexiona_verbos.py", "flexiona_nao_verbos.py", "flexiona_todas_traducoes.py"):
                extra = ["--nofill", "--skip-verbs"] if script == "flexiona_todas_traducoes.py" else []
                run = self.run_cli(script, "--input", source, "--dry-run", "--strong", "2570", "--limit", 1, *extra)
                if script != "flexiona_verbos.py":
                    self.assertIn("2570[0]", run.stdout)
                self.assertEqual(source.read_bytes(), original)
            self.assertEqual(list(Path(folder).iterdir()), [source])

    def test_combined_repeat_filter_and_fill_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "lex.json"
            source.write_text(json.dumps(fixture(), ensure_ascii=False, indent=2) + "\n")
            output = Path(folder) / "out.json"
            self.run_cli("flexiona_todas_traducoes.py", "--input", source, "--output", output,
                         "--strong", "2212", "--strong", "2570", "--skip-verbs", "--skip-nonverbs")
            result = storage.load_dictionary(output)
            self.assertNotEqual(result["2212"]["verbete"], fixture()["2212"]["verbete"])
            self.assertNotEqual(result["2570"]["verbetes"], fixture()["2570"]["verbetes"])
            for group in result.values():
                for entry in group["flexoes"]:
                    self.assertEqual(entry["pt"], "original")

    def test_defaults_are_lexical_and_nofill_does_not_load_strongs(self):
        for module in (verbs, nonverbs, combined):
            with patch.object(sys, "argv", ["script"]):
                self.assertEqual(module.parse_args().input, storage.DEFAULT_INPUT)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "lex.json"
            source.write_text(json.dumps(fixture(), ensure_ascii=False))
            self.run_cli("flexiona_todas_traducoes.py", "--input", source, "--nofill", "--dry-run", cwd=folder)


if __name__ == "__main__":
    unittest.main()
