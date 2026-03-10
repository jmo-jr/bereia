import json
import re
from pathlib import Path
from typing import Optional, List

STRONGS_FILE = Path("src/_data/strongs_greek_pt_defs.json")

PATTERN = re.compile(r"(G\d{1,4})\s*:\s*(.*)")


def load_strongs():
    with open(STRONGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # garante formato simples
    strongs = {}
    for k, v in data.items():
        if isinstance(v, str):
            strongs[k] = v.split(":")[-1].strip()
    return strongs


def transform_dictionary(data, strongs, strong_targets: Optional[List[str]] = None):

    def process(node):

        if isinstance(node, dict):
            if "verbete" in node and isinstance(node["verbete"], str):
                texto = node["verbete"].strip()
                match = PATTERN.match(texto)
                if match:
                    codigo = match.group(1)
                    if strong_targets is None or codigo in strong_targets:
                        definicao = strongs.get(codigo)
                        if definicao:
                            node["verbete"] = f"{codigo}: {definicao}"
            for k, v in node.items():
                node[k] = process(v)
            return node
        elif isinstance(node, list):
            return [process(x) for x in node]
        return node

    return process(data)