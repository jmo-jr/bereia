#!/usr/bin/env python3
"""Remove conteúdo entre parênteses do campo `pt` em nt_greek-pt_dict.json

Usage:
    python3 tools/clean_pt_parentheses.py --file src/_data/nt_greek-pt_dict.json --start-line 15237

Opções:
    --dry-run    : mostra amostra de mudanças, não grava o arquivo
    --start-line : linha do arquivo (1-index) a partir da qual aplicar mudanças
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List

PAREN_RE = re.compile(r"\([^)]*\)")
HYPHEN_EDGE_RE = re.compile(r"^[\s\-–]+|[\s\-–]+$")
MULTI_SPACE_RE = re.compile(r"\s+")


def clean_pt_value(s: str) -> str:
    if not isinstance(s, str):
        return s
    # remove all parenthetical fragments
    new = PAREN_RE.sub("", s)
    # remove edge hyphens or dashes left from patterns like (a-)word
    new = HYPHEN_EDGE_RE.sub("", new)
    # collapse spaces and trim
    new = MULTI_SPACE_RE.sub(" ", new).strip()
    return new


def map_key_start_lines(text: str) -> Dict[str, int]:
    mapping = {}
    key_re = re.compile(r'^\s*"(?P<key>[^"]+)"\s*:\s*\{')
    for i, line in enumerate(text.splitlines(), start=1):
        m = key_re.match(line)
        if m:
            mapping[m.group('key')] = i
    return mapping


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="caminho do JSON a editar")
    parser.add_argument("--start-line", type=int, default=1, help="linha (1-index) a partir da qual aplicar mudanças")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    p = Path(args.file)
    if not p.exists():
        raise SystemExit(f"Arquivo não encontrado: {p}")

    text = p.read_text(encoding="utf-8")
    key_lines = map_key_start_lines(text)

    data = json.loads(text)

    keys_in_order = list(data.keys())

    to_modify_keys: List[str] = [k for k in keys_in_order if key_lines.get(k, 0) >= args.start_line]

    if not to_modify_keys:
        print("Nenhuma chave encontrada a partir da linha", args.start_line)
        return

    backup = p.with_suffix(p.suffix + ".bak")
    if not args.dry_run:
        shutil.copy2(p, backup)
        print(f"Backup criado: {backup}")

    changed = 0
    samples = []

    for k in to_modify_keys:
        entry = data.get(k)
        if not isinstance(entry, dict):
            continue
        pt = entry.get("pt")
        if not isinstance(pt, str):
            continue
        cleaned = clean_pt_value(pt)
        if cleaned != pt:
            entry["pt"] = cleaned
            changed += 1
            if len(samples) < 40:
                samples.append((k, pt, cleaned))

    if changed == 0:
        print("Nenhuma alteração necessária.")
        return

    print(f"Entradas modificadas: {changed}")
    print("Amostra de mudanças (até 40):")
    for k, old, new in samples:
        print(f"- {k}: '{old}' -> '{new}'")

    if not args.dry_run:
        # write JSON using tabs as project prefers
        p.write_text(json.dumps(data, ensure_ascii=False, indent='\t') + "\n", encoding="utf-8")
        print(f"Arquivo gravado: {p}")
        print(f"Diferença sugerida: `git diff -- {p}`")


if __name__ == '__main__':
    main()
