import json
import sys
from pathlib import Path


def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def criar_indice_morfologia(dados):
    """
    Cria um índice:
        morfologia -> abrev_morf

    A origem é percorrida recursivamente para encontrar
    todos os objetos que possuem as duas chaves.
    """
    indice = {}

    def percorrer(obj):
        if isinstance(obj, dict):
            if "morfologia" in obj and "abrev_morf" in obj:
                morfologia = obj["morfologia"]
                abrev_morf = obj["abrev_morf"]

                if morfologia and abrev_morf:
                    indice[morfologia] = abrev_morf

            for valor in obj.values():
                percorrer(valor)

        elif isinstance(obj, list):
            for item in obj:
                percorrer(item)

    percorrer(dados)

    return indice


def atualizar_destino(dados_destino, indice):
    """
    Procura objetos no destino que possuem 'morfologia'.

    Quando a morfologia existir no índice da origem,
    copia obrigatoriamente o respectivo 'abrev_morf'
    para o objeto do destino.
    """
    correspondencias = 0
    atualizados = 0

    def percorrer(obj):
        nonlocal correspondencias, atualizados

        if isinstance(obj, dict):

            if "morfologia" in obj:
                morfologia = obj["morfologia"]

                if morfologia in indice:
                    correspondencias += 1

                    # Copia o valor da origem para o destino.
                    obj["abrev_morf"] = indice[morfologia]

                    atualizados += 1

            for valor in obj.values():
                percorrer(valor)

        elif isinstance(obj, list):
            for item in obj:
                percorrer(item)

    percorrer(dados_destino)

    return correspondencias, atualizados


def main():

    if len(sys.argv) < 2:
        print("Uso:")
        print("python3 tools/preenche_abrev_morf.py src/_data/nt_greek-pt_dict.json")
        sys.exit(1)

    # Arquivo de origem passado pelo terminal.
    arquivo_origem = Path(sys.argv[1])

    # Arquivo de destino fica na mesma pasta deste script.
    arquivo_destino = (
        Path(__file__).resolve().parent
        / "nt-missing-lemmas-FINAL.json"
    )

    if not arquivo_origem.exists():
        print(f"ERRO: arquivo de origem não encontrado:")
        print(f"  {arquivo_origem.resolve()}")
        sys.exit(1)

    if not arquivo_destino.exists():
        print(f"ERRO: arquivo de destino não encontrado:")
        print(f"  {arquivo_destino.resolve()}")
        sys.exit(1)

    print("Arquivo de origem:")
    print(f"  {arquivo_origem.resolve()}")

    print("Arquivo de destino:")
    print(f"  {arquivo_destino.resolve()}")

    print()

    # Carrega os dois arquivos.
    origem = carregar_json(arquivo_origem)
    destino = carregar_json(arquivo_destino)

    # Cria o índice morfologia -> abrev_morf a partir da origem.
    indice = criar_indice_morfologia(origem)

    print(f"Morfologias com abrev_morf na origem: {len(indice)}")

    # Preenche o destino.
    correspondencias, atualizados = atualizar_destino(
        destino,
        indice
    )

    print(f"Correspondências encontradas: {correspondencias}")
    print(f"Objetos preenchidos: {atualizados}")

    # Salva primeiro em arquivo temporário.
    arquivo_temporario = arquivo_destino.with_suffix(
        arquivo_destino.suffix + ".tmp"
    )

    with open(arquivo_temporario, "w", encoding="utf-8") as arquivo:
        json.dump(
            destino,
            arquivo,
            ensure_ascii=False,
            indent=2
        )
        arquivo.write("\n")

    # Substitui o arquivo original pelo arquivo atualizado.
    arquivo_temporario.replace(arquivo_destino)

    print()
    print("Arquivo atualizado com sucesso:")
    print(f"  {arquivo_destino.resolve()}")


if __name__ == "__main__":
    main()