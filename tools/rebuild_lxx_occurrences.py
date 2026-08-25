#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import sys
import unicodedata
from pathlib import Path
from collections import defaultdict
from html import unescape

ROOT = Path(__file__).resolve().parent.parent
LXX_DIR = ROOT / "src" / "interlinear" / "at"
DEFAULT_INPUT = ROOT / "tools" / "nt_greek-pt_dict.json"
DEFAULT_OUTPUT = ROOT / "tools" / "dict_flex_nt-lxx_greek-pt.json"

TABLEFLOAT_RE = re.compile(r'<table class="tablefloat">(.*?)</table>', re.S | re.I)
SPAN_RE = re.compile(r'<span class="([^"]+)">(.*?)</span>', re.S | re.I)
TAG_RE = re.compile(r'<[^>]+>')
LEADING_PUNCT_RE = re.compile(r'^[\s"“”‘’«»\(\[\{.,;:!?·—–-]+', re.UNICODE)
TRAILING_PUNCT_RE = re.compile(r'[\s"“”‘’«»\)\]\}.,;:!?·—–-]+$', re.UNICODE)

BOOK_MAP = {
    "1_cronicas": "1Cr",
    "2_cronicas": "2Cr",
    "1_esdras": "1Esd",
    "1_macabeus": "1Mc",
    "2_esdras": "2Esd",
    "2_macabeus": "2Mc",
    "amos": "Am",
    "baruc": "Bar",
    "cantico": "Ct",
    "daniel": "Dn",
    "deuteronomio": "Dt",
    "eclesiastes": "Ec",
    "efesios": "Ef",
    "esdras": "Ed",
    "ester": "Est",
    "exodo": "Ex",
    "ezequiel": "Ez",
    "genesis": "Gn",
    "habacuque": "Hc",
    "isaias": "Is",
    "jeremias": "Jr",
    "jo": "Jó",
    "joel": "Jl",
    "jonas": "Jn",
    "josue": "Js",
    "juizes": "Jz",
    "lamentacoes": "Lm",
    "levitico": "Lv",
    "malaquias": "Ml",
    "miqueias": "Mq",
    "naum": "Na",
    "neemias": "Ne",
    "numeros": "Nm",
    "obadias": "Ob",
    "oseias": "Os",
    "proverbios": "Pv",
    "1_reis": "1Rs",
    "2_reis": "2Rs",
    "1_samuel": "1Sm",
    "2_samuel": "2Sm",
    "salmos": "Sl",
    "sabedoria": "Sab",
    "siracida": "Sir",
    "sofonias": "Sf",
    "zacarias": "Zc",
}


def clean_html_text(value: str) -> str:
    value = unescape(value)
    value = TAG_RE.sub('', value)
    value = value.replace('\xa0', ' ')
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


def strip_edge_punctuation(value: str) -> str:
    value = LEADING_PUNCT_RE.sub('', value)
    value = TRAILING_PUNCT_RE.sub('', value)
    return value.strip()


def normalize_greek_form(value: str) -> str:
    value = clean_html_text(value)
    value = strip_edge_punctuation(value)
    return value


def normalize_for_match(value: str) -> str:
    value = normalize_greek_form(value)
    value = unicodedata.normalize('NFD', value)
    value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')
    value = unicodedata.normalize('NFC', value)
    return value


def split_greek_block(value: str):
    value = normalize_greek_form(value)
    if not value:
        return []
    parts = [p for p in value.split() if p]
    return parts if parts else []


def book_from_path(path: Path) -> str:
    slug = path.parent.name
    return BOOK_MAP.get(slug, slug.replace('_', ' '))


def chapter_from_path(path: Path) -> str:
    return path.stem


def first_reference_in_block(block_html: str):
    refs = []
    for cls, inner in SPAN_RE.findall(block_html):
        if cls.lower() in {"reftop", "refmain", "refbot"}:
            text = clean_html_text(inner)
            if text:
                refs.append(text)
    for ref in refs:
        m = re.match(r'^(\d+):(\d+)$', ref)
        if m:
            return m.group(1), m.group(2)
    return None


def greek_forms_in_block(block_html: str):
    forms = []
    for cls, inner in SPAN_RE.findall(block_html):
        if cls.lower() == 'greek':
            for item in split_greek_block(inner):
                forms.append(item)
    return forms


def build_lxx_index():
    refs_by_form = defaultdict(list)
    refs_by_normalized = defaultdict(list)
    files = sorted(LXX_DIR.glob('*/*.html'))

    for html_file in files:
        book = book_from_path(html_file)
        chapter = chapter_from_path(html_file)
        current_verse = None
        html = html_file.read_text(encoding='utf-8', errors='ignore')
        blocks = TABLEFLOAT_RE.findall(html)

        for block in blocks:
            ref = first_reference_in_block(block)
            if ref:
                _chapter, verse = ref
                current_verse = verse
            if not current_verse:
                continue

            forms = greek_forms_in_block(block)
            if not forms:
                continue

            verse_ref = f"{book} {chapter}:{current_verse}"
            for form in forms:
                if not refs_by_form[form] or refs_by_form[form][-1] != verse_ref:
                    refs_by_form[form].append(verse_ref)

                normalized = normalize_for_match(form)
                if normalized and (not refs_by_normalized[normalized] or refs_by_normalized[normalized][-1] != verse_ref):
                    refs_by_normalized[normalized].append(verse_ref)

    return refs_by_form, refs_by_normalized


def load_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def enrich_dictionary(data, refs_by_form, refs_by_normalized, lxx_key='lxx'):
    updated = 0
    zeroed = 0
    fallback_used = 0

    for term, entry in data.items():
        refs = refs_by_form.get(term, [])
        if not refs:
            normalized = normalize_for_match(term)
            refs = refs_by_normalized.get(normalized, [])
            if refs:
                fallback_used += 1

        entry[lxx_key] = refs
        entry['ocorrencias_lxx'] = len(refs)
        if refs:
            updated += 1
        else:
            zeroed += 1

    return updated, zeroed, fallback_used


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    if not input_path.exists():
        print(f"Arquivo de entrada não encontrado: {input_path}")
        sys.exit(1)

    if not LXX_DIR.exists():
        print(f"Pasta da LXX não encontrada: {LXX_DIR}")
        sys.exit(1)

    data = load_json(input_path)
    if not isinstance(data, dict):
        print("O JSON de entrada precisa ser um objeto/dicionário na raiz.")
        sys.exit(1)

    refs_by_form, refs_by_normalized = build_lxx_index()
    updated, zeroed, fallback_used = enrich_dictionary(data, refs_by_form, refs_by_normalized, lxx_key='lxx')
    save_json(output_path, data)

    print(f"Entrada : {input_path}")
    print(f"Saída   : {output_path}")
    print(f"Termos com ocorrências na LXX : {updated}")
    print(f"Termos zerados / ausentes      : {zeroed}")
    print(f"Fallback normalizado usado     : {fallback_used}")
    print(f"Total de formas indexadas      : {len(refs_by_form)}")
    print(f"Total de chaves normalizadas   : {len(refs_by_normalized)}")


if __name__ == '__main__':
    main()
