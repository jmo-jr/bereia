"""Adaptador de build: reutiliza o conversor existente sem gravar fontes Liquid."""
import importlib.util
import json
import re
import html
from pathlib import Path
import sys

converter_file = Path(__file__).resolve().parents[1] / 'biblech' / 'gera_capitulos_html.py'
spec = importlib.util.spec_from_file_location('bereia_chapter_converter', converter_file)
converter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = converter
spec.loader.exec_module(converter)
result = []
for chapter in json.load(sys.stdin):
    source = Path(chapter['filename']).read_text(encoding='utf-8')
    parsed = converter.parse_source(source, chapter['chapter'])
    if set(parsed) != {chapter['chapter']}:
        raise ValueError(f"Capítulos não esperados em {chapter['filename']}")
    pericopes = []
    warnings = []
    for pericope in parsed[chapter['chapter']]:
        paragraphs = []
        for paragraph in pericope.paragraphs:
            verses = []
            for verse in paragraph:
                label = f"{chapter['book']} {chapter['chapter']}:{verse.number}"
                text = re.sub(r'(?<!<)/rl>', '</rl>', verse.text, flags=re.IGNORECASE)
                if text != verse.text:
                    warnings.append({'reference': label, 'reason': 'Fechamento /rl> tratado como </rl> no HTML; TXT preservado.'})
                try:
                    text = converter.convert_redletter(text, label)
                    text = converter.convert_reference(text, label)
                    text = converter.convert_entity_markers(text, label)
                except ValueError as error:
                    warnings.append({'reference': label, 'reason': str(error) + ' Conteúdo exibido literalmente para preservar a fonte.'})
                    text = html.escape(verse.text)
                verses.append({'number': verse.number, 'html': text})
            paragraphs.append(verses)
        pericopes.append({'title': pericope.title, 'concordance': pericope.concordance, 'paragraphs': paragraphs})
    result.append({**chapter, 'pericopes': pericopes, 'warnings': warnings})
json.dump(result, sys.stdout, ensure_ascii=False)
