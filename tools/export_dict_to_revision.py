import argparse
import csv
import json
from pathlib import Path

CAMPOS = ("grego", "traducao", "pt", "morfologia")


def valor_csv(valor):
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    return json.dumps(valor, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Exporta campos do dicionário grego para CSV."
    )
    parser.add_argument(
        "--entrada",
        default="src/_data/dict_flex_nt-lxx_greek-pt.json",
        help="Caminho do arquivo JSON.",
    )
    parser.add_argument(
        "--saida",
        default="src/_data/dict_flex_nt-lxx_greek-pt.csv",
        help="Caminho do CSV a criar.",
    )
    args = parser.parse_args()

    entrada = Path(args.entrada)
    saida = Path(args.saida)

    with entrada.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, dict):
        raise ValueError("A raiz do JSON precisa ser um objeto.")

    saida.parent.mkdir(parents=True, exist_ok=True)

    with saida.open("w", encoding="utf-8-sig", newline="") as arquivo:
        colunas = ["chave_json", *CAMPOS]
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()

        for chave, entrada_json in dados.items():
            entrada_json = entrada_json if isinstance(entrada_json, dict) else {}
            linha = {"chave_json": chave}
            linha.update({
                campo: valor_csv(entrada_json.get(campo, ""))
                for campo in CAMPOS
            })
            escritor.writerow(linha)

    print(f"Exportadas {len(dados)} entradas para: {saida}")


if __name__ == "__main__":
    main()