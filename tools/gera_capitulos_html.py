#!/usr/bin/env python3
"""Gera fontes Liquid de capítulos bíblicos a partir de um TXT.

Formato:

    A purificação do leproso (Lc 5:12-16)
    1 Primeiro versículo.
    2 Segundo versículo.

    3 Outro parágrafo da mesma perícope.
    --
    A cura de outro enfermo
    4 Próximo versículo.

Uma linha em branco inicia outro parágrafo; ``--`` inicia outra perícope.
Versículos podem usar ``capítulo:versículo`` ou apenas ``versículo`` quando
``--chapter`` foi informado. O marcador ``<rl>...</rl>`` vira uma marcação
``<span class="redletter">...</span>`` no conteúdo.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


VERSE_RE = re.compile(r"^\s*(?:(\d+)\s*:\s*)?(\d+)\s+(.+?)\s*$")
PERICOPE_CONCORDANCE_RE = re.compile(r"^(.*?)\s*\(([^()]*)\)\s*$")
REDLETTER_TAG_RE = re.compile(r"</?rl>", re.IGNORECASE)
SLUG_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")


@dataclass
class Verse:
    number: int
    text: str


@dataclass
class Pericope:
    title: str
    concordance: str = ""
    paragraphs: list[list[Verse]] = field(default_factory=list)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = SLUG_SEPARATOR_RE.sub("", ascii_value)
    if not slug:
        raise ValueError("O nome do livro nao produz um slug valido.")
    return slug


def split_title_and_concordance(value: str) -> tuple[str, str]:
    match = PERICOPE_CONCORDANCE_RE.fullmatch(value.strip())
    if not match:
        return value.strip(), ""

    title, concordance = match.groups()
    title = title.strip()
    concordance = concordance.strip()
    return (title, concordance) if title else (value.strip(), "")


def parse_source(
    source: str, default_chapter: int | None = None
) -> dict[int, list[Pericope]]:
    chapters: dict[int, list[Pericope]] = {}
    current_chapter = default_chapter
    current_pericope: Pericope | None = None
    current_paragraph: list[Verse] = []
    pending_title: str | None = None

    def flush_paragraph() -> None:
        nonlocal current_paragraph
        if current_pericope is not None and current_paragraph:
            current_pericope.paragraphs.append(current_paragraph)
        current_paragraph = []

    def flush_pericope(line_number: int) -> None:
        nonlocal current_pericope
        flush_paragraph()
        if current_pericope is None:
            return
        if not current_pericope.paragraphs:
            raise ValueError(
                f"Linha {line_number}: a pericope {current_pericope.title!r} nao tem versiculos."
            )
        if current_chapter is None:
            raise ValueError(f"Linha {line_number}: pericope sem capitulo definido.")
        chapters.setdefault(current_chapter, []).append(current_pericope)
        current_pericope = None

    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue

        if line == "--":
            flush_pericope(line_number)
            pending_title = None
            continue

        match = VERSE_RE.fullmatch(line)
        if match:
            explicit_chapter, verse_number, text = match.groups()
            chapter = int(explicit_chapter) if explicit_chapter else current_chapter
            if chapter is None:
                raise ValueError(
                    f"Linha {line_number}: informe --chapter ou use capitulo:versiculo."
                )
            if chapter < 1:
                raise ValueError(f"Linha {line_number}: o capitulo deve ser maior que zero.")

            verse_number = int(verse_number)
            if verse_number < 1:
                raise ValueError(f"Linha {line_number}: o versiculo deve ser maior que zero.")

            if current_chapter != chapter:
                flush_pericope(line_number)
                current_chapter = chapter

            if current_pericope is None:
                if pending_title is None:
                    raise ValueError(
                        f"Linha {line_number}: versiculo sem titulo de pericope."
                    )
                title, concordance = split_title_and_concordance(pending_title)
                if not title:
                    raise ValueError(
                        f"Linha {line_number}: titulo de pericope vazio."
                    )
                current_pericope = Pericope(title, concordance)
                pending_title = None
            elif pending_title is not None:
                raise ValueError(
                    f"Linha {line_number}: use uma linha '--' antes do proximo titulo."
                )

            current_paragraph.append(Verse(verse_number, text))
            continue

        if current_pericope is not None or current_paragraph:
            raise ValueError(
                f"Linha {line_number}: titulo encontrado dentro de uma pericope; "
                "separe as pericopes com uma linha contendo apenas '--'."
            )
        if pending_title is not None:
            raise ValueError(
                f"Linha {line_number}: titulo sem versiculos antes do proximo titulo."
            )
        pending_title = line

    flush_pericope(len(source.splitlines()) + 1)
    if pending_title is not None:
        raise ValueError(f"Titulo sem versiculos: {pending_title!r}.")
    if not chapters:
        raise ValueError("Nenhum versiculo foi encontrado no arquivo de entrada.")

    return chapters


def convert_redletter(text: str, line_description: str) -> str:
    depth = 0
    for match in REDLETTER_TAG_RE.finditer(text):
        is_closing = match.group().startswith("</")
        if is_closing:
            depth -= 1
            if depth < 0:
                raise ValueError(
                    f"{line_description}: marcador </rl> sem <rl> correspondente."
                )
        else:
            depth += 1
            if depth > 1:
                raise ValueError(f"{line_description}: marcadores <rl> nao podem ser aninhados.")

    if depth:
        raise ValueError(f"{line_description}: marcador <rl> sem fechamento </rl>.")

    return REDLETTER_TAG_RE.sub(
        lambda match: (
            '<span class="redletter">'
            if not match.group().startswith("</")
            else "</span>"
        ),
        text,
    )


def liquid_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_chapter(
    book_name: str,
    book_abbrev: str,
    book_slug: str,
    chapter: int,
    pericopes: list[Pericope],
) -> str:
    sections: list[str] = []
    for pericope in pericopes:
        lines = [
            f"{{% pericope {liquid_string(pericope.title)}, "
            f"{liquid_string(pericope.concordance)} %}}"
        ]

        for paragraph in pericope.paragraphs:
            for verse in paragraph:
                text = convert_redletter(
                    verse.text,
                    f"Capitulo {chapter}, versiculo {verse.number}",
                )
                lines.append(
                    f"{{% verse bookAbbrev bookChapter {verse.number} %}}"
                    f"{text}{{% endverse %}}"
                )
            lines.append("")

        lines.append("{% endpericope %}")
        sections.append("\n".join(lines))

    front_matter = "\n".join(
        (
            "---",
            f"bookName: {liquid_string(book_name)}",
            f"bookAbbrev: {liquid_string(book_abbrev)}",
            f"bookChapter: {chapter}",
            f"permalink: \"/biblia/{book_slug}/{chapter}/\"",
            "bee: true",
            "---",
        )
    )
    header = (
        "{% render 'bibleChapterHeader.liquid', bookName: bookName, "
        "bookAbbrev: bookAbbrev, bookChapter: bookChapter %}"
    )
    return f"{front_matter}\n{header}\n\n" + "\n\n".join(sections) + "\n</div>\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Arquivo TXT de entrada")
    parser.add_argument(
        "--book-name",
        required=True,
        help="Nome exibido do livro, por exemplo: Mateus",
    )
    parser.add_argument(
        "--book-abbrev",
        "--id-prefix",
        dest="book_abbrev",
        help="Abreviacao usada nos IDs dos versiculos (padrao: slug do livro)",
    )
    parser.add_argument(
        "--chapter",
        type=int,
        help="Capitulo padrao quando os versiculos nao incluem capitulo:",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("src/biblia/nt"),
        help="Pasta raiz dos livros (padrao: src/biblia/nt)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescreve arquivos Liquid existentes",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.chapter is not None and args.chapter < 1:
        raise ValueError("--chapter deve ser maior que zero.")

    book_slug = slugify(args.book_name)
    book_abbrev = (args.book_abbrev or book_slug).lower()
    if not re.fullmatch(r"[a-z0-9]+", book_abbrev, flags=re.IGNORECASE):
        raise ValueError("--book-abbrev deve conter apenas letras e numeros.")

    chapters = parse_source(args.input.read_text(encoding="utf-8"), args.chapter)
    book_destination = args.destination / book_slug
    rendered_chapters = [
        (
            chapter,
            book_destination / f"{chapter}.liquid",
            render_chapter(
                args.book_name,
                book_abbrev,
                book_slug,
                chapter,
                pericopes,
            ),
        )
        for chapter, pericopes in chapters.items()
    ]

    existing_targets = [
        output_path
        for _, output_path, _ in rendered_chapters
        if output_path.exists() and not args.force
    ]
    if existing_targets:
        names = "\n".join(f"- {path}" for path in existing_targets)
        raise FileExistsError(
            f"Arquivos Liquid ja existem; use --force para sobrescrever:\n{names}"
        )

    conflicting_sources = []
    for chapter, output_path, _ in rendered_chapters:
        candidates = (
            output_path.with_suffix(".html"),
            output_path.with_suffix(".md"),
            book_destination / str(chapter) / f"{chapter}.html",
            book_destination / str(chapter) / f"{chapter}.liquid",
            book_destination / str(chapter) / f"{chapter}.md",
        )
        conflicting_sources.extend(
            path for path in candidates if path.exists()
        )
    if conflicting_sources:
        names = "\n".join(f"- {path}" for path in conflicting_sources)
        raise FileExistsError(
            "Ja existem fontes para o mesmo capitulo; evite permalinks duplicados:\n"
            f"{names}"
        )

    for chapter, output_path, rendered in rendered_chapters:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"Gerado: {output_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, FileExistsError) as error:
        raise SystemExit(f"Erro: {error}")
