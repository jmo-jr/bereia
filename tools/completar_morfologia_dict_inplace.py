#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

TEMPOS = {
    "P": "Presente",
    "I": "Imperfeito",
    "A": "Aoristo",
    "F": "Futuro",
    "R": "Perfeito",
    "L": "Mais-que-perfeito",
    "T": "Futuro Perfeito",
}

MODOS = {
    "I": "Indicativo",
    "S": "Subjuntivo",
    "O": "Optativo",
    "M": "Imperativo",
    "N": "Infinitivo",
    "P": "Particípio",
}

VOZES = {
    "A": "Ativa",
    "M": "Média",
    "P": "Passiva",
    "M/P": "Média ou Passiva",
}

CASOS = {
    "N": "Nominativo",
    "G": "Genitivo",
    "D": "Dativo",
    "A": "Acusativo",
    "V": "Vocativo",
}

GENEROS = {
    "M": "Masculino",
    "F": "Feminino",
    "N": "Neutro",
}

NUMEROS = {
    "S": "Singular",
    "P": "Plural",
}

PESSOAS = {
    "1": "1ª Pessoa",
    "2": "2ª Pessoa",
    "3": "3ª Pessoa",
}


def gerar_morfologia_verbo(code):
    parts = code.split("-")
    if len(parts) < 2 or parts[0] != "V":
        return None

    principal = parts[1]
    if len(principal) < 3:
        return None

    tempo = TEMPOS.get(principal[0], f"Tempo {principal[0]}")
    modo = MODOS.get(principal[1], f"Modo {principal[1]}")
    voz_code = principal[2:]
    voz = VOZES.get(voz_code, f"Voz {voz_code}")
    resultado = f"Verbo - {tempo} {modo} {voz}"

    if len(parts) < 3:
        return resultado

    final = parts[2]
    if modo == "Particípio" and len(final) >= 3:
        caso = CASOS.get(final[0], f"Caso {final[0]}")
        genero = GENEROS.get(final[1], f"Gênero {final[1]}")
        numero = NUMEROS.get(final[2], f"Número {final[2]}")
        resultado += f" - {caso} {genero} {numero}"
    elif modo not in {"Infinitivo", "Particípio"} and len(final) >= 2:
        pessoa = PESSOAS.get(final[0], f"{final[0]}ª Pessoa")
        numero = NUMEROS.get(final[1], f"Número {final[1]}")
        resultado += f" - {pessoa} {numero}"

    return resultado


def gerar_morfologia_nominal(code):
    parts = code.split("-")
    if len(parts) < 2 or len(parts[1]) < 3:
        return None

    classes = {
        "S": "Substantivo",
        "A": "Adjetivo",
        "T": "Artigo",
        "D": "Demonstrativo",
        "P": "Pronome",
    }
    classe = classes.get(code[0], f"Classe {code[0]}")
    final = parts[1]
    caso = CASOS.get(final[0], f"Caso {final[0]}")
    genero = GENEROS.get(final[1], f"Gênero {final[1]}")
    numero = NUMEROS.get(final[2], f"Número {final[2]}")
    return f"{classe} - {caso} {genero} {numero}"


def gerar_morfologia(abrev_morf):
    code = str(abrev_morf or "").strip()
    if not code:
        return None
    if code.startswith("V-"):
        return gerar_morfologia_verbo(code)
    return gerar_morfologia_nominal(code)


def main():
    parser = argparse.ArgumentParser(description="Atualiza morfologia no próprio arquivo JSON.")
    parser.add_argument("input", type=Path, help="Arquivo JSON a ser alterado")
    parser.add_argument("--all", action="store_true", help="Recalcula todas as morfologias")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8-sig") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise SystemExit("Esperado um objeto JSON indexado pelas formas gregas.")

    alterados = 0
    ignorados = 0

    for entry in data.values():
        if not isinstance(entry, dict):
            continue

        nova = gerar_morfologia(entry.get("abrev_morf"))
        if nova is None:
            ignorados += 1
            continue

        atual = str(entry.get("morfologia") or "").strip()
        incompleta = not atual or len(atual.split()) < 4

        if args.all or incompleta:
            if atual != nova:
                entry["morfologia"] = nova
                alterados += 1

    with args.input.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"{alterados} entrada(s) alterada(s); {ignorados} sem código reconhecido.")


if __name__ == "__main__":
    main()
