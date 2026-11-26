#!/usr/bin/env python3
"""Create a copy of the Greek dictionary containing forms found in the TM NT."""

import argparse
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DICTIONARY = ROOT / "src/_data/dict_flex_nt-lxx_greek-pt.json"
DEFAULT_NT_DIR = ROOT / "src/interlinear/nt"
DEFAULT_OUTPUT = ROOT / "tools/files/dict_tm.json"
HOMOGRAPHS_KEY = "_homografos_normalizados"
MISSING_FORMS_KEY = "_formas_tm_sem_entrada"


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Não foi possível ler JSON válido em {path}: {exc}") from exc


def collect_tm_forms(nt_dir: Path) -> set[str]:
    files = sorted(nt_dir.glob("*.json"))
    if not files:
        raise ValueError(f"Nenhum arquivo JSON encontrado em {nt_dir}")

    forms: set[str] = set()

    def visit(value, source: Path) -> None:
        if isinstance(value, dict):
            tokens = value.get("tokens")
            if isinstance(tokens, list):
                for index, token in enumerate(tokens):
                    if not isinstance(token, dict) or not isinstance(token.get("lemma"), str):
                        raise ValueError(
                            f"Token inválido em {source}: tokens[{index}] precisa ter lemma textual"
                        )
                    forms.add(token["lemma"])
            for child in value.values():
                visit(child, source)
        elif isinstance(value, list):
            for child in value:
                visit(child, source)

    for path in files:
        visit(load_json(path), path)
    return forms


def normalize_greek_form(form: str) -> str:
    """Remove diacritics and case distinctions, keeping iota subscript as iota."""
    normalized = []
    for char in unicodedata.normalize("NFD", form):
        if char == "\u0345":  # Greek ypogegrammeni represents an iota.
            normalized.append("ι")
        elif unicodedata.combining(char):
            continue
        else:
            normalized.append(char.casefold())
    return "".join(normalized)


def find_normalized_homographs(forms) -> list[str]:
    forms_by_normalized = defaultdict(set)
    for form in forms:
        forms_by_normalized[normalize_greek_form(form)].add(form)
    return sorted(
        normalized
        for normalized, spellings in forms_by_normalized.items()
        if len(spellings) > 1
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Filtra uma cópia do dicionário pelas formas presentes nos JSONs do TM NT."
    )
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY,
                        help=f"Dicionário de entrada (padrão: {DEFAULT_DICTIONARY})")
    parser.add_argument("--nt-dir", type=Path, default=DEFAULT_NT_DIR,
                        help=f"Diretório dos JSONs do TM (padrão: {DEFAULT_NT_DIR})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Cópia filtrada (padrão: {DEFAULT_OUTPUT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra as contagens sem gravar a cópia filtrada")
    args = parser.parse_args()

    try:
        dictionary = load_json(args.dictionary)
        if not isinstance(dictionary, dict):
            raise ValueError("O dicionário precisa ser um objeto JSON indexado pelas formas gregas.")
        if not all(isinstance(form, str) for form in dictionary):
            raise ValueError("Todas as chaves do dicionário precisam ser formas textuais.")

        tm_forms = collect_tm_forms(args.nt_dir)
        filtered = {form: entry for form, entry in dictionary.items() if form in tm_forms}
        absent_count = len(dictionary) - len(filtered)
        tm_missing_from_dictionary = len(tm_forms - dictionary.keys())
        missing_forms = sorted(tm_forms - dictionary.keys())
        homographs = find_normalized_homographs(filtered)
        reserved_keys = {HOMOGRAPHS_KEY, MISSING_FORMS_KEY}
        if reserved_keys.intersection(filtered):
            raise ValueError("Uma chave reservada para metadados já existe no dicionário.")

        print(f"Formas distintas no TM NT: {len(tm_forms)}")
        print(f"Entradas no dicionário:    {len(dictionary)}")
        print(f"Entradas mantidas:         {len(filtered)}")
        print(f"Entradas fora do TM:       {absent_count}")
        print(f"Formas do TM sem entrada:  {tm_missing_from_dictionary}")
        print(f"Grupos homógrafos:         {len(homographs)}")
        print(f"Formas ausentes listadas:  {len(missing_forms)}")

        if args.dry_run:
            print("Prévia: nenhum arquivo foi gravado.")
            return 0

        if args.output.resolve() == args.dictionary.resolve():
            raise ValueError("A saída não pode sobrescrever o dicionário de entrada.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output_data = dict(filtered)
        output_data[HOMOGRAPHS_KEY] = homographs
        output_data[MISSING_FORMS_KEY] = missing_forms
        with args.output.open("w", encoding="utf-8") as file:
            json.dump(output_data, file, ensure_ascii=False, indent=2)
            file.write("\n")

        # Reabre e valida o JSON gravado e a contagem de entradas.
        saved = load_json(args.output)
        if (not isinstance(saved, dict)
                or list(saved) != [*filtered, HOMOGRAPHS_KEY, MISSING_FORMS_KEY]
                or saved[HOMOGRAPHS_KEY] != homographs
                or saved[MISSING_FORMS_KEY] != missing_forms):
            raise ValueError(f"A cópia gravada não passou na validação: {args.output}")
        print(f"Cópia gravada e validada: {args.output}")
        return 0
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
