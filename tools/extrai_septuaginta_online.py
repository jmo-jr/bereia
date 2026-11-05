#!/usr/bin/env python3
"""Converte uma página de verbetes do Septuaginta Online em JSON UTF-8."""

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


URL_BASE = "https://www.septuaginta.online/"
LETRAS = (
    "alfa beta gama delta epsilon zeta eta theta iota kappa lambda mi ni xi "
    "omicron pi rho sigma tau upsilon phi chi psi omega"
).split()
BLOCO_HTML = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
GREGO = r"[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f]+"
VERBETE = re.compile(rf"^(?P<lema>{GREGO}(?:[ /]+{GREGO})*)[\s\u00ad]*[-–—]\s*(?P<corpo>.+)$")
FLEXAO = re.compile(
    r"(?<!\w)(?P<rotulo>(?:nominativo|acusativo|genitivo|dativo|vocativo)"
    r"(?:\s+(?:singular|plural))?|"
    r"(?:particípio\s+)?(?:presente|imperfeito|perfeito|mais-que-perfeito|aoristo|futuro)"
    r"(?:\s+(?:indicativo|imperativo|subjuntivo|optativo|infinitivo|particípio|"
    r"ativo|médio|passivo|simples|segundo|primeiro))*|"
    r"infinitivo|particípio|plural|singular|fem\.|masc\.|neutro)"
    rf"(?:\s*[:;]\s*|\s+(?={GREGO}))",
    re.IGNORECASE,
)
HEBRAICO = re.compile(r"\bHeb\.\s*:?\s*(?=[\u0590-\u05ff])", re.IGNORECASE)
TRANSLIT = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ž'’‘ʼ-]+")


class TextoDaPagina(HTMLParser):
    """Reúne os parágrafos de texto da área principal do site."""

    def __init__(self):
        super().__init__()
        self.no_main = False
        self.tag = None
        self.partes = []
        self.paragrafos = []

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.no_main = True
        if self.no_main and tag in BLOCO_HTML:
            self.tag = tag
            self.partes = []
        if tag == "br" and self.tag:
            self.partes.append("\n")

    def handle_data(self, data):
        if self.tag:
            self.partes.append(data)

    def handle_endtag(self, tag):
        if tag == self.tag:
            texto = "".join(self.partes).strip()
            if texto:
                self.paragrafos.append(texto)
            self.tag = None
        if tag == "main":
            self.no_main = False


def separar_verbetes(html):
    pagina = TextoDaPagina()
    pagina.feed(html)
    pagina.close()
    verbetes = []
    iniciais = []
    for paragrafo in pagina.paragrafos:
        linhas = paragrafo.splitlines()
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            inicio = VERBETE.fullmatch(linha)
            if inicio:
                verbetes.append((inicio["lema"].strip(), [linha], inicio["corpo"]))
            elif verbetes:
                verbetes[-1][1].append(linha)
            else:
                iniciais.append(linha)
    if not verbetes:
        raise ValueError("nenhum verbete reconhecido no HTML da página")
    return verbetes, iniciais


def extrair_flexoes(trechos):
    flex = {}
    anterior = None
    for rotulo, valor in trechos:
        if not valor:
            continue
        if rotulo == "plural" and anterior == "nominativo" and isinstance(flex.get(anterior), str):
            flex[anterior] = {"singular": flex[anterior], "plural": valor}
        elif rotulo in flex:
            existente = flex[rotulo]
            flex[rotulo] = existente + [valor] if isinstance(existente, list) else [existente, valor]
        else:
            flex[rotulo] = valor
        anterior = rotulo
    return flex


def extrair_campos(lema, linhas, primeira_linha):
    texto = "\n".join(linhas)
    corpo = " ".join([primeira_linha, *linhas[1:]])
    # Marcadores hebraicos e flexionais podem alternar no mesmo verbete.
    marcadores = sorted(
        [(m.start(), m.end(), m["rotulo"].lower()) for m in FLEXAO.finditer(corpo)]
        + [(m.start(), m.end(), "heb") for m in HEBRAICO.finditer(corpo)]
    )
    abertura = corpo[:marcadores[0][0]] if marcadores else corpo
    abertura = abertura.strip(" .;\u00a0")
    prefixo, virgula, definicao = abertura.partition(",")
    translit = None
    if virgula and TRANSLIT.fullmatch(prefixo.strip()):
        translit = prefixo.strip()
    else:
        # Alguns verbetes trazem a transliteração após a própria definição.
        final = re.search(rf":\s*{re.escape(lema)},\s*([^,]+)$", abertura)
        translit = final[1].strip() if final and TRANSLIT.fullmatch(final[1].strip()) else None
        definicao = abertura[:final.start()] if translit else abertura
    heb = []
    flexoes = []
    for indice, (_, fim, rotulo) in enumerate(marcadores):
        proximo = marcadores[indice + 1][0] if indice + 1 < len(marcadores) else len(corpo)
        valor = corpo[fim:proximo].strip(" .;\u00a0")
        if rotulo == "heb":
            heb.append(valor)
        else:
            flexoes.append((rotulo, valor))
    return {
        "translit": translit,
        "def": definicao.strip(),
        "flex": extrair_flexoes(flexoes),
        "heb": "; ".join(heb) if heb else None,
        "texto_bruto": texto,
    }


def converter(html, url):
    verbetes, iniciais = separar_verbetes(html)
    indice = {}
    for lema, linhas, corpo in verbetes:
        campos = extrair_campos(lema, linhas, corpo)
        if lema not in indice:
            indice[lema] = campos
        elif isinstance(indice[lema], list):
            indice[lema].append(campos)
        else:
            indice[lema] = [indice[lema], campos]
    return {"fonte": url, "texto_inicial": iniciais, "verbetes": indice}, len(verbetes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    seletor = parser.add_mutually_exclusive_group(required=True)
    for letra in LETRAS:
        seletor.add_argument(f"--{letra}", dest="pagina", action="store_const", const=letra)
    seletor.add_argument("--pagina", metavar="CAMINHO", help="outro caminho no mesmo site")
    parser.add_argument("--html", type=Path, help="usar um HTML salvo em vez de baixar a página")
    parser.add_argument("-o", "--saida", type=Path, help="arquivo JSON de saída")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9-]+", args.pagina):
        parser.error("use um caminho simples, como alfa ou beta")
    url = URL_BASE + args.pagina
    saida = args.saida or Path(f"septuaginta-online-{args.pagina}.json")
    try:
        if args.html:
            html = args.html.read_text(encoding="utf-8")
        else:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=30) as resposta:
                html = resposta.read().decode(resposta.headers.get_content_charset() or "utf-8")
        dados, total = converter(html, url)
        saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as erro:
        parser.exit(1, f"Erro ao converter {url}: {erro}\n")
    print(f"{total} verbetes gravados em {saida}")


if __name__ == "__main__":
    main()
