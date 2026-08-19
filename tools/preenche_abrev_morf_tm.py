#!/usr/bin/env python3
"""
Preenche a chave "abrev_morf" do arquivo destino (nt-missing-lemmas-FINAL.json)
com o dado morfológico (conteúdo entre colchetes, ex: N-NSM) encontrado nos
arquivos CSV de origem em tools/tm_with-parsing, cruzando pelo termo grego
normalizado (sem acentos/diacríticos, minúsculo, sigma final normalizado).

Apenas entradas com "abrev_morf" VAZIO (ausente, None ou string vazia) são
preenchidas. Entradas já preenchidas são preservadas sem alteração.

Formato de origem (coluna 'text' dos CSVs), tokens separados por espaço:
    παυλος 3972 {N-NSM} κλητος 2822 {A-NSM} ...

Uso:
    python3 preenche_abrev_morf_tm.py
"""

import json
import re
import csv
import unicodedata
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "tm_with-parsing"
DST_FILE = BASE_DIR / "nt-missing-lemmas-FINAL.json"
OUT_FILE = BASE_DIR / "nt-missing-lemmas-FINAL.json"
BACKUP_FILE = BASE_DIR / "nt-missing-lemmas-FINAL.backup.json"

TOKEN_RE = re.compile(r"(\S+)\s+(\d+)\s+\{([^}]+)\}")


def normalize_greek(word: str) -> str:
    if not word:
        return ""
    decomposed = unicodedata.normalize("NFD", word)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    normalized = unicodedata.normalize("NFC", stripped).lower()
    normalized = normalized.replace("ς", "σ")
    return normalized


def is_empty(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def build_source_index():
    index = defaultdict(Counter)
    csv_files = sorted(SRC_DIR.glob("*.csv"))
    total_tokens = 0

    for csv_path in csv_files:
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get("text", "")
                if not text:
                    continue
                for match in TOKEN_RE.finditer(text):
                    greek_word, strongs, morph = match.groups()
                    norm = normalize_greek(greek_word)
                    if norm:
                        index[norm][morph] += 1
                        total_tokens += 1

    return index, len(csv_files), total_tokens


def main():
    print(f"Lendo arquivos de origem em: {SRC_DIR}")
    index, n_files, total_tokens = build_source_index()
    print(f"  -> {n_files} arquivos CSV processados, {total_tokens} tokens indexados, "
          f"{len(index)} formas gregas únicas (normalizadas).")

    print(f"Lendo destino: {DST_FILE}")
    with DST_FILE.open(encoding="utf-8") as f:
        dest = json.load(f)

    with BACKUP_FILE.open("w", encoding="utf-8") as f:
        json.dump(dest, f, ensure_ascii=False, indent=2)
    print(f"Backup salvo em: {BACKUP_FILE}")

    updated = 0
    already_filled = 0
    not_found = []
    ambiguous = []
    UPDATABLE_PLACEHOLDER = "Substantivo/Adjetivo"

    for key, entry in dest.items():
        current = entry.get("abrev_morf")
        if not is_empty(current) and current != UPDATABLE_PLACEHOLDER:
            already_filled += 1
            continue

        grego = entry.get("grego", key)
        norm = normalize_greek(grego)
        matches = index.get(norm)
        if not matches:
            not_found.append(grego)
            continue

        most_common = matches.most_common()
        best_morph, best_count = most_common[0]
        if len(most_common) > 1 and most_common[1][1] == best_count:
            ambiguous.append((grego, most_common))

        entry["abrev_morf"] = best_morph
        updated += 1

    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(dest, f, ensure_ascii=False, indent=2)

    print("\n=== Relatório ===")
    print(f"Total de entradas no destino: {len(dest)}")
    print(f"Entradas já preenchidas (preservadas, não alteradas): {already_filled}")
    print(f"Entradas vazias atualizadas agora (abrev_morf preenchido): {updated}")
    print(f"Entradas vazias sem correspondência encontrada: {len(not_found)}")
    if not_found:
        preview = ", ".join(not_found[:20])
        print(f"  Exemplos sem correspondência: {preview}"
              f"{' ...' if len(not_found) > 20 else ''}")
    print(f"Entradas com morfologia ambígua (empate de frequência): {len(ambiguous)}")
    if ambiguous:
        for grego, opts in ambiguous[:10]:
            print(f"  {grego}: {opts}")

    print(f"\nArquivo atualizado salvo em: {OUT_FILE}")


if __name__ == "__main__":
    main()
