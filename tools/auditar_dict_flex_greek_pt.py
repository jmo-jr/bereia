#!/usr/bin/env python3
import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

FEMININOS_PLURAL = {
    "reprovaes", "embarcaes", "crianas", "mulheres",
    "aes", "aflioes", "almas", "ameaas", "rvores", "benos", "cidades",
    "coisas", "escrituras", "figueiras", "naes", "obras", "oraes", "palavras",
    "pessoas", "vidas",
}
MASCULINOS_PLURAL = {
    "cordes", "escorpies",
    "caminhos", "coraes", "filhos", "homens", "olhos",
    "pes", "pecados", "povos", "ramos", "sbados", "tempos", "vasos",
}

# Auxiliares de passiva em português.
AUX_PASSIVO = re.compile(
    r"\b(?:ser|sendo|sido|seja|sejam|sejais|sejamos|"
    r"foi|foram|fui|fomos|foste|fostes|"
    r"era|eram|sou|s|es|somos|sois|sede|so|"
    r"serei|seras|sera|seremos|sereis|serao|sera|seras|seremos|sereis|serao|"
    r"fosse|fossem|fssemos|fsseis|"
    r"tenha sido|tendo sido|havia sido|haviam sido|"
    r"estou|ests|est|estamos|estais|esto|estava|estavam)\b",
    re.I,
)
REFLEXIVO = re.compile(r"\b(?:me|te|se|nos|vos)\b|\w+-(?:me|te|se|nos|vos)\b", re.I)
INFINITIVO_ATIVO = re.compile(r"^[a-zà·´ÿ]+(?:ar|er|ir)$", re.I)

# Padrô·µ·μes para concordancia de particpio.
AUX_PLURAL = re.compile(r"\b(?:foram|fomos|fostes|serao|seremos|sereis|sejam|sejamos|sejais|somos|sois|esto|estavam)\s+([a-zà·´ÿ]+)\b", re.I)
AUX_SINGULAR = re.compile(r"\b(?:foi|fui|foste|sera|serei|seras|seja|sou|s|e|est|estava)\s+([a-zà·´ÿ]+)\b", re.I)

# Formas irregulares de particpio para evitar pluralizaes absurdas.
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
    "posto": "postos",
    "vindo": "vindos",
    "tido": "tidos",
    "sido": None,
}


def norm(value):
    return unicodedata.normalize("NFC", str(value or "")).strip()


def lower(value):
    return norm(value).lower()


def verb_info(code):
    parts = norm(code).split("-")
    if not parts or parts[0] != "V":
        return None
    main = parts[1] if len(parts) > 1 else ""
    voice = main[2:] if len(main) >= 3 else ""
    return {"main": main, "voice": voice, "raw": norm(code)}


def person_number(code):
    m = re.search(r"-(\d)([SP])$", norm(code))
    return (m.group(1), m.group(2)) if m else (None, None)


def passive_translation(text):
    return bool(AUX_PASSIVO.search(text) or REFLEXIVO.search(text))


def expected_plural(code):
    _, number = person_number(code)
    return number == "P"


def likely_singular_participle(word):
    word = lower(word)
    return bool(re.search(r"(?:ado|ido|to|so|cho)$", word)) and not bool(re.search(r"(?:ados|idos|tos|sos|chos)$", word))


def likely_plural_participle(word):
    word = lower(word)
    return bool(re.search(r"(?:ados|idos|tos|sos|chos)$", word))


def add(findings, kind, priority, finding, suggestion):
    findings.append({"tipo": kind, "prioridade": priority, "achado": finding, "sugestao": suggestion})


def audit_contractions(pt, findings):
    words = re.findall(r"[a-zà·´ÿ]+", lower(pt))
    for i, word in enumerate(words[:-1]):
        next_word = words[i + 1]
        if word == "aos" and next_word in FEMININOS_PLURAL:
            add(findings, "concordancia_nominal", "alta", f"Contraao masculina antes de feminino plural: '{pt}'.", f"Trocar 'aos {next_word}' por 'as {next_word}'.")
        elif word == "as" and next_word in MASCULINOS_PLURAL:
            add(findings, "concordancia_nominal", "alta", f"Contraao feminina antes de masculino plural: '{pt}'.", f"Trocar 'as {next_word}' por 'aos {next_word}'.")


def audit_passive(code, pt, findings):
    info = verb_info(code)
    if not info:
        return
    voice = info["voice"]
    explicit_passive = voice == "P"
    ambiguous = voice == "M/P"
    normalized_pt = lower(pt)

    if explicit_passive and INFINITIVO_ATIVO.fullmatch(normalized_pt):
        add(
            findings,
            "passiva_sem_marca",
            "alta",
            f"'{code}' e passiva, mas 'pt' esta em infinitivo ativo: '{pt}'.",
            "Revisar para uma forma passiva adequada, por exemplo 'ser + particpio', quando o contexto nao exigir outra soluao.",
        )
    elif ambiguous and INFINITIVO_ATIVO.fullmatch(normalized_pt):
        add(
            findings,
            "media_passiva_ambigua",
            "revisar",
            f"'{code}' e media ou passiva e 'pt' e infinitivo ativo: '{pt}'.",
            "Decidir pelo contexto entre leitura media/reflexiva, passiva ou ativa idiomatica; nao corrigir automaticamente.",
        )
    elif explicit_passive and not passive_translation(pt) and not INFINITIVO_ATIVO.fullmatch(normalized_pt):
        add(
            findings,
            "passiva_a_confirmar",
            "revisar",
            f"'{code}' e passiva, porem a passiva nao esta explicita em '{pt}'.",
            "Confirmar se a glossa pretende particpio isolado, adjetivo verbal ou construao passiva completa.",
        )


