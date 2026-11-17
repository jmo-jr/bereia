#!/usr/bin/env python3
"""Recupera exclusivamente João 21, conferindo CCAT com o CSV com parsing.

Por padrão apenas valida; --apply preenche o capítulo se estiver vazio.
Não altera os demais capítulos nem reconstrói diacríticos.
"""
import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'tools/tmnt/no-variants/JOH.csv'
PARSING = ROOT / 'tools/tmnt/with-parsing/JOH.csv'
TARGET = ROOT / 'src/interlinear/nt/JO.json'


def normalized(word):
    return ''.join(c for c in unicodedata.normalize('NFD', word.lower())
                   if unicodedata.category(c).startswith('L')).replace('ς', 'σ')


def chapter_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if int(r['chapter']) == 21]
    assert [int(r['verse']) for r in rows] == list(range(1, 26)), path
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    verses = []
    for source, parsed in zip(chapter_rows(SOURCE), chapter_rows(PARSING)):
        words = [w.strip('¶,.;:··;!?()[]«»“”"') for w in source['text'].split()]
        assert all(words), source
        reference = re.findall(r'(\S+)\s+\d+\s+\{[^}]+\}', parsed['text'])
        assert [normalized(w) for w in words] == [normalized(w) for w in reference], source
        verses.append({'verse': int(source['verse']), 'tokens': [{'lemma': w} for w in words]})

    original = TARGET.read_text(encoding='utf-8')
    book = json.loads(original)
    chapter = next(c for c in book if c['chapter'] == 21)
    if chapter['pericopes']:
        existing = [v for p in chapter['pericopes'] for v in p['verses']]
        assert existing == verses, 'João 21 já contém conteúdo diferente; revisão manual necessária.'
        print('João 21 já corresponde à fonte: 25 versículos, 552 tokens.')
        return

    ids = [int(p['id'][1:]) for c in book for p in c['pericopes']]
    recovered = {'chapter': 21, 'pericopes': [{
        'id': f'P{max(ids) + 1:03d}', 'title': '',
        'start_verse': 1, 'end_verse': 25, 'verses': verses,
    }]}
    # Substituição localizada: preserva todos os bytes fora do capítulo vazio.
    old = json.dumps(chapter, ensure_ascii=False, indent=2)
    new = json.dumps(recovered, ensure_ascii=False, indent=2)
    indent = lambda text: '\n'.join('  ' + line for line in text.splitlines())
    assert original.count(indent(old)) == 1, 'Formatação inesperada; nenhuma alteração aplicada.'
    result = original.replace(indent(old), indent(new), 1)
    expected = json.loads(original)
    expected[expected.index(chapter)] = recovered
    assert json.loads(result) == expected
    if args.apply:
        TARGET.write_text(result, encoding='utf-8')
    print(f"João 21: 25 versículos, {sum(len(v['tokens']) for v in verses)} tokens; "
          + ('aplicado.' if args.apply else 'validado; use --apply para preencher.'))


if __name__ == '__main__':
    main()
