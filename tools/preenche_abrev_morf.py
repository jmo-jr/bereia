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

    Percorre recursivamente listas e objetos JSON.
    """
    indice = {}

    def percorrer(obj):
        if isinstance(obj, dict):
            if "morfologia" in obj and "abrev_morf" in obj:
                morfologia = obj["morfologia"]

                if morfologia:
                    indice[morfologia] = obj["abrev_morf"]

            for valor in obj.values():
                percorrer(valor)

        elif isinstance(obj, list):
            for item in obj:
                percorrer(item)

    percorrer(dados)
    return indice


def atualizar_destino(dados_destino, indice):
    """
    Procura objetos no destino com 'morfologia'
    e atualiza 'abrev_morf' quando houver correspondência.
    """
    encontrados = 0
    atualizados = 0

    def percorrer(obj):
        nonlocal encontrados, atualizados

        if isinstance(obj, dict):
            if "morfologia" in obj:
                morfologia = obj["morfologia"]

                if morfologia in indice:
                    encontrados += 1

                    novo_valor = indice[morfologia]

                    if obj.get("abrev_morf") != novo_valor:
                        obj["abrev_morf"] = novo_valor
                        atualizados += 1

            for valor in obj.values():
                percorrer(valor)

        elif isinstance(obj, list):
            for item in obj:
                percorrer(item)

    percorrer(dados_destino)

    return encontrados, atualizados


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("python atualizar_abrev_morf.py arquivo_origem.json")
        sys.exit(1)

    arquivo_origem = Path(sys.argv[1])
    arquivo_destino = Path("tools/nt-missing-lemmas-FINAL.json")

    if not arquivo_origem.exists():
        print(f"Erro: arquivo de origem não encontrado: {arquivo_origem}")
        sys.exit(1)

    if not arquivo_destino.exists():
        print(f"Erro: arquivo de destino não encontrado: {arquivo_destino}")
        sys.exit(1)

    origem = carregar_json(arquivo_origem)
    destino = carregar_json(arquivo_destino)

    indice = criar_indice_morfologia(origem)

    encontrados, atualizados = atualizar_destino(destino, indice)

    with open(arquivo_destino, "w", encoding="utf-8") as arquivo:
        json.dump(
            destino,
            arquivo,
            ensure_ascii=False,
            indent=2
        )
        arquivo.write("\n")

    print(f"Formas de morfologia encontradas na origem: {len(indice)}")
    print(f"Correspondências encontradas no destino: {encontrados}")
    print(f"Objetos atualizados: {atualizados}")
    print(f"Arquivo atualizado: {arquivo_destino}")


if __name__ == "__main__":
    main()