def audit_participle_agreement(pt, findings):
    for match in AUX_PLURAL.finditer(lower(pt)):
        participle = match.group(1)
        if likely_singular_participle(participle):
            suggestion = f"Revisar o numero do particpio; provavel forma plural: '{participle}s'."
            if participle in PARTICIPIOS_IRREGULARES:
                if PARTICIPIOS_IRREGULARES[participle] is None:
                    suggestion = "Reescrever a construao; 'sido' nao deve ser pluralizado. Usar forma idiomatica (ex.: 'puderam', 'foram capazes')."
                else:
                    suggestion = f"Revisar o numero do particpio; forma plural provavel: '{PARTICIPIOS_IRREGULARES[participle]}'."
            add(
                findings,
                "concordancia_participio",
                "alta",
                f"Auxiliar plural com particpio aparentemente singular: '{match.group(0)}'.",
                suggestion,
            )
    for match in AUX_SINGULAR.finditer(lower(pt)):
        participle = match.group(1)
        if likely_plural_participle(participle):
            add(
                findings,
                "concordancia_participio",
                "alta",
                f"Auxiliar singular com particpio aparentemente plural: '{match.group(0)}'.",
                "Revisar o numero do particpio conforme o referente real.",
            )


BAD_CONSTRUCTIONS = [
    (re.compile(r"\b(?:foram|fomos|seremos|sereis)\s+sido\b", re.I), "Construao inadequada com 'sido'.", "Reescrever idiomaticamente; por exemplo, 'foram capazes', 'puderam' ou 'seremos capazes', conforme o sentido."),
    (re.compile(r"\b(?:foram|fomos)\s+ficado\b", re.I), "Construao inadequada com 'ficado'.", "Reescrever; por exemplo, 'ficaram' ou 'tornaram-se'."),
    (re.compile(r"\b(?:foram|fomos|serao|seremos|sejam|sejamos|fostes|sejais)\s+tornado\b", re.I), "Particpio de 'tornar' sem concordancia ou construao adequada.", "Usar 'tornados/tornadas' quando for passiva real, ou reescrever como 'tornaram-se'/'passaram a ser'."),
    (re.compile(r"\bfomos\s+tido\b", re.I), "Construao inadequada com 'tido'.", "Reescrever conforme o sentido: 'tivemos', 'recebemos' ou 'fomos considerados'."),
    (re.compile(r"\bficaram\s+muito\s+surpreso\b", re.I), "Concordancia nominal possivelmente incorreta.", "Usar 'ficaram muito surpresos' quando o referente for plural."),
]


def audit_bad_constructions(pt, findings):
    for pattern, finding, suggestion in BAD_CONSTRUCTIONS:
        if pattern.search(pt):
            add(findings, "construcao_inadequada", "alta", finding, suggestion)


def audit_entry(entry):
    pt = norm(entry.get("pt"))
    code = norm(entry.get("abrev_morf"))
    findings = []
    if not pt:
        add(findings, "pt_vazio", "alta", "Campo 'pt' esta vazio.", "Informe uma glossa portuguesa.")
        return findings
    audit_contractions(pt, findings)
    audit_passive(code, pt, findings)
    audit_participle_agreement(pt, findings)
    audit_bad_constructions(pt, findings)
    return findings


def main():
    parser = argparse.ArgumentParser(description="Auditoria v5 de glossas PT por morfologia grega.")
    parser.add_argument("input", type=Path, help="Caminho do arquivo JSON")
    parser.add_argument("--output", type=Path, default=Path("auditoria_dict_flex_v5.csv"), help="CSV de sada")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit("Esperado um objeto JSON indexado pela forma grega.")

    fields = ["forma_grega", "strongs", "abrev_morf", "morfologia", "pt", "traducao", "tipo", "prioridade", "achado", "sugestao"]
    count = 0
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for form, entry in data.items():
            if not isinstance(entry, dict):
                continue
            for finding in audit_entry(entry):
                count += 1
                writer.writerow({
                    "forma_grega": norm(form),
                    "strongs": norm(entry.get("strongs")),
                    "abrev_morf": norm(entry.get("abrev_morf")),
                    "morfologia": norm(entry.get("morfologia")),
                    "pt": norm(entry.get("pt")),
                    "traducao": norm(entry.get("traducao")),
                    **finding,
                })
    print(f"{count} apontamento(s) gravado(s) em {args.output}")


if __name__ == "__main__":
    main()