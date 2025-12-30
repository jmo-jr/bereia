#!/usr/bin/env python3
"""Limpeza adicional dos valores `pt`:
- remove parênteses remanescentes
- remove parênteses soltos '(' e ')'
- remove hifens nas bordas e hífens isolados entre espaços
- colapsa espaços múltiplos

Uso:
    python3 tools/clean_pt_residuals.py --file src/_data/nt_greek-pt_dict.json --start-line 15237
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List

PAREN_RE = re.compile(r"\([^)]*\)")
LEFTOVER_PAREN_RE = re.compile(r"[()]")
HYPHEN_BORDER_RE = re.compile(r"(^|\s)[-–—]+|[-–—]+(\s|$)")
HYPHEN_ISOLATED_RE = re.compile(r"\s+[-–—]+\s+")
MULTI_SPACE_RE = re.compile(r"\s+")


def refine_pt(s: str) -> str:
    if not isinstance(s, str):
        return s
    new = s
    # remove parenthetical fragments and any leftover parentheses
    new = PAREN_RE.sub("", new)
    new = LEFTOVER_PAREN_RE.sub("", new)
    # remove hyphens that are isolated (surrounded by spaces)
    new = HYPHEN_ISOLATED_RE.sub(" ", new)
    # remove hyphens at word boundaries (leading/trailing adjacent to spaces)
    new = HYPHEN_BORDER_RE.sub(lambda m: (m.group(1) or "") if m.group(1) or m.group(2) else "", new)
    # remove stray sequences like "-" adjacent to punctuation or start/end
    new = re.sub(r"(^|\s)[-–—]+(?=\w)", r"\1", new)
    new = re.sub(r"(?<=\w)[-–—]+(\s|$)", r"\1", new)
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
    parser.add_argument("--file", required=True)
    parser.add_argument("--start-line", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    p = Path(args.file)
    if not p.exists():
        raise SystemExit(f"Arquivo não encontrado: {p}")

    text = p.read_text(encoding="utf-8")
    key_lines = map_key_start_lines(text)

    data = json.loads(text)
    keys_in_order = list(data.keys())
    to_modify = [k for k in keys_in_order if key_lines.get(k, 0) >= args.start_line]

    if not to_modify:
        print("Nenhuma chave a partir da linha", args.start_line)
        return

    backup = p.with_suffix(p.suffix + ".residuals.bak")
    if not args.dry_run:
        shutil.copy2(p, backup)
        print(f"Backup criado: {backup}")

    changed = 0
    samples = []

    for k in to_modify:
        entry = data.get(k)
        if not isinstance(entry, dict):
            continue
        pt = entry.get("pt")
        if not isinstance(pt, str):
            continue
        cleaned = refine_pt(pt)
        if cleaned != pt:
            entry["pt"] = cleaned
            changed += 1
            if len(samples) < 80:
                samples.append((k, pt, cleaned))

    if changed == 0:
        print("Nenhuma alteração necessária na etapa de refinamento.")
        return

    print(f"Entradas modificadas no refinamento: {changed}")
    print("Amostra de mudanças (até 80):")
    for k, old, new in samples:
        print(f"- {k}: '{old}' -> '{new}'")

    if not args.dry_run:
        p.write_text(json.dumps(data, ensure_ascii=False, indent='\t') + "\n", encoding="utf-8")
        print(f"Arquivo gravado: {p}")
        print(f"Sugestão para revisar diff: git diff -- {p}")


if __name__ == '__main__':
    main()
