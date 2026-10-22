import csv
import json
import re
from pathlib import Path

PASTA_SCRIPT = Path(__file__).resolve().parent

ARQUIVO_CSV = PASTA_SCRIPT / "correcoes_dicionario_pt.csv"
ARQUIVO_JSON = PASTA_SCRIPT.parent / "src" / "_data" / "dict_flex_nt-lxx_greek-pt.json"
ARQUIVO_SAIDA = PASTA_SCRIPT / "correcoes_dicionario_pt_com_morfologia.csv"

COLUNA_GREGO = "grego"
COLUNA_MORFOLOGIA = "abrev_morf"


def normalizar_texto(valor):
    """Remove espaços externos e normaliza separadores invisíveis."""
    if valor is None:
        return ""

    valor = str(valor)
    valor = valor.replace("\ufeff", "")
    valor = valor.replace("\u200b", "")
    valor = valor.replace("\u00a0", " ")
    return valor.strip()


def remover_diacriticos_externos(valor):
    """
    Mantém o grego normalmente, mas também permite uma comparação
    alternativa removendo caracteres de pontuação externos.
    """
    valor = normalizar_texto(valor)
    return valor.strip(" .,;:!?()[]{}\"'")


def carregar_dicionario(caminho):
    with caminho.open("r", encoding="utf-8-sig") as arquivo:
        return json.load(arquivo)


def localizar_entrada(dicionario, termo_grego):
    termo = normalizar_texto(termo_grego)
    termo_sem_pontuacao = remover_diacriticos_externos(termo)

    # Caso mais comum: o termo grego é a própria chave do JSON.
    if isinstance(dicionario, dict):
        if termo in dicionario:
            return dicionario[termo]

        if termo_sem_pontuacao in dicionario:
            return dicionario[termo_sem_pontuacao]

        # Caso o JSON seja organizado por IDs ou outros agrupamentos.
        for chave, entrada in dicionario.items():
            if not isinstance(entrada, dict):
                continue

            candidatos = [
                entrada.get("grego"),
                entrada.get("forma"),
                entrada.get("chave_json"),
                chave,
            ]

            candidatos = {
                normalizar_texto(valor)
                for valor in candidatos
                if valor is not None
            }

            if termo in candidatos or termo_sem_pontuacao in candidatos:
                return entrada

    # Caso o JSON seja uma lista de objetos.
    elif isinstance(dicionario, list):
        for entrada in dicionario:
            if not isinstance(entrada, dict):
                continue

            candidatos = [
                entrada.get("grego"),
                entrada.get("forma"),
                entrada.get("chave_json"),
            ]

            candidatos = {
                normalizar_texto(valor)
                for valor in candidatos
                if valor is not None
            }

            if termo in candidatos or termo_sem_pontuacao in candidatos:
                return entrada

    return None


def obter_abrev_morf(entrada):
    if not isinstance(entrada, dict):
        return ""

    valor = entrada.get(COLUNA_MORFOLOGIA, "")

    if valor is None:
        return ""

    if isinstance(valor, list):
        return " | ".join(str(item) for item in valor)

    if isinstance(valor, dict):
        return json.dumps(
            valor,
            ensure_ascii=False,
            separators=(",", ":")
        )

    return str(valor)


def detectar_dialeto(caminho):
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        amostra = arquivo.read(8192)

    try:
        return csv.Sniffer().sniff(amostra, delimiters=",;\t")
    except csv.Error:
        dialeto = csv.excel
        dialeto.delimiter = ";"
        return dialeto


def main():
    if not ARQUIVO_CSV.exists():
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado:\n{ARQUIVO_CSV}"
        )

    if not ARQUIVO_JSON.exists():
        raise FileNotFoundError(
            f"Arquivo JSON não encontrado:\n{ARQUIVO_JSON}"
        )

    dicionario = carregar_dicionario(ARQUIVO_JSON)
    dialeto = detectar_dialeto(ARQUIVO_CSV)

    with ARQUIVO_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:
        leitor = csv.DictReader(arquivo, dialect=dialeto)

        if leitor.fieldnames is None:
            raise ValueError("O CSV não possui cabeçalho.")

        cabecalho = list(leitor.fieldnames)

        if COLUNA_GREGO not in cabecalho:
            raise ValueError(
                f"A coluna '{COLUNA_GREGO}' não foi encontrada.\n"
                f"Colunas disponíveis: {cabecalho}"
            )

        if COLUNA_MORFOLOGIA not in cabecalho:
            cabecalho.append(COLUNA_MORFOLOGIA)

        linhas = []
        encontrados = 0
        nao_encontrados = 0
        vazios = 0

        for numero, linha in enumerate(leitor, start=2):
            termo_grego = linha.get(COLUNA_GREGO, "")
            termo_grego = normalizar_texto(termo_grego)

            if not termo_grego:
                linha[COLUNA_MORFOLOGIA] = ""
                vazios += 1
                linhas.append(linha)
                continue

            entrada = localizar_entrada(dicionario, termo_grego)
            morfologia = obter_abrev_morf(entrada)

            linha[COLUNA_MORFOLOGIA] = morfologia
            linhas.append(linha)

            if morfologia:
                encontrados += 1
            else:
                nao_encontrados += 1

    with ARQUIVO_SAIDA.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=cabecalho,
            dialect=dialeto,
            extrasaction="ignore"
        )

        escritor.writeheader()
        escritor.writerows(linhas)

    print("Processamento concluído.")
    print(f"CSV original:       {ARQUIVO_CSV}")
    print(f"JSON consultado:    {ARQUIVO_JSON}")
    print(f"CSV gerado:         {ARQUIVO_SAIDA}")
    print(f"Linhas processadas: {len(linhas)}")
    print(f"Encontrados:        {encontrados}")
    print(f"Não encontrados:    {nao_encontrados}")
    print(f"Gregos vazios:      {vazios}")


if __name__ == "__main__":
    main()
