#!/usr/bin/env python3
"""Auditoria v6 de glossas portuguesas por morfologia grega.

Baseada na v5: mantém os alertas existentes e remove de
passiva_a_confirmar as passivas explícitas no padrão "ser + particípio".
"""

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

FEMININOS_PLURAL = {
    "reprovaes", "embarcaes", "crianas", "mulheres", "aes", "aflioes",
    "almas", "ameaas", "rvores", "benos", "cidades", "coisas",
    "escrituras", "figueiras", "naes", "obras", "oraes", "palavras",
    "pessoas", "vidas",
}
MASCULINOS_PLURAL = {
    "cordes", "escorpies", "caminhos", "coraes", "filhos", "homens",
    "olhos", "pes", "pecados", "povos", "ramos", "sbados", "tempos",
    "vasos",
}

AUX_PASSIVO = re.compile(
    r"\b(?:ser|sendo|sido|seja|sejam|sejais|sejamos|foi|foram|fui|fomos|"
    r"foste|fostes|era|eram|sou|és|é|somos|sois|são|serei|serás|será|"
    r"seremos|sereis|serão|fosse|fossem|tenha sido|tendo sido|havia sido|"
    r"haviam sido|estou|estás|está|estamos|estais|estão|estava|estavam)\b",
    re.I,
)
REFLEXIVO = re.compile(r"\b(?:me|te|se|nos|vos)\b|\w+-(?:me|te|se|nos|vos)\b", re.I)
INFINITIVO_ATIVO = re.compile(r"^[a-zà-ÿ]+(?:ar|er|ir)$", re.I)

AUX_PLURAL = re.compile(
    r"\b(?:foram|fomos|fostes|serão|seremos|sereis|sejam|sejamos|sejais|"
    r"somos|sois|estão|estavam)\s+([a-zà-ÿ]+)\b", re.I,
)
AUX_SINGULAR = re.compile(
    r"\b(?:foi|fui|foste|será|serei|serás|seja|sou|é|está|estava)\s+([a-zà-ÿ]+)\b",
    re.I,
)

PARTICIPIOS_IRREGULARES = {
    "dado": "dados", "feito": "feitos", "posto": "postos",
    "tornado": "tornados", "visto": "vistos", "aberto": "abertos",
    "escrito": "escritos", "dito": "ditos", "morto": "mortos",
    "vindo": "vindos", "tido": "tidos", "sido": None,
}

# Formas finitas de SER. "ser + particípio" é reconhecido separadamente.
FORMAS_SER = {
    "sou", "és", "é", "somos", "sois", "são", "era", "eras", "era", "éramos",
    "éreis", "eram", "fui", "foste", "foi", "fomos", "fostes", "foram",
    "serei", "serás", "será", "seremos", "sereis", "serão", "seria", "serias",
    "seríamos", "seríeis", "seriam", "seja", "sejas", "seja", "sejamos", "sejais",
    "sejam", "fosse", "fosses", "fôssemos", "fôsseis", "fossem", "sendo", "sido",
}
CLITICOS = {"me", "te", "se", "nos", "vos", "lhe", "lhes", "o", "a", "os", "as"}

BAD_CONSTRUCTIONS = [
    (re.compile(r"\b(?:foram|fomos|seremos|sereis)\s+sido\b", re.I),
     "Construção inadequada com 'sido'.",
     "Reescrever conforme o sentido: 'foram capazes', 'puderam' ou equivalente."),
    (re.compile(r"\b(?:foram|fomos)\s+ficado\b", re.I),
     "Construção inadequada com 'ficado'.",
     "Reescrever; por exemplo, 'ficaram' ou 'tornaram-se'."),
    (re.compile(r"\bficaram\s+muito\s+surpreso\b", re.I),
     "Concordância nominal possivelmente incorreta.",
     "Usar 'ficaram muito surpresos' quando o referente for plural."),
]


def norm(value):
    return unicodedata.normalize("NFC", str(value or "")).strip()


def lower(value):
    return norm(value).lower()


def verb_info(code):
    parts = norm(code).split("-")
    if not parts or parts[0] != "V":
        return None
    main = parts[1] if len(parts) > 1 else ""
    return {"main": main, "voice": main[2:] if len(main) >= 3 else "", "raw": norm(code)}


def person_number(code):
    match = re.search(r"-(\d)([SP])$", norm(code))
    return (match.group(1), match.group(2)) if match else (None, None)


def passive_translation(text):
    return bool(AUX_PASSIVO.search(text) or REFLEXIVO.search(text))


def is_participle(token):
    token = lower(token)
    if token in PARTICIPIOS_IRREGULARES or token in {"aceito", "eleito", "expresso", "impresso", "incluso", "anexo", "suspenso", "extinto", "pago", "ganho", "gasto", "coberto", "descoberto", "oferecido", "surgido", "havido", "estado"}:
        return True
    return bool(re.search(r"(?:ado|ido|to|so|cho|sto|eto|eto)$", token))


