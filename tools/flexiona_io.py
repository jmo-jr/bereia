"""Acesso às flexões e gravação sem reformatar o JSON de entrada."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Set

DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "src/_data/dict_lex_nt-lxx_greek-pt.json"


@dataclass
class Entry:
    label: str
    strong: str
    target: Dict[str, Any]
    payload: Dict[str, Any]


def iter_entries(data: Dict[str, Any]) -> Iterator[Entry]:
    """Não indexa por grego: formas repetidas permanecem registros distintos."""
    for key, group in data.items():
        if not isinstance(group, dict):
            raise ValueError(f"Entrada inválida: {key}")
        if "flexoes" not in group:
            yield Entry(key, str(group.get("strongs", "")).strip(), group, dict(group))
            continue
        if not isinstance(group["flexoes"], list):
            raise ValueError(f"Lista de flexões inválida: {key}")
        for index, flex in enumerate(group["flexoes"]):
            if not isinstance(flex, dict):
                raise ValueError(f"Flexão inválida: {key}[{index}]")
            payload = dict(flex)
            payload["strongs"] = key
            if "verbete" not in payload and "verbete" in group:
                payload["verbete"] = group["verbete"]
            if not isinstance(payload.get("verbete"), str):
                raise ValueError(f"Verbete não definido para {key}[{index}]; informe-o na flexão ou no grupo.")
            yield Entry(f"{key}[{index}] {flex.get('grego', '')}", str(key).strip(), flex, payload)


def preview(data: Dict[str, Any], strong_filter: Optional[Set[str]], limit: int,
            verbs: bool = True, nonverbs: bool = True) -> None:
    if limit <= 0:
        return
    shown = 0
    for entry in iter_entries(data):
        if strong_filter and entry.strong not in strong_filter:
            continue
        is_verb = entry.payload.get("abrev_morf", "").startswith("V")
        if (is_verb and not verbs) or (not is_verb and not nonverbs):
            continue
        print(f"{entry.label}: {entry.target.get('traducao', '')}")
        shown += 1
        if shown >= limit:
            break


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Chave JSON repetida: {key}")
        result[key] = value
    return result


def load_dictionary(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle, object_pairs_hook=_unique_object)
    if not isinstance(data, dict):
        raise ValueError("O dicionário deve ser um objeto JSON.")
    return data


def _patch_json(text: str, updated: Any) -> str:
    """Substitui somente valores alterados e insere campos novos sem reordenar.

    As rotinas de flexão não removem chaves nem mudam a estrutura dos arrays.
    Mudanças estruturais inesperadas são recusadas em vez de perder dados.
    """
    decoder = json.JSONDecoder(object_pairs_hook=_unique_object)
    spans = {}
    objects = {}

    def skip(pos):
        while pos < len(text) and text[pos] in " \t\r\n\ufeff":
            pos += 1
        return pos

    def scan(pos, route):
        pos = skip(pos)
        start = pos
        if text[pos] == "{":
            pos = skip(pos + 1)
            last_end = start + 1
            keys = []
            while text[pos] != "}":
                key, pos = decoder.raw_decode(text, pos)
                keys.append(key)
                pos = skip(pos)
                if text[pos] != ":":
                    raise ValueError("Separador JSON inválido")
                pos = scan(pos + 1, route + (key,))
                last_end = pos
                pos = skip(pos)
                if text[pos] == ",":
                    pos = skip(pos + 1)
            objects[route] = (start, pos, last_end, keys)
            pos += 1
        elif text[pos] == "[":
            pos = skip(pos + 1)
            index = 0
            while text[pos] != "]":
                pos = scan(pos, route + (index,))
                index += 1
                pos = skip(pos)
                if text[pos] == ",":
                    pos = skip(pos + 1)
            pos += 1
        else:
            _, pos = decoder.raw_decode(text, pos)
        spans[route] = (start, pos)
        return pos

    original = json.loads(text.lstrip("\ufeff"), object_pairs_hook=_unique_object)
    scan(0, ())
    patches = []
    encode = lambda value: json.dumps(value, ensure_ascii=False)

    def compare(old, new, route):
        if isinstance(old, dict) and isinstance(new, dict):
            if not old.keys() <= new.keys():
                raise ValueError("A flexão não pode remover campos do JSON.")
            for key in old:
                compare(old[key], new[key], route + (key,))
            added = [key for key in new if key not in old]
            if added:
                start, end, last_end, keys = objects[route]
                newline = "\r\n" if "\r\n" in text else "\n"
                if "\n" in text[start:end]:
                    line = text.rfind("\n", 0, start) + 1
                    parent_indent = len(text[line:start]) - len(text[line:start].lstrip(" \t"))
                    indent = " " * (parent_indent + 2)
                    if keys:
                        child_start = spans[route + (keys[0],)][0]
                        child_line = text.rfind("\n", 0, child_start) + 1
                        prefix = text[child_line:child_start]
                        if prefix.lstrip().startswith('"'):
                            indent = prefix[:len(prefix) - len(prefix.lstrip(" \t"))]
                    separator = newline + indent
                else:
                    separator = " "
                content = ("," if keys else "") + separator
                content += ("," + separator).join(encode(key) + ": " + encode(new[key]) for key in added)
                patches.append((last_end, last_end, content))
        elif isinstance(old, list) and isinstance(new, list):
            if len(old) != len(new):
                raise ValueError("A flexão não pode remover ou adicionar análises.")
            for index, (before, after) in enumerate(zip(old, new)):
                compare(before, after, route + (index,))
        elif old != new or type(old) is not type(new):
            start, end = spans[route]
            patches.append((start, end, encode(new)))

    compare(original, updated, ())
    for start, end, replacement in sorted(patches, reverse=True):
        text = text[:start] + replacement + text[end:]
    if json.loads(text.lstrip("\ufeff")) != updated:
        raise ValueError("Falha na verificação do JSON gerado.")
    return text


def write_dictionary(path: Path, data: Dict[str, Any], template_path: Optional[Path] = None) -> None:
    template = template_path or (path if path.exists() else None)
    if template:
        text = _patch_json(template.read_bytes().decode("utf-8"), data)
    else:
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    content = text.encode("utf-8")
    if path.exists() and path.read_bytes() == content:
        return
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = path.with_name(path.name + ".bak-" + stamp)
        shutil.copy2(path, backup)
        print(f"Backup: {backup}", file=sys.stderr)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
