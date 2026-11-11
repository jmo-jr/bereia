import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.biblech.gera_capitulos_html import (
    convert_redletter,
    parse_source,
    render_chapter,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ParseSourceTests(unittest.TestCase):
    def test_blank_lines_group_verses_into_paragraphs_and_separator_starts_pericope(self):
        source = """A purificação do leproso (Lc 5:12-16)
1 Primeiro versículo.
2 Segundo versículo.

3 Outro parágrafo.
--
Outra perícope
4 Próximo versículo.
"""

        chapters = parse_source(source, default_chapter=8)

        self.assertEqual(list(chapters), [8])
        self.assertEqual(len(chapters[8]), 2)
        self.assertEqual(chapters[8][0].title, "A purificação do leproso")
        self.assertEqual(chapters[8][0].concordance, "Lc 5:12-16")
        self.assertEqual(
            [[verse.number for verse in paragraph] for paragraph in chapters[8][0].paragraphs],
            [[1, 2], [3]],
        )
        self.assertEqual(chapters[8][1].title, "Outra perícope")

    def test_explicit_chapter_numbers_split_output_chapters(self):
        source = """Primeira perícope
8:1 Primeiro capítulo.
--
Segunda perícope
9:1 Segundo capítulo.
"""

        chapters = parse_source(source)

        self.assertEqual(list(chapters), [8, 9])
        self.assertEqual(chapters[9][0].paragraphs[0][0].text, "Segundo capítulo.")

    def test_requires_separator_before_next_pericope_title(self):
        with self.assertRaisesRegex(ValueError, "separe as pericopes"):
            parse_source("Primeira perícope\n1 Texto.\nSegunda perícope\n2 Texto.", 1)

    def test_rejects_missing_verse_number_or_chapter(self):
        with self.assertRaisesRegex(ValueError, "Titulo sem versiculos"):
            parse_source("Perícope sem versículos")
        with self.assertRaisesRegex(ValueError, "informe --chapter"):
            parse_source("Perícope\n1 Texto.")
        with self.assertRaisesRegex(ValueError, "capitulo deve ser maior que zero"):
            parse_source("Perícope\n0:1 Texto.")
        with self.assertRaisesRegex(ValueError, "versiculo deve ser maior que zero"):
            parse_source("Perícope\n0 Texto.", default_chapter=1)


class RenderingTests(unittest.TestCase):
    def test_redletter_markers_become_span_markup(self):
        self.assertEqual(
            convert_redletter("Diz: <rl>Venha!</rl>", "versículo 1"),
            'Diz: <span class="redletter">Venha!</span>',
        )

    def test_rejects_unbalanced_redletter_markers(self):
        with self.assertRaisesRegex(ValueError, "sem fechamento"):
            convert_redletter("<rl>Texto", "versículo 1")
        with self.assertRaisesRegex(ValueError, "sem <rl> correspondente"):
            convert_redletter("Texto</rl>", "versículo 1")

    def test_renders_flat_liquid_chapter_with_shortcodes(self):
        pericope = parse_source(
            "A perícope (Lc 1:2)\n1 <rl>Texto</rl>.\n\n2 Segundo parágrafo.",
            default_chapter=3,
        )[3]

        output = render_chapter("Mateus", "mt", "mateus", 3, pericope)

        self.assertIn('bookAbbrev: "mt"', output)
        self.assertIn('permalink: "/biblia/mateus/3/"', output)
        self.assertIn("{% pericope \"A perícope\", \"Lc 1:2\" %}", output)
        self.assertIn(
            '{% verse bookAbbrev bookChapter 1 %}'
            '<span class="redletter">Texto</span>.{% endverse %}',
            output,
        )
        self.assertIn(
            "{% endverse %}\n\n{% verse bookAbbrev bookChapter 2 %}",
            output,
        )
        self.assertIn(
            "{% render 'bibleChapterHeader.liquid', bookName: bookName, "
            "bookAbbrev: bookAbbrev, bookChapter: bookChapter %}",
            output,
        )


class CommandLineTests(unittest.TestCase):
    def test_writes_flat_liquid_file_and_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            input_path = temporary_path / "input.txt"
            destination = temporary_path / "output"
            input_path.write_text(
                "A perícope (Lc 1:2)\n1 <rl>Texto</rl>.",
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(REPOSITORY_ROOT / "tools" / "biblech" / "gera_capitulos_html.py"),
                str(input_path),
                "--book-name",
                "Mateus",
                "--book-abbrev",
                "mt",
                "--chapter",
                "3",
                "--destination",
                str(destination),
            ]

            first_run = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            output_path = destination / "mateus" / "3.liquid"

            self.assertEqual(first_run.returncode, 0, first_run.stderr)
            self.assertTrue(output_path.is_file())
            self.assertIn('<span class="redletter">Texto</span>', output_path.read_text())

            second_run = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(second_run.returncode, 0)
            self.assertIn("Arquivos Liquid ja existem", second_run.stderr)

    def test_batch_generates_liquid_for_all_chapter_txt_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            input_directory = temporary_path / "chapters"
            input_directory.mkdir()
            (input_directory / "1.txt").write_text(
                "Primeira perícope\n1 Texto do primeiro capítulo.",
                encoding="utf-8",
            )
            nested_directory = input_directory / "revisado"
            nested_directory.mkdir()
            (nested_directory / "2.TXT").write_text(
                "Segunda perícope\n1 Texto do segundo capítulo.",
                encoding="utf-8",
            )
            destination = temporary_path / "output"
            command = [
                sys.executable,
                str(REPOSITORY_ROOT / "tools" / "biblech" / "gera_capitulos_html.py"),
                str(input_directory),
                "--batch",
                "--book-name",
                "Mateus",
                "--book-abbrev",
                "mt",
                "--destination",
                str(destination),
            ]

            result = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            first_output = destination / "mateus" / "1.liquid"
            second_output = destination / "mateus" / "2.liquid"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(first_output.is_file())
            self.assertTrue(second_output.is_file())
            self.assertIn("bookChapter: 1", first_output.read_text(encoding="utf-8"))
            self.assertIn("bookChapter: 2", second_output.read_text(encoding="utf-8"))

    def test_batch_requires_chapter_numbers_in_txt_filenames(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            input_directory = temporary_path / "chapters"
            input_directory.mkdir()
            (input_directory / "chapter-one.txt").write_text(
                "Perícope\n1 Texto.",
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(REPOSITORY_ROOT / "tools" / "biblech" / "gera_capitulos_html.py"),
                str(input_directory),
                "--batch",
                "--book-name",
                "Mateus",
                "--destination",
                str(temporary_path / "output"),
            ]

            result = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nome do arquivo TXT deve ser o numero", result.stderr)


if __name__ == "__main__":
    unittest.main()
