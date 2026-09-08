#!/usr/bin/env python3
import csv
import json
import re
import unicodedata
from pathlib import Path

PARTICIPIOS_IRREGULARES = {
    "dado": "dados",
    "feito": "feitos",
    "posto": "postos",
    "tornado": "tornados",
    "visto": "vistos",
    "aberto": "abertos",
    "escrito": "escritos",
    "dito": "ditos",
    "morto": "mortos",
    "vindo": "vindos",
    "tido": "tidos",
    "sido": None,
}

AUX_PLURAL = re.compile(r"\b(?:foram|fomos|fostes|serao|seremos|sereis|sejam|sejamos|sejais|somos|sois|esto|estavam)\s+([a-zà·´ÿ]+)\b", re.I)
AUX_SINGULAR = re.compile(r"\b(?:foi|fui|foste|sera|serei|seras|seja|sou|s|e|est|estava)\s+([a-zà·´ÿ]+)\b", re.I)

def norm(value):
    return unicodedata.normalize("NFC", str(value or "")).strip()


def lower(value):
    return norm(value).lower()


def likely_singular_participle(word):
    word = lower(word)
    return bool(re.search(r"(?:ado|ido|to|so|cho)$", word)) and not bool(re.search(r"(?:ados|idos|tos|sos|chos)$", word))


def likely_plural_participle(word):
    word = lower(word)
    return bool(re.search(r"(?:ados|idos|tos|sos|chos)$", word))


def corrigir_concordancia(pt):
    """Aplica correcoes seguras de concordancia de participio."""
    altered = False
    result = pt

    for match in AUX_PLURAL.finditer(result):
        participle = match.group(1)
        if likely_singular_participle(participle):
            if participle in PARTICIPIOS_IRREGULARES:
                forma = PARTICIPIOS_IRREGULARES[participle]
                if forma is None:
                    continue
            else:
                forma = participle + "s"
            result = result[: match.start(1)] + forma + result[match.end(1):]
            altered = True

    for match in AUX_SINGULAR.finditer(result):
        participle = match.group(1)
        if likely_plural_participle(participle):
            if participle in PARTICIPIOS_IRREGULARES:
                forma = PARTICIPIOS_IRREGULARES[participle]
                if forma is None:
                    continue
                forma = forma.rstrip("s")
            else:
                forma = participle.rstrip("s")
            result = result[: match.start(1)] + forma + result[match.end(1):]
            altered = True

    return result, altered


def main():
    input_path = Path("src/_data/dict_flex_nt-lxx_greek-pt.json")
    audit_csv = Path("auditoria_dict_flex_v5.csv")
    output_json = Path("dict_flex_nt-lxx_greek-pt_corrigido.json")
    output_csv = Path("correcoes_aplicadas.csv")

    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    correcoes = []

    with audit_csv.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["tipo"] not in {"concordancia_participio", "concordancia_nominal"}:
                continue
            if row["prioridade"] != "alta":
                continue

            forma = norm(row["forma_grega"])
            if forma not in data:
                continue

            pt_antigo = data[forma].get("pt", "")
            pt_novo, altered = corrigir_concordancia(pt_antigo)

            if altered and pt_novo != pt_antigo:
                correcoes.append({
                    "forma_grega": forma,
                    "strongs": norm(data[forma].get("strongs")),
                    "pt_antigo": pt_antigo,
                    "pt_novo": pt_novo,
                    "motivo": row["tipo"],
                })
                data[forma]["pt"] = pt_novo

    with output_json.open("w", encoding="utf-8-sig") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["forma_grega", "strongs", "pt_antigo", "pt_novo", "motivo"])
        writer.writeheader()
        writer.writerows(correcoes)

    print(f"{len(correcoes)} correcao(oes) aplicadas.")
    print(f"JSON corrigido: {output_json}")
    print(f"Relatorio de correcoes: {output_csv}")


if __name__ == "__main__":
    main()