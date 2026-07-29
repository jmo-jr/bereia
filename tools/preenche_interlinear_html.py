#!/usr/bin/env python3
"""Preenche traduções e morfologia em arquivos HTML interlineares.

Uso:
    python3 tools/preenche_interlinear_html.py src/interlinear/at/habacuque

Por padrão, processa arquivos .html/.htm diretamente dentro da pasta informada.
Use --recursive para incluir subpastas.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Optional


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DEFAULT_DICT_PATH = PROJECT_ROOT / "src/_data/nt_greek-pt_dict.json"

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

STRONG_RE = re.compile(r"G?\s*-?(\d+)(?:\.\d+)?", re.IGNORECASE)


class Node:
    parent: Optional["Element"] = None

    def render(self) -> str:
        raise NotImplementedError

    def text_content(self) -> str:
        return ""


class Text(Node):
    def __init__(self, data: str) -> None:
        self.data = data

    def render(self) -> str:
        return html.escape(self.data, quote=False)

    def text_content(self) -> str:
        return self.data


class Entity(Node):
    def __init__(self, entity: str) -> None:
        self.entity = entity

    def render(self) -> str:
        return f"&{self.entity};"

    def text_content(self) -> str:
        if self.entity == "nbsp":
            return "\xa0"
        return html.unescape(f"&{self.entity};")


class CharRef(Node):
    def __init__(self, charref: str) -> None:
        self.charref = charref

    def render(self) -> str:
        return f"&#{self.charref};"

    def text_content(self) -> str:
        return html.unescape(f"&#{self.charref};")


class Raw(Node):
    def __init__(self, data: str) -> None:
        self.data = data

    def render(self) -> str:
        return self.data


class Element(Node):
    def __init__(
        self,
        tag: str,
        attrs: Optional[list[tuple[str, Optional[str]]]] = None,
        self_closing: bool = False,
    ) -> None:
        self.tag = tag
        self.attrs = attrs or []
        self.children: list[Node] = []
        self.self_closing = self_closing

    def append(self, node: Node) -> None:
        node.parent = self
        self.children.append(node)

    def get_attr(self, name: str) -> Optional[str]:
        for attr_name, value in self.attrs:
            if attr_name.lower() == name.lower():
                return value
        return None

    def set_attr(self, name: str, value: str) -> None:
        for index, (attr_name, _) in enumerate(self.attrs):
            if attr_name.lower() == name.lower():
                self.attrs[index] = (attr_name, value)
                return
        self.attrs.append((name, value))

    def has_class(self, class_name: str) -> bool:
        classes = self.get_attr("class")
        return bool(classes and class_name in classes.split())

    def render(self) -> str:
        if self.tag == "__root__":
            return "".join(child.render() for child in self.children)

        attrs = "".join(
            f" {name}" if value is None else f' {name}="{html.escape(value, quote=True)}"'
            for name, value in self.attrs
        )
        if self.self_closing:
            return f"<{self.tag}{attrs} />"
        if self.tag.lower() in VOID_TAGS:
            return f"<{self.tag}{attrs}>"
        return f"<{self.tag}{attrs}>" + "".join(child.render() for child in self.children) + f"</{self.tag}>"

    def text_content(self) -> str:
        return "".join(child.text_content() for child in self.children)


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root = Element("__root__")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        node = Element(tag, attrs)
        self.stack[-1].append(node)
        if tag.lower() not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        self.stack[-1].append(Element(tag, attrs, self_closing=True))

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag.lower() == tag_lower:
                del self.stack[index:]
                return
        self.stack[-1].append(Raw(f"</{tag}>"))

    def handle_data(self, data: str) -> None:
        self.stack[-1].append(Text(data))

    def handle_entityref(self, name: str) -> None:
        self.stack[-1].append(Entity(name))

    def handle_charref(self, name: str) -> None:
        self.stack[-1].append(CharRef(name))

    def handle_comment(self, data: str) -> None:
        self.stack[-1].append(Raw(f"<!--{data}-->"))

    def handle_decl(self, decl: str) -> None:
        self.stack[-1].append(Raw(f"<!{decl}>"))

    def unknown_decl(self, data: str) -> None:
        self.stack[-1].append(Raw(f"<![{data}]>"))

    def handle_pi(self, data: str) -> None:
        self.stack[-1].append(Raw(f"<?{data}>"))


def parse_html(source: str) -> Element:
    parser = TreeBuilder()
    parser.feed(source)
    parser.close()
    return parser.root


def iter_elements(node: Node, tag: Optional[str] = None) -> Iterable[Element]:
    if isinstance(node, Element):
        if tag is None or node.tag.lower() == tag.lower():
            yield node
        for child in node.children:
            yield from iter_elements(child, tag)


def find_first_descendant(node: Element, tag: str, class_name: Optional[str] = None) -> Optional[Element]:
    for child in iter_elements(node, tag):
        if child is node:
            continue
        if class_name is None or child.has_class(class_name):
            return child
    return None


def direct_child_index(parent: Element, child: Node) -> Optional[int]:
    for index, item in enumerate(parent.children):
        if item is child:
            return index
    return None


def normalize_greek(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.strip().lower())
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return without_marks.replace("ς", "σ")


def normalize_strongs(value: str) -> Optional[str]:
    match = STRONG_RE.search(value.strip())
    return match.group(1) if match else None


def text_with_nbsp(value: str) -> list[Node]:
    nodes: list[Node] = []
    for index, chunk in enumerate(re.split(r"([ \xa0]+)", value)):
        if not chunk:
            continue
        if chunk.isspace() or "\xa0" in chunk:
            for _ in chunk:
                nodes.append(Entity("nbsp"))
        else:
            nodes.append(Text(chunk))
        if index == 0 and chunk == "":
            continue
    return nodes


def make_refs(entries: list[dict]) -> Element:
    title = " | ".join(str(entry.get("morfologia", "")).strip() for entry in entries if entry.get("morfologia"))
    label = " ".join(str(entry.get("abrev_morf", "")).strip() for entry in entries if entry.get("abrev_morf"))
    small = Element("small", [("class", "refs tooltip tooltipstered"), ("title", title)])
    for node in text_with_nbsp(label):
        small.append(node)
    return small


def load_dictionary(path: Path) -> dict[str, list[dict]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    index: dict[str, list[dict]] = {}
    for key, entry in data.items():
        if not isinstance(entry, dict):
            continue
        code = normalize_strongs(str(entry.get("strongs", "")))
        if not code:
            continue
        indexed_entry = dict(entry)
        indexed_entry.setdefault("grego", key)
        index.setdefault(code, []).append(indexed_entry)
    return index


def split_greek_words(td: Element) -> list[str]:
    greek = find_first_descendant(td, "span", "greek")
    if greek is None:
        return []
    return [word for word in re.split(r"\s+", greek.text_content().replace("\xa0", " ").strip()) if word]


def choose_entry(candidates: list[dict], greek_words: list[str], position: int) -> dict:
    normalized_candidates = [
        (normalize_greek(str(entry.get("grego", ""))), entry)
        for entry in candidates
    ]

    if position < len(greek_words):
        wanted = normalize_greek(greek_words[position])
        for normalized_greek, entry in normalized_candidates:
            if normalized_greek == wanted:
                return entry

    normalized_words = {normalize_greek(word) for word in greek_words}
    for normalized_greek, entry in normalized_candidates:
        if normalized_greek in normalized_words:
            return entry

    return candidates[0]


def extract_strongs_items(strongs_span: Element) -> list[tuple[str, Optional[Element]]]:
    items: list[tuple[str, Optional[Element]]] = []
    anchors = [child for child in iter_elements(strongs_span, "a") if child is not strongs_span]
    if anchors:
        for anchor in anchors:
            code = normalize_strongs(anchor.text_content())
            if code:
                items.append((code, anchor))
        return items

    text = strongs_span.text_content().strip()
    if text == "*":
        return []
    return [(match.group(1), None) for match in STRONG_RE.finditer(text)]


def replace_eng_contents(eng_span: Element, entries: list[dict]) -> None:
    eng_span.children = []
    for index, entry in enumerate(entries):
        if index:
            eng_span.append(Entity("nbsp"))
        for node in text_with_nbsp(str(entry.get("pt", "")).strip()):
            eng_span.append(node)


def update_strongs_titles(items: list[tuple[str, Optional[Element], dict]]) -> None:
    for _, anchor, entry in items:
        if anchor is None:
            continue
        anchor.set_attr("title", str(entry.get("verbete", "")).strip())


def remove_existing_refs(td: Element, eng_span: Element) -> int:
    eng_index = direct_child_index(td, eng_span)
    if eng_index is None:
        return 0

    removed = 0
    index = eng_index + 1
    while index < len(td.children):
        child = td.children[index]
        if isinstance(child, Text) and not child.text_content().strip():
            index += 1
            continue
        if isinstance(child, Element) and child.tag.lower() == "small" and child.has_class("refs"):
            del td.children[index]
            removed += 1
            continue
        break
    return removed


def insert_refs_after_eng(td: Element, eng_span: Element, entries: list[dict]) -> bool:
    eng_index = direct_child_index(td, eng_span)
    if eng_index is None:
        return False
    remove_existing_refs(td, eng_span)
    eng_index = direct_child_index(td, eng_span)
    if eng_index is None:
        return False
    refs = make_refs(entries)
    refs.parent = td
    td.children.insert(eng_index + 1, refs)
    return True


def process_tree(root: Element, dictionary: dict[str, list[dict]]) -> tuple[int, int]:
    updated = 0
    missing = 0

    for td in iter_elements(root, "td"):
        strongs_span = find_first_descendant(td, "span", "strongs")
        eng_span = find_first_descendant(td, "span", "eng")
        if strongs_span is None or eng_span is None:
            continue

        strongs_items = extract_strongs_items(strongs_span)
        if not strongs_items:
            continue

        greek_words = split_greek_words(td)
        entries: list[dict] = []
        resolved_items: list[tuple[str, Optional[Element], dict]] = []
        for position, (code, anchor) in enumerate(strongs_items):
            candidates = dictionary.get(code)
            if not candidates:
                missing += 1
                continue
            entry = choose_entry(candidates, greek_words, position)
            entries.append(entry)
            resolved_items.append((code, anchor, entry))

        if not entries:
            continue

        update_strongs_titles(resolved_items)
        replace_eng_contents(eng_span, entries)
        insert_refs_after_eng(td, eng_span, entries)
        updated += 1

    return updated, missing


def iter_html_files(folder: Path, recursive: bool) -> Iterable[Path]:
    pattern = "**/*" if recursive else "*"
    for path in sorted(folder.glob(pattern)):
        if path.is_file() and path.suffix.lower() in {".html", ".htm"}:
            yield path


def process_file(path: Path, dictionary: dict[str, list[dict]], dry_run: bool) -> tuple[int, int, bool]:
    original = path.read_text(encoding="utf-8")
    root = parse_html(original)
    updated, missing = process_tree(root, dictionary)
    rendered = root.render()
    changed = rendered != original
    if changed and not dry_run:
        path.write_text(rendered, encoding="utf-8")
    return updated, missing, changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Pasta com arquivos HTML a processar.")
    parser.add_argument(
        "--dict",
        dest="dict_path",
        type=Path,
        default=DEFAULT_DICT_PATH,
        help=f"Arquivo de dicionário JSON. Padrão: {DEFAULT_DICT_PATH}",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Processa arquivos HTML também nas subpastas.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra estatísticas sem gravar alterações.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    folder = args.folder.resolve()
    dict_path = args.dict_path.resolve()

    if not folder.is_dir():
        print(f"Erro: pasta não encontrada: {folder}", file=sys.stderr)
        return 2
    if not dict_path.is_file():
        print(f"Erro: dicionário não encontrado: {dict_path}", file=sys.stderr)
        return 2

    dictionary = load_dictionary(dict_path)
    files = list(iter_html_files(folder, args.recursive))
    if not files:
        print("Nenhum arquivo .html/.htm encontrado.")
        return 0

    total_updated = 0
    total_missing = 0
    changed_files = 0

    for path in files:
        updated, missing, changed = process_file(path, dictionary, args.dry_run)
        total_updated += updated
        total_missing += missing
        if changed:
            changed_files += 1
        print(f"{path}: {updated} td(s) atualizados, {missing} código(s) sem verbete")

    action = "seriam alterados" if args.dry_run else "alterados"
    print(
        f"Concluído: {changed_files}/{len(files)} arquivo(s) {action}; "
        f"{total_updated} td(s) atualizados; {total_missing} código(s) sem verbete."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
