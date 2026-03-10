import json
import re
from pathlib import Path

STRONGS_FILE = Path("src/_data/strongs_greek_pt_defs.json")
PATTERN = re.compile(r"(G\d{1,4}):\s*([^\";,]*)")

def load_dictionary(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_strongs():
    with open(STRONGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # garante mapa simples {G0001: definição}
    return {k: v.split(":")[-1].strip() if ":" in v else v for k, v in data.items()}

def transform_dictionary(data, strongs):

    def process(value):

        if isinstance(value, dict):
            for k in value:
                value[k] = process(value[k])
            return value

        if isinstance(value, list):
            return [process(v) for v in value]

        if isinstance(value, str):

            def repl(match):
                codigo = match.group(1)
                if codigo in strongs:
                    return f"{codigo}: {strongs[codigo]}"
                return match.group(0)

            return PATTERN.sub(repl, value)

        return value

    return process(data)

def write_dictionary(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)