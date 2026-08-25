#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
MORPHGNT_DIR = ROOT / "tools" / "morphgnt"

DEFAULT_INPUT = ROOT / "tools" / "nt_greek-pt_dict.json"
DEFAULT_OUTPUT = ROOT / "tools" / "nt_greek-pt_dict2.json"

BOOK_MAP = {
    "MAT": "Mt",
    "MR": "Mc",
    "LUK": "Lc",
    "JOH": "Jo",
    "AC": "At",
    "ROM": "Rm",
    "1CO": "1Co",
    "2CO": "2Co",
    "GA": "Gl",
    "EPH": "Ef",
    "PHP": "Fp",
    "COL": "Cl",
    "1TH": "1Ts",
    "2TH": "2Ts",
    "1TI": "1Tm",
    "2TI": "2Tm",
    "TIT": "Tt",
    "PHM": "Fm",
    "HEB": "Hb",
    "JAS": "Tg",
    "1PE": "1Pe",
    "2PE": "2Pe",
    "1JO": "1Jo",
    "2JO": "2Jo",
    "3JO": "3Jo",
    "JUD": "Jd",
    "RE": "Ap",
}

WORD_REF_RE = re.compile(r"^(\d+):(\d+)\.(\d+)$")


def normalize_strongs(value):
    if value is None:
        return ""
    s = str(value).strip()
    s = s.upper().replace("G", "")
    return s


def format_ref(book_code, cvw):
    m = WORD_REF_RE.match(cvw)
    if not m:
        return None
    chapter, verse, _word = m.groups()
    book = BOOK_MAP.get(book_code, book_code)
    return f"{book} {chapter}:{verse}"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_nt_index():
    refs_by_form = defaultdict(list)

    for txt_file in sorted(MORPHGNT_DIR.glob("*.txt")):
        with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 7:
                    continue

                book_code = parts[0]
                ref_token = parts[1]
                form = parts[3]

                ref = format_ref(book_code, ref_token)
                if not ref:
                    continue

                if not refs_by_form[form] or refs_by_form[form][-1] != ref:
                    refs_by_form[form].append(ref)

    return refs_by_form


def enrich_dictionary(data, refs_by_form, nt_key="nt"):
    updated = 0
    zeroed = 0

    for term, entry in data.items():
        refs = refs_by_form.get(term, [])
        entry["ocorrencias"] = len(refs)
        entry[nt_key] = refs

        if refs:
            updated += 1
        else:
            zeroed += 1

    return updated, zeroed


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    if not input_path.exists():
        print(f"Arquivo de entrada não encontrado: {input_path}")
        sys.exit(1)

    if not MORPHGNT_DIR.exists():
        print(f"Pasta morphgnt não encontrada: {MORPHGNT_DIR}")
        sys.exit(1)

    data = load_json(input_path)
    if not isinstance(data, dict):
        print("O JSON de entrada precisa ser um objeto/dicionário na raiz.")
        sys.exit(1)

    refs_by_form = build_nt_index()
    updated, zeroed = enrich_dictionary(data, refs_by_form, nt_key="nt")
    save_json(output_path, data)

    print(f"Entrada : {input_path}")
    print(f"Saída   : {output_path}")
    print(f"Termos com ocorrências no NT : {updated}")
    print(f"Termos zerados / ausentes    : {zeroed}")
    print(f"Total de formas indexadas    : {len(refs_by_form)}")


if __name__ == "__main__":
    main()
