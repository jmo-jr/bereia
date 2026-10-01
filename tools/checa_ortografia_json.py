# filepath: tools/checa_ortografia_json.py
import argparse
import csv
import json
import re
from pathlib import Path

from AppKit import NSSpellChecker
from Foundation import NSNotFound

PALAVRA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)*")


def percorrer(valor, caminho="$"):
    if isinstance(valor, dict):
        for chave, filho in valor.items():
            caminho_filho = f"{caminho}.{chave}"
            yield from percorrer(filho, caminho_filho)
    elif isinstance(valor, list):
        for indice, filho in enumerate(valor):
            yield from percorrer(filho, f"{caminho}[{indice}]")
    elif isinstance(valor, str):
        yield caminho, valor


def verificar(palavra, corretor):
    resultado = corretor.checkSpellingOfString_startingAt_(palavra, 0)
    local = resultado.location if hasattr(resultado, "location") else resultado[0]

    if local == NSNotFound:
        return None

    sugestoes = corretor.guessesForWord_(palavra) or []
    return list(sugestoes)


def main():
    parser = argparse.ArgumentParser(
        description="Verifica campos selecionados de um JSON com o corretor do macOS."
    )
    parser.add_argument("arquivo", type=Path)
    parser.add_argument(
        "--keys",
        nargs="+",
        default=["pt", "traducao"],
        help="Chaves de texto a verificar (padrão: pt traducao).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("relatorio-ortografia.csv"),
    )
    args = parser.parse_args()

    idiomas = list(NSSpellChecker.sharedSpellChecker().availableLanguages())
    corretor = NSSpellChecker.sharedSpellChecker()

    if "pt_BR" not in idiomas or not corretor.setLanguage_("pt_BR"):
        raise SystemExit(
            f"O idioma pt_BR não está disponível no corretor do macOS. "
            f"Idiomas disponíveis: {', '.join(idiomas)}"
        )

    with args.arquivo.open(encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    cache = {}
    relatorio = []

    for caminho, texto in percorrer(dados):
        chave = caminho.rsplit(".", 1)[-1]
        if chave not in args.keys:
            continue

        for correspondencia in PALAVRA.finditer(texto):
            palavra = correspondencia.group()
            if palavra not in cache:
                cache[palavra] = verificar(palavra, corretor)

            sugestoes = cache[palavra]
            if sugestoes is not None:
                inicio = max(0, correspondencia.start() - 35)
                fim = min(len(texto), correspondencia.end() + 35)
                contexto = texto[inicio:fim].replace("\n", " ")
                relatorio.append(
                    [caminho, palavra, " | ".join(sugestoes), contexto]
                )

    with args.output.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["caminho_json", "palavra", "sugestões", "contexto"])
        escritor.writerows(relatorio)

    print(f"{len(relatorio)} possíveis ocorrências registradas em {args.output}")


if __name__ == "__main__":
    main()