def explicit_ser_participle(text):
    tokens = re.findall(r"[A-Za-zÀ-ÿ]+", lower(text))
    for index, token in enumerate(tokens):
        if token not in FORMAS_SER:
            continue
        j = index + 1
        while j < len(tokens) and tokens[j] in CLITICOS:
            j += 1
        if j < len(tokens) and is_participle(tokens[j]):
            return True
    return False


def likely_singular_participle(word):
    word = lower(word)
    return bool(re.search(r"(?:ado|ido|to|so|cho)$", word)) and not bool(re.search(r"(?:ados|idos|tos|sos|chos)$", word))


def likely_plural_participle(word):
    return bool(re.search(r"(?:ados|idos|tos|sos|chos)$", lower(word)))


def add(findings, kind, priority, finding, suggestion):
    findings.append({"tipo": kind, "prioridade": priority, "achado": finding, "sugestao": suggestion})


def audit_contractions(pt, findings):
    words = re.findall(r"[a-zà-ÿ]+", lower(pt))
    for word, next_word in zip(words, words[1:]):
        if word == "aos" and next_word in FEMININOS_PLURAL:
            add(findings, "concordancia_nominal", "alta", f"Contração masculina antes de feminino plural: '{pt}'.", f"Trocar 'aos {next_word}' por 'às {next_word}'.")
        elif word == "as" and next_word in MASCULINOS_PLURAL:
            add(findings, "concordancia_nominal", "alta", f"Contração feminina antes de masculino plural: '{pt}'.", f"Trocar 'as {next_word}' por 'aos {next_word}'.")


def audit_passive(code, pt, findings):
    info = verb_info(code)
    if not info:
        return
    voice = info["voice"]
    normalized_pt = lower(pt)
    if voice == "P" and INFINITIVO_ATIVO.fullmatch(normalized_pt):
        add(findings, "passiva_sem_marca", "alta", f"'{code}' é passiva, mas 'pt' está em infinitivo ativo: '{pt}'.", "Revisar para uma forma passiva adequada, quando o contexto exigir.")
    elif voice == "M/P" and INFINITIVO_ATIVO.fullmatch(normalized_pt):
        add(findings, "media_passiva_ambigua", "revisar", f"'{code}' é média ou passiva e 'pt' é infinitivo ativo: '{pt}'.", "Decidir pelo contexto; não corrigir automaticamente.")
    elif voice == "P" and passive_translation(pt):
        if explicit_ser_participle(pt):
            return
        add(findings, "passiva_a_confirmar", "revisar", f"'{code}' é passiva, mas a tradução não explicita claramente a passiva: '{pt}'.", "Confirmar se a glossa pretende particípio, adjetivo verbal ou construção passiva completa.")


def audit_participle_agreement(pt, findings):
    for match in AUX_PLURAL.finditer(lower(pt)):
        participle = match.group(1)
        if likely_singular_participle(participle):
            suggestion = f"Revisar o número do particípio; forma plural provável: '{participle}s'."
            if participle in PARTICIPIOS_IRREGULARES:
                suggestion = "Reescrever a construção; 'sido' não deve ser pluralizado." if PARTICIPIOS_IRREGULARES[participle] is None else f"Revisar o número; forma plural provável: '{PARTICIPIOS_IRREGULARES[participle]}'."
            add(findings, "concordancia_participio", "alta", f"Auxiliar plural com particípio aparentemente singular: '{match.group(0)}'.", suggestion)
    for match in AUX_SINGULAR.finditer(lower(pt)):
        participle = match.group(1)
        if likely_plural_participle(participle):
            add(findings, "concordancia_participio", "alta", f"Auxiliar singular com particípio aparentemente plural: '{match.group(0)}'.", "Revisar o número do particípio conforme o referente real.")


def audit_bad_constructions(pt, findings):
    for pattern, finding, suggestion in BAD_CONSTRUCTIONS:
        if pattern.search(pt):
            add(findings, "construcao_inadequada", "alta", finding, suggestion)


def audit_entry(entry):
    pt = norm(entry.get("pt"))
    code = norm(entry.get("abrev_morf"))
    findings = []
    if not pt:
        add(findings, "pt_vazio", "alta", "Campo 'pt' está vazio.", "Informe uma glossa portuguesa.")
        return findings
    audit_contractions(pt, findings)
    audit_passive(code, pt, findings)
    audit_participle_agreement(pt, findings)
    audit_bad_constructions(pt, findings)
    return findings


def main():
    parser = argparse.ArgumentParser(description="Auditoria v6 de glossas PT por morfologia grega.")
    parser.add_argument("input", type=Path, help="Caminho do arquivo JSON")
    parser.add_argument("--output", type=Path, default=Path("auditoria_dict_flex_v6.csv"), help="CSV de saída")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8-sig") as handle:
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
                writer.writerow({"forma_grega": norm(form), "strongs": norm(entry.get("strongs")), "abrev_morf": norm(entry.get("abrev_morf")), "morfologia": norm(entry.get("morfologia")), "pt": norm(entry.get("pt")), "traducao": norm(entry.get("traducao")), **finding})
    print(f"{count} apontamento(s) gravado(s) em {args.output}")


if __name__ == "__main__":
    main()
