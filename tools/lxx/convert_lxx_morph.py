#!/usr/bin/env python3
"""Converte JSONs locais do OpenScriptorium para o formato interlinear BEREIA.

Uso: python3 tools/lxx/convert_lxx_morph.py CAMINHO [--overwrite]
CAMINHO pode ser um JSON de livro ou uma pasta contendo os JSONs finais.
Não baixa arquivos, não altera a fonte nem consulta/modifica o dicionário.
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "src/interlinear/at"
SOURCE_BASE_URL = "https://github.com/OpenScriptorium/lxx-morph/blob/master/db/seeds/lxx_morph/"

# Versões textuais distintas sempre recebem arquivos distintos.
BOOK_CODES = dict(pair.split(":") for pair in """
genesis:gn exodus:ex leviticus:lv numbers:nm deuteronomy:dt
joshua:js joshua-a:js-a joshua-b:js-b judges:jz judges-a:jz-a judges-b:jz-b
ruth:rt 1-samuel:1sm 2-samuel:2sm 1-kings:1rs 2-kings:2rs
1-chronicles:1cr 2-chronicles:2cr 1-esdras:1esd 2-esdras:2esd
ezra:ed nehemiah:ne esther:est esther-greek:est judith:jdt
tobit:tb tobit-ba:tb-ba tobit-s:tb-s
1-maccabees:1mc 2-maccabees:2mc 3-maccabees:3mc 4-maccabees:4mc
psalms:sl odes:odes proverbs:pv ecclesiastes:ec song-of-songs:ct
song-of-solomon:ct job:jo wisdom:sb wisdom-of-solomon:sb sirach:eclo
psalms-of-solomon:sl-sal hosea:os amos:am micah:mq joel:jl obadiah:ob
jonah:jn nahum:na habakkuk:hc zephaniah:sf haggai:ag zechariah:zc
malachi:ml isaiah:is jeremiah:jr baruch:br lamentations:lm
letter-of-jeremiah:ep-jr epistle-of-jeremiah:ep-jr ezekiel:ez
susanna:sus susanna-theodotion:sus-th daniel:dn daniel-theodotion:dn-th
bel-and-the-dragon:bel bel-and-the-dragon-theodotion:bel-th
prayer-of-manasseh:or-mn
""".split())


def convert(data, source_name):
    """Preserva ordem, grafia e referência; usa surface, nunca o lema lexical."""
    if not isinstance(data, list) or not data:
        raise ValueError("a fonte deve ser uma lista não vazia de versículos")
    chapters = {}
    seen = set()
    book_ref = None
    for index, row in enumerate(data, 1):
        if not isinstance(row, dict):
            raise ValueError(f"registro {index}: versículo inválido")
        ref = row.get("ref")
        match = re.fullmatch(r"(.+) (\d+):(\d+[a-z]?)", ref) if isinstance(ref, str) else None
        if not match:
            raise ValueError(f"registro {index}: referência não reconhecida: {ref!r}")
        book, chapter, verse_text = match.groups()
        if book_ref is not None and book != book_ref:
            raise ValueError("a fonte contém referências de mais de um livro")
        book_ref = book
        if ref in seen:
            raise ValueError(f"referência duplicada: {ref}")
        seen.add(ref)
        chapter = int(chapter)
        # Sufixos e versículo zero são preservados, sem fusão ou renumeração.
        verse = int(verse_text) if verse_text.isdigit() else verse_text
        words = row.get("words")
        if not isinstance(words, list) or not words:
            raise ValueError(f"{ref}: lista words ausente ou vazia")
        tokens = []
        for position, word in enumerate(words, 1):
            surface = word.get("surface") if isinstance(word, dict) else None
            if not isinstance(surface, str) or not surface.strip():
                raise ValueError(f"{ref}, palavra {position}: surface ausente ou inválido")
            tokens.append({"lemma": surface})
        if chapter not in chapters:
            chapters[chapter] = {
                "chapter": chapter,
                "source_file": source_name,
                "source_url": SOURCE_BASE_URL + source_name,
                "pericopes": [{
                    "id": f"P{len(chapters) + 1:03d}",
                    "title": "",
                    "start_verse": verse,
                    "end_verse": verse,
                    "verses": [],
                }],
            }
        pericope = chapters[chapter]["pericopes"][0]
        pericope["verses"].append({"verse": verse, "tokens": tokens})
        pericope["end_verse"] = verse
    return list(chapters.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON de livro ou pasta de JSONs finais")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--book", help="sigla de saída para um único arquivo, ex.: gn")
    parser.add_argument("--overwrite", action="store_true", help="autoriza substituir saídas existentes")
    args = parser.parse_args()
    try:
        if not args.input.exists():
            raise ValueError(f"entrada inexistente: {args.input}")
        files = sorted(args.input.glob("*.json")) if args.input.is_dir() else [args.input]
        if not files:
            raise ValueError("nenhum JSON encontrado")
        if args.book and (args.input.is_dir() or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.book)):
            raise ValueError("--book exige um arquivo único e uma sigla simples em minúsculas")
        planned = {}
        # Valida o lote completo antes de escrever qualquer saída.
        for source in files:
            code = args.book or BOOK_CODES.get(source.stem)
            if not code:
                raise ValueError(f"livro desconhecido: {source.name}; converta-o individualmente com --book SIGLA")
            target = args.output_dir / f"{code}.json"
            if target.resolve() == source.resolve():
                raise ValueError(f"saída não pode substituir a fonte: {source}")
            if target in planned:
                raise ValueError(f"dois arquivos correspondem à mesma saída: {target.name}")
            if target.exists() and not args.overwrite:
                raise ValueError(f"saída existente: {target}; use --overwrite para substituir")
            data = json.loads(source.read_text(encoding="utf-8"))
            planned[target] = convert(data, source.name)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for target, chapters in planned.items():
            target.write_text(json.dumps(chapters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            verses = sum(len(c["pericopes"][0]["verses"]) for c in chapters)
            print(f"{target}: {len(chapters)} capítulos, {verses} versículos")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Erro: {error}\n")


if __name__ == "__main__":
    main()
