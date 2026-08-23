#!/usr/bin/env python3
"""
Adiciona o prefixo "G<strongs>: " ao inicio do campo "verbete" de cada
entrada em nt-missing-lemmas.json, evitando duplicar o prefixo caso ele
ja exista. Cria um backup .bak antes de sobrescrever o arquivo original.

Uso:
    python3 add_strongs_prefix.py
"""

import json
import re
import shutil
from pathlib import Path

ARQUIVO = Path(__file__).parent / "nt-missing-lemmas.json"
BACKUP = ARQUIVO.with_suffix(".json.bak")

PREFIXO_REGEX = re.compile(r"^G\d+:\s*")


def main():
    if not ARQUIVO.exists():
        raise SystemExit(f"Arquivo nao encontrado: {ARQUIVO}")

    with ARQUIVO.open("r", encoding="utf-8") as f:
        dados = json.load(f)

    alterados = 0
    ja_tinha_prefixo = 0
    sem_strongs = 0

    for chave, entrada in dados.items():
        strongs = entrada.get("strongs")
        verbete = entrada.get("verbete", "")

        if not strongs:
            sem_strongs += 1
            continue

        # Remove prefixo G<numero>: existente antes de reaplicar,
        # evitando duplicacao se o script for executado mais de uma vez
        verbete_sem_prefixo = PREFIXO_REGEX.sub("", verbete, count=1)
        novo_verbete = f"G{strongs}: {verbete_sem_prefixo}"

        if novo_verbete != verbete:
            if PREFIXO_REGEX.match(verbete):
                ja_tinha_prefixo += 1
            entrada["verbete"] = novo_verbete
            alterados += 1

    shutil.copy2(ARQUIVO, BACKUP)

    with ARQUIVO.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Arquivo atualizado: {ARQUIVO}")
    print(f"Backup salvo em:    {BACKUP}")
    print(f"Total de entradas:  {len(dados)}")
    print(f"Alteradas:          {alterados}")
    print(f"Ja tinham prefixo (normalizadas): {ja_tinha_prefixo}")
    print(f"Sem campo 'strongs' (ignoradas):  {sem_strongs}")


if __name__ == "__main__":
    main()
