import csv
import json
import re
import sys
from pathlib import Path

import language_tool_python


ARQUIVO_ENTRADA = Path(
    "dict_flex_nt-lxx_greek-pt_to_revision.csv"
)

ARQUIVO_SAIDA = Path(
    "dict_flex_nt-lxx_greek-pt_revisado.csv"
)

ARQUIVO_RELATORIO = Path(
    "dict_flex_nt-lxx_greek-pt_relatorio.csv"
)


def detectar_numero(morfologia):
    texto = morfologia.lower()

    if "plural" in texto:
        return "plural"

    if "singular" in texto:
        return "singular"

    return None


def detectar_genero(morfologia):
    texto = morfologia.lower()

    if "feminino" in texto:
        return "feminino"

    if "masculino" in texto:
        return "masculino"

    if "neutro" in texto:
        return "neutro"

    return None


def detectar_pessoa(morfologia):
    texto = morfologia.lower()

    if "1ª pessoa plural" in texto:
        return ("1", "plural")

    if "2ª pessoa plural" in texto:
        return ("2", "plural")

    if "3ª pessoa plural" in texto:
        return ("3", "plural")

    if "1ª pessoa singular" in texto:
        return ("1", "singular")

    if "2ª pessoa singular" in texto:
        return ("2", "singular")

    if "3ª pessoa singular" in texto:
        return ("3", "singular")

    return None


def e_forma_verbal(morfologia):
    return morfologia.lower().startswith("verbo")


def classificar_ocorrencia(ocorrencia, morfologia, original, sugestao):
    mensagem = ocorrencia.message.lower()
    regra = ocorrencia.rule_id.lower()

    if "spell" in regra or "typo" in mensagem:
        categoria = "ORTOGRAFIA"
        confianca = "ALTA"
    elif any(
        termo in mensagem
        for termo in [
            "concord",
            "plural",
            "singular",
            "masculin",
            "feminin",
            "verbo",
            "particípio",
        ]
    ):
        categoria = "CONCORDANCIA"
        confianca = "PROVAVEL"
    elif "pontua" in mensagem:
        categoria = "PONTUACAO"
        confianca = "PROVAVEL"
    else:
        categoria = "REVISAR"
        confianca = "INCERTO"

    if e_forma_verbal(morfologia):
        pessoa = detectar_pessoa(morfologia)

        if pessoa and pessoa[1] == "plural":
            if re.search(r"\b(foram|sejam|serão|estão|ficam|ficando)\b", original.lower()):
                confianca = "PROVAVEL"

    if original.strip() == sugestao.strip():
        confianca = "IGNORAR"

    return categoria, confianca


def obter_sugestoes(tool, texto, morfologia, linha, campo, dados):
    if not texto or not texto.strip():
        return texto, []

    ocorrencias = tool.check(texto)
    relatorio = []

    for ocorrencia in ocorrencias:
        sugestoes = ocorrencia.replacements[:5]

        if not sugestoes:
            continue

        sugestao = sugestoes[0]
        categoria, confianca = classificar_ocorrencia(
            ocorrencia,
            morfologia,
            texto,
            sugestao,
        )

        aceitar = confianca in {"ALTA", "PROVAVEL"}

        relatorio.append(
            {
                "linha": linha,
                "chave_json": dados.get("chave_json", ""),
                "grego": dados.get("grego", ""),
                "campo": campo,
                "texto_original": texto,
                "sugestao": sugestao,
                "mensagem": ocorrencia.message,
                "regra": ocorrencia.rule_id,
                "categoria": categoria,
                "confianca": confianca,
                "status": "SUGESTAO_ACEITA" if aceitar else "INCERTO",
            }
        )

    texto_revisado = texto

    for item in reversed(relatorio):
        if item["status"] != "SUGESTAO_ACEITA":
            continue

        ocorrencia = next(
            (
                ocorrencia
                for ocorrencia in ocorrencias
                if ocorrencia.message == item["mensagem"]
                and ocorrencia.rule_id == item["regra"]
            ),
            None,
        )

        if ocorrencia is None:
            continue

        inicio = ocorrencia.offset
        fim = inicio + ocorrencia.error_length

        texto_revisado = (
            texto_revisado[:inicio]
            + item["sugestao"]
            + texto_revisado[fim:]
        )

    return texto_revisado, relatorio


def main():
    if not ARQUIVO_ENTRADA.exists():
        print(f"Arquivo não encontrado: {ARQUIVO_ENTRADA}")
        sys.exit(1)

    with ARQUIVO_ENTRADA.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:
        leitor = csv.DictReader(arquivo)
        campos_originais = leitor.fieldnames or []
        linhas = list(leitor)

    campos_saida = campos_originais + [
        "traducao_revisada",
        "pt_revisado",
        "status_traducao",
        "status_pt",
        "observacao",
    ]

    linhas_saida = []
    relatorio_total = []

    with language_tool_python.LanguageTool("pt-BR") as tool:
        for numero_linha, dados in enumerate(linhas, start=2):
            morfologia = dados.get("morfologia", "")
            traducao = dados.get("traducao", "")
            pt = dados.get("pt", "")

            traducao_revisada, relatorio_traducao = obter_sugestoes(
                tool,
                traducao,
                morfologia,
                numero_linha,
                "traducao",
                dados,
            )

            pt_revisado, relatorio_pt = obter_sugestoes(
                tool,
                pt,
                morfologia,
                numero_linha,
                "pt",
                dados,
            )

            relatorio_linha = relatorio_traducao + relatorio_pt
            relatorio_total.extend(relatorio_linha)

            status_traducao = (
                "OK"
                if traducao_revisada == traducao
                else "SUGESTAO"
            )

            status_pt = (
                "OK"
                if pt_revisado == pt
                else "SUGESTAO"
            )

            observacoes = [
                item["mensagem"]
                for item in relatorio_linha
            ]

            saida = dict(dados)
            saida["traducao_revisada"] = traducao_revisada
            saida["pt_revisado"] = pt_revisado
            saida["status_traducao"] = status_traducao
            saida["status_pt"] = status_pt
            saida["observacao"] = " | ".join(observacoes)

            linhas_saida.append(saida)

            if numero_linha % 500 == 0:
                print(f"Processadas {numero_linha - 1} linhas...")

    with ARQUIVO_SAIDA.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos_saida,
        )
        escritor.writeheader()
        escritor.writerows(linhas_saida)

    campos_relatorio = [
        "linha",
        "chave_json",
        "grego",
        "campo",
        "texto_original",
        "sugestao",
        "mensagem",
        "regra",
        "categoria",
        "confianca",
        "status",
    ]

    with ARQUIVO_RELATORIO.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos_relatorio,
        )
        escritor.writeheader()
        escritor.writerows(relatorio_total)

    print()
    print("Processamento concluído.")
    print(f"Arquivo revisado: {ARQUIVO_SAIDA}")
    print(f"Relatório: {ARQUIVO_RELATORIO}")
    print(f"Sugestões registradas: {len(relatorio_total)}")


if __name__ == "__main__":
    main()
