import json
import argparse
from pathlib import Path


def remover_repeticoes(texto: str) -> str:
    partes = [p.strip() for p in texto.split(",")]
    vistos = set()
    resultado = []

    for p in partes:
        if p not in vistos:
            vistos.add(p)
            resultado.append(p)

    return ", ".join(resultado)


def processar(data):

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = remover_repeticoes(v)
            else:
                data[k] = processar(v)
        return data

    elif isinstance(data, list):
        return [processar(x) for x in data]

    return data


def main():

    parser = argparse.ArgumentParser(
        description="Remove palavras repetidas em valores separados por vírgula dentro de um JSON."
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Arquivo JSON de entrada"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Arquivo JSON de saída (se omitido, sobrescreve o de entrada)"
    )

    args = parser.parse_args()

    output = args.output if args.output else args.input

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = processar(data)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()