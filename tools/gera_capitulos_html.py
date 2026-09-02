#!/usr/bin/env python3
"""Gera paginas HTML de capitulos a partir de um TXT de traducao.

Formato aceito:

    Titulo da pericope
    1:1 Primeiro versiculo
    2 Segundo versiculo do mesmo capitulo

O prefixo ``capitulo:`` e opcional depois que o primeiro capitulo foi
identificado. Uma linha sem numero inicia uma nova pericope.
"""

from __future__ import annotations

import argparse
import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


VERSE_RE = re.compile(r"^\s*(?:(\d+)\s*:\s*)?(\d+)\s+(.+?)\s*$")
SLUG_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class Verse:
    chapter: int
    number: int
    text: str


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = SLUG_SEPARATOR_RE.sub("", ascii_value)
    if not slug:
        raise ValueError("O nome do livro nao produz um slug valido.")
    return slug


def parse_source(source: str, default_chapter: int | None = None) -> dict[int, list[tuple[str, list[Verse]]]]:
    chapters: dict[int, list[tuple[str, list[Verse]]]] = {}
    current_chapter: int | None = None
    current_pericope: tuple[str, list[Verse]] | None = None
    pending_title: str | None = None

    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        match = VERSE_RE.match(line)
        if match:
            explicit_chapter, verse_number, text = match.groups()
            chapter = int(explicit_chapter) if explicit_chapter else (current_chapter or default_chapter)
            if chapter is None:
                raise ValueError(f"Linha {line_number}: versiculo sem capitulo.")

            if current_chapter != chapter:
                current_chapter = chapter
                current_pericope = None

            if current_pericope is None:
                current_pericope = (pending_title or "Texto biblico", [])
                chapters.setdefault(chapter, []).append(current_pericope)
                pending_title = None

            current_pericope[1].append(Verse(chapter, int(verse_number), text))
            continue

        pending_title = line
        if current_chapter is not None:
            current_pericope = (line, [])
            chapters.setdefault(current_chapter, []).append(current_pericope)

    if not chapters or not any(verses for groups in chapters.values() for _, verses in groups):
        raise ValueError("Nenhum versiculo foi encontrado no arquivo de entrada.")

    for chapter, groups in chapters.items():
        chapters[chapter] = [(title, verses) for title, verses in groups if verses]

    return chapters


def render_chapter(book_name: str, book_slug: str, id_prefix: str, chapter: int, groups: list[tuple[str, list[Verse]]]) -> str:
    sections = []
    for title, verses in groups:
        verse_markup = "\n".join(
            f'\t\t\t<span id="{id_prefix}_{chapter}-{verse.number}" class="verse">\n'
            f'\t\t\t\t<span class="verse-number">{verse.number}</span>\n'
            f'\t\t\t\t<span class="verse-text">{html.escape(verse.text, quote=False)}</span>\n'
            "\t\t\t</span>"
            for verse in verses
        )
        sections.append(
            f'''\t<h4 class="pericope title">
\t\t{html.escape(title, quote=False)}
\t\t<small class="pericope concordance"></small>
\t</h4>

\t<div class="pericope text">
\t\t<p>
{verse_markup}
\n\t\t</p>
\t</div>'''
        )

    return f'''---
bookName: "{book_name.replace('"', '\\"')}"
bookChapter: {chapter}
permalink: "/biblia/{book_slug}/{chapter}/"
bee: true
---

<div class="page-header">
\t<a href="{{{{ '/biblia/' | url }}}}{{{{ bookName | downcase }}}}/{{{{ bookChapter | minus: 1 }}}}"
\t\ttitle="{{{{ bookName }}}} {{{{ bookChapter | minus: 1 }}}}">◄</a>

\t<h3>{{{{bookName}}}} {{{{bookChapter}}}}</h3>

\t<a href="{{{{ '/biblia/' | url }}}}{{{{ bookName | downcase }}}}/{{{{ bookChapter | plus: 1 }}}}"
\t\ttitle="{{{{ bookName }}}} {{{{ bookChapter | plus: 1 }}}}">►</a>
</div>

<div class="content-container">

{chr(10).join(sections)}

</div>
<footer class="chapter-footer">
</footer>
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Arquivo TXT de entrada")
    parser.add_argument("--book-name", required=True, help="Nome exibido do livro, por exemplo: Mateus")
    parser.add_argument("--chapter", type=int, help="Numero do capitulo quando o TXT contem apenas versiculos")
    parser.add_argument("--id-prefix", help="Prefixo dos IDs dos versiculos, por exemplo: mt (padrao: slug do livro)")
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("src/biblia/nt"),
        help="Pasta que recebera a pasta do livro (padrao: src/biblia/nt)",
    )
    parser.add_argument("--force", action="store_true", help="Sobrescreve arquivos HTML existentes")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    book_slug = slugify(args.book_name)
    chapters = parse_source(args.input.read_text(encoding="utf-8"), args.chapter)
    id_prefix = args.id_prefix or book_slug
    book_destination = args.destination / book_slug
    output_paths = [book_destination / str(chapter) / f"{chapter}.html" for chapter in chapters]

    existing = [path for path in output_paths if path.exists()]
    if existing and not args.force:
        names = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"Arquivos ja existem; use --force para sobrescrever:\n{names}")

    for chapter, groups in chapters.items():
        output_path = book_destination / str(chapter) / f"{chapter}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_chapter(args.book_name, book_slug, id_prefix, chapter, groups), encoding="utf-8")
        print(f"Gerado: {output_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, FileExistsError) as error:
        raise SystemExit(f"Erro: {error}")