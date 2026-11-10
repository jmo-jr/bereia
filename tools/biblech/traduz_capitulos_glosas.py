#!/usr/bin/env python3
"""Produz rascunhos mecânicos de tradução a partir das fontes locais."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]


def normalized(word):
    # Remover os sinais antes de casefold evita expandir o iota subscrito.
    return "".join(c for c in unicodedata.normalize("NFD", word.lower())
                   if not unicodedata.combining(c)).casefold().strip().rstrip("’'")


def chapter_numbers(value, available):
    if value == "all":
        return sorted(available)
    result = set()
    for part in value.split(","):
        if not re.fullmatch(r"[1-9]\d*(?:-[1-9]\d*)?", part):
            raise ValueError("Capítulos: use 14-28, 14,16-18 ou all.")
        bounds = list(map(int, part.split("-")))
        start, end = bounds[0], bounds[-1]
        if end < start:
            raise ValueError("Intervalo de capítulos invertido.")
        result.update(range(start, end + 1))
    if not result or not result <= set(available):
        raise ValueError("O intervalo contém capítulos ausentes no texto-base.")
    return sorted(result)


def lexical_index(dictionary):
    index = {}
    for key in dictionary:
        index.setdefault(normalized(key), []).append(key)
    return index


def lexical_packet(chapter, dictionary, index):
    words = dict.fromkeys(t["lemma"] for p in chapter["pericopes"]
                          for v in p["verses"] for t in v["tokens"])
    fields = ("grego", "strongs", "transliteracao", "verbete", "traducao", "pt",
              "abrev_morf", "morfologia", "ocorrencias")
    result = []
    for word in words:
        # A grafia original tem precedência; a busca normalizada é fallback.
        keys = [word] if word in dictionary else index.get(normalized(word), [])
        candidates = []
        for key in keys:
            match = ("exata" if key == word else
                     "caixa/Unicode" if unicodedata.normalize("NFC", key.casefold()) ==
                     unicodedata.normalize("NFC", word.casefold()) else
                     "normalizada")
            candidates.append({"chave_json": key, "correspondencia": match,
                               **{field: dictionary[key].get(field) for field in fields}})
        result.append({"forma_tm": word, "candidatos": candidates,
                       "estado": "consultar" if candidates else "sem registro"})
    return result


def check_sources(chapter, morphology):
    numbers = []
    for pericope in chapter["pericopes"]:
        actual = [verse["verse"] for verse in pericope["verses"]]
        if actual != list(range(pericope["start_verse"], pericope["end_verse"] + 1)):
            raise ValueError("Sequência inválida na perícope do TM.")
        for verse in pericope["verses"]:
            number = verse["verse"]
            greek = [normalized(token["lemma"]) for token in verse["tokens"]]
            parsed = [normalized(word) for word in re.findall(
                r"(\S+) \d+ \{[^}]+\}", morphology.get(number, ""))]
            if greek != parsed:
                raise ValueError(f"TM e CSV divergem no versículo {number}; revisão manual.")
        numbers.extend(actual)
    if not numbers or numbers != list(range(1, numbers[-1] + 1)):
        raise ValueError("Numeração incompleta ou duplicada na fonte.")
    if set(morphology) != set(numbers):
        raise ValueError("CSV e JSON não contêm os mesmos versículos.")


def mechanical_draft(chapter, dictionary, index):
    """Alinha glosas sem escolher uma acepção contextual."""
    lexicon = {item["forma_tm"]: item
               for item in lexical_packet(chapter, dictionary, index)}
    blocks = []
    for pericope in chapter["pericopes"]:
        lines = [pericope["title"]]
        for verse in pericope["verses"]:
            glosses = []
            for token in verse["tokens"]:
                word = token["lemma"]
                item = lexicon[word]
                candidates = item["candidatos"]
                candidate_glosses = []
                for candidate in candidates:
                    gloss = candidate.get("pt") or candidate.get("traducao")
                    if isinstance(gloss, str) and gloss.strip():
                        candidate_glosses.append(" ".join(gloss.split()))
                    else:
                        candidate_glosses.append(word)
                if not candidates:
                    gloss = word
                else:
                    gloss = " / ".join(candidate_glosses)
                glosses.append(gloss)
            lines.append(f'{verse["verse"]} ' + " ".join(glosses))
        blocks.append("\n".join(lines))
    text = "\n--\n".join(blocks) + "\n"

    spec = importlib.util.spec_from_file_location(
        "bereia_converter", ROOT / "tools/biblech/gera_capitulos_html.py")
    converter = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = converter
    spec.loader.exec_module(converter)
    converter.parse_source(text, default_chapter=chapter["chapter"])
    return text


def parser():
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--chapters", required=True, help="14-28, 14,16-18 ou all")
    command.add_argument("--source", type=Path, default=ROOT / "src/interlinear/nt/MC.json")
    command.add_argument("--morphology", type=Path,
                         default=ROOT / "tools/tmnt/with-parsing/MAR.csv")
    command.add_argument("--dictionary", type=Path,
                         help="Dicionário flexionado; detecta a localização atual ou a antiga")
    command.add_argument("--book-name", default="Marcos")
    command.add_argument("--output", type=Path,
                         default=ROOT / "reports/traducao/marcos")
    return command


def run(args):
    dictionary_path = args.dictionary
    if dictionary_path is None:
        candidates = [ROOT / "src/_data/nt/dict_flex_nt-lxx_greek-pt.json",
                      ROOT / "src/_data/dict_flex_nt-lxx_greek-pt.json"]
        dictionary_path = next((path for path in candidates if path.exists()), None)
        if dictionary_path is None:
            raise ValueError("Dicionário definitivo ausente; informe --dictionary.")
    dictionary_path = dictionary_path.resolve()
    print(f"Dicionário (somente leitura): {dictionary_path}", flush=True)
    dictionary_bytes = dictionary_path.read_bytes()
    dictionary = json.loads(dictionary_bytes)
    index = lexical_index(dictionary)
    chapters = json.loads(args.source.read_text(encoding="utf-8"))
    by_number = {chapter["chapter"]: chapter for chapter in chapters}
    selected = chapter_numbers(args.chapters, by_number)

    morphology = {}
    with args.morphology.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            chapter_number, verse_number = int(row["chapter"]), int(row["verse"])
            target = morphology.setdefault(chapter_number, {})
            if verse_number in target:
                raise ValueError("Versículo duplicado no CSV.")
            target[verse_number] = row["text"]

    output = args.output.resolve()
    for protected in (ROOT / "src", ROOT / "docs", ROOT / "tools", ROOT / ".git"):
        if output == protected or protected in output.parents:
            raise ValueError("Escolha uma pasta de rascunhos fora de src/docs/tools/.git.")
    output.mkdir(parents=True, exist_ok=True)

    for number in selected:
        chapter = by_number[number]
        chapter_morphology = morphology.get(number, {})
        check_sources(chapter, chapter_morphology)
        folder = output / str(number)
        print(f"{args.book_name} {number}: montando glosas locais…", flush=True)
        text = mechanical_draft(chapter, dictionary, index)
        folder.mkdir(parents=True, exist_ok=True)
        txt_path = folder / f"{number}.txt"
        with txt_path.open("x", encoding="utf-8", newline="\n") as file:
            file.write(text)
        print(f"{args.book_name} {number}: TXT salvo em {txt_path}.", flush=True)


def main():
    try:
        run(parser().parse_args())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
