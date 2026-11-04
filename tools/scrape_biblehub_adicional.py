from datetime import datetime
from html.parser import HTMLParser
import json
import re
import shutil
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen


JSON_PATH = Path("docs/notas-lexicais-piloto.json")
ENTRY_RE = re.compile(r'(?ms)^(  "(G\d+)": \{\n)(.*?)(^  \})(,?)$')
ADDITIONAL_RE = re.compile(r'(?m)^    "adicional": "(?:\\.|[^"\\])*"(,?)$')
KEY_RE = re.compile(r"G(\d+)")


class DiscoveryParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.found = False
        self.finished = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.finished or self.inside or tag != "p":
            return

        classes = dict(attrs).get("class", "").split()
        if "discovery" in classes:
            self.inside = True
            self.found = True

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.inside and tag == "p":
            self.inside = False
            self.finished = True


def fetch_discovery(strong_number):
    url = f"https://biblehub.com/greek/{strong_number}.htm"
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BereiaLexicalScraper/1.0)"},
    )

    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(charset)

    parser = DiscoveryParser()
    parser.feed(html)
    if not parser.found:
        print(f"Aviso: p.discovery não encontrado em {url}; gravando campo vazio.")
        return ""

    return " ".join("".join(parser.parts).split())


def update_entry(match, scraped_text):
    head, key, body, closing, comma = match.groups()
    encoded_text = json.dumps(scraped_text, ensure_ascii=False)

    if re.search(r'(?m)^    "adicional":', body):
        if not ADDITIONAL_RE.search(body):
            raise ValueError(f'Campo "adicional" existente tem formato inesperado em {key}')

        body = ADDITIONAL_RE.sub(
            lambda found: f'    "adicional": {encoded_text}{found.group(1)}',
            body,
            count=1,
        )
    else:
        lines = body.rstrip("\n").split("\n")
        if not lines or not lines[-1].strip():
            raise ValueError(f"Formato inesperado na entrada {key}")

        if not lines[-1].rstrip().endswith(","):
            lines[-1] += ","

        lines.append(f'    "adicional": {encoded_text}')
        body = "\n".join(lines) + "\n"

    return f"{head}{body}{closing}{comma}"


def main():
    with JSON_PATH.open(encoding="utf-8") as file:
        source = file.read()

    entries = json.loads(source)
    if not isinstance(entries, dict):
        raise ValueError("O JSON deve conter um objeto de entradas no nível principal.")

    entry_matches = list(ENTRY_RE.finditer(source))
    matched_keys = [match.group(2) for match in entry_matches]
    if len(matched_keys) != len(entries) or set(matched_keys) != set(entries):
        raise ValueError(
            "A estrutura do JSON não corresponde ao formato esperado; nada foi gravado."
        )

    scraped = {}
    for index, key in enumerate(entries):
        key_match = KEY_RE.fullmatch(key)
        if not key_match:
            raise ValueError(f"Chave fora do formato esperado: {key}")

        scraped[key] = fetch_discovery(key_match.group(1))
        print(f"{key}: texto capturado")

        if index < len(entries) - 1:
            time.sleep(0.7)

    updated = ENTRY_RE.sub(
        lambda match: update_entry(match, scraped[match.group(2)]),
        source,
    )

    validated = json.loads(updated)
    for key, text in scraped.items():
        if validated[key].get("adicional") != text:
            raise ValueError(f"Validação falhou para {key}; nada foi gravado.")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=JSON_PATH.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(updated)

        backup_path = JSON_PATH.with_name(
            f"{JSON_PATH.name}.{datetime.now():%Y%m%d-%H%M%S-%f}.bak"
        )
        shutil.copy2(JSON_PATH, backup_path)
        temp_path.replace(JSON_PATH)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()

    print(f"Atualizado: {JSON_PATH}")
    print(f"Backup: {backup_path}")


if __name__ == "__main__":
    main()
