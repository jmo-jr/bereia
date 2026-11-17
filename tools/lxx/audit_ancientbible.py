#!/usr/bin/env python3
"""Cruza pendências da LXX com registros individualmente legíveis de uma concordância."""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.update_interlinear_translit import transliterate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(text):
    return unicodedata.normalize('NFC', text.strip())


def folded(text):
    return exact(text).casefold()


def accentless(text):
    return ''.join(c for c in unicodedata.normalize('NFD', folded(text)) if not unicodedata.combining(c))


def greek_head(text):
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all('GREEK' in unicodedata.name(c, '') for c in letters)


def audit(source, output):
    pending_path = ROOT / 'tools/relatorios/lxx-beta-pendencias.csv'
    text = source.read_text(encoding='utf-8-sig')
    try:
        json.loads(text)
        whole_error = None
    except json.JSONDecodeError as error:
        whole_error = {'message': error.msg, 'line': error.lineno, 'column': error.colno, 'offset': error.pos}
    starts = list(re.finditer(r'\[\s*"\s*([GH]\d+[A-Za-z]*)"\s*,', text))
    decoder = json.JSONDecoder()
    readable, broken, nonstandard, prefixes = [], [], [], []
    for index, match in enumerate(starts):
        try:
            row, end = decoder.raw_decode(text, match.start())
            if index + 1 < len(starts) and end > starts[index + 1].start():
                raise ValueError('Registro invade o próximo identificador')
        except (json.JSONDecodeError, ValueError) as error:
            broken.append({'id': match.group(1), 'offset': match.start(), 'error': str(error)})
            # Ler apenas strings iniciais sintaticamente completas, sem reparar o registro.
            cursor, prefix = match.start() + 1, []
            limit = starts[index + 1].start() if index + 1 < len(starts) else len(text)
            try:
                for _ in range(4):
                    while cursor < limit and text[cursor].isspace():
                        cursor += 1
                    value, cursor = decoder.raw_decode(text, cursor)
                    if cursor > limit or not isinstance(value, str):
                        break
                    prefix.append(value)
                    while cursor < limit and text[cursor].isspace():
                        cursor += 1
                    if cursor >= limit or text[cursor] != ',':
                        break
                    cursor += 1
            except json.JSONDecodeError:
                pass
            if len(prefix) >= 2:
                prefixes.append(prefix)
            continue
        readable.append(row)
        if not (len(row) == 6 and all(isinstance(value, str) for value in row[:4])
                and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in row[4:])):
            nonstandard.append({'id': match.group(1), 'offset': match.start(), 'fields': len(row)})
    indexes = [defaultdict(list) for _ in range(3)]
    roman_index, id_index = defaultdict(list), defaultdict(list)
    seen = set()
    for row, valid in [(row, True) for row in readable] + [(row, False) for row in prefixes]:
        if len(row) < 2 or not isinstance(row[1], str) or not row[0].strip().startswith('G'):
            continue
        has_greek = greek_head(row[1])
        core = len(row) >= 4 and all(isinstance(value, str) for value in row[:4])
        roman = row[2] if core else row[1] if not has_greek else None
        gloss = row[3] if core else row[2] if not has_greek and len(row) >= 3 and isinstance(row[2], str) else None
        identity = (tuple(str(value) for value in row[:4]), valid)
        if identity in seen:
            continue
        seen.add(identity)
        entry = {'id': row[0], 'greek': row[1] if has_greek else None, 'transliteration': roman,
                 'gloss': gloss, 'complete_json_record': valid,
                 'head_original': row[1], 'fields_read_original': row}
        id_index[exact(row[0])].append(entry)
        if roman and not any('GREEK' in unicodedata.name(c, '') for c in roman):
            roman_index[accentless(roman)].append(entry)
        if has_greek:
            variants = list(dict.fromkeys([row[1], *[part.strip() for part in row[1].split(',')]]))
            for variant in variants:
                if not greek_head(variant):
                    continue
                for normalize, mapping in zip([exact, folded, accentless], indexes):
                    if entry not in mapping[normalize(variant)]:
                        mapping[normalize(variant)].append(entry)
    application = json.loads((ROOT / 'tools/relatorios/lxx-beta-aplicacao.json').read_text())
    coverage = json.loads((ROOT / application['input_files']['audit']).read_text())
    lexicon = {entry['line']: entry for entry in coverage['lexicon']}
    candidate_ids = defaultdict(set)
    candidate_roman = defaultdict(set)
    for row in coverage['records']:
        for line in row['candidate_lines']:
            entry = lexicon[line]
            candidate_ids[row['lemma']].add(entry['dStrong'].split()[0])
            candidate_roman[row['lemma']].add(entry['transliteration'])
    grouped = {}
    with pending_path.open(encoding='utf-8', newline='') as file:
        for row in csv.DictReader(file):
            item = grouped.setdefault(row['lema'], {'lemma': row['lema'], 'occurrences': 0, 'forms': [], 'references': []})
            item['occurrences'] += int(row['ocorrencias'])
            if row['forma'] not in item['forms']:
                item['forms'].append(row['forma'])
            for reference in row['referencias'].split('; '):
                if reference and reference not in item['references']:
                    item['references'].append(reference)
    summary = defaultdict(Counter)
    for lemma, row in grouped.items():
        row['status'], row['matches'] = 'not_found_in_readable_greek_entries', []
        for label, normalize, mapping in zip(['exact', 'case_or_sigma_only', 'without_diacritics'], [exact, folded, accentless], indexes):
            if normalize(lemma) in mapping:
                row['status'], row['matches'] = label, mapping[normalize(lemma)]
                if not any(normalize(entry['greek']) == normalize(lemma) for entry in row['matches']):
                    row['status'] += '_listed_variant'
                break
        row['transliteration_candidates'], row['identifier_candidates'] = [], []
        for roman in {transliterate(lemma), *candidate_roman[lemma]}:
            for entry in roman_index.get(accentless(roman), []):
                if entry not in row['transliteration_candidates']:
                    row['transliteration_candidates'].append(entry)
        for identifier in sorted(candidate_ids[lemma]):
            for entry in id_index.get(identifier, []):
                if entry not in row['identifier_candidates']:
                    row['identifier_candidates'].append(entry)
        summary[row['status']]['lemmas'] += 1
        summary[row['status']]['occurrences'] += row['occurrences']
    report = {'source': {'path': str(source.resolve()), 'sha256': digest(source), 'valid_json': whole_error is None,
                         'json_error': whole_error, 'detected_record_starts': len(starts),
                         'individually_readable_records': len(readable), 'broken_records': len(broken),
                         'nonstandard_readable_records': len(nonstandard),
                         'distinct_greek_heads': len(indexes[0])},
              'pending': {'file': str(pending_path.relative_to(ROOT)), 'sha256': digest(pending_path),
                          'lemmas': len(grouped), 'occurrences': sum(row['occurrences'] for row in grouped.values())},
              'method': 'Leitura individual delimitada por identificadores G/H. Lemas integralmente gregos nos campos iniciais legíveis; registros parciais explicitamente marcados. Contagens da fonte não são usadas. Candidatos por transliteração (projeto ou TBESG) e identificador completo da TBESG são separados da presença do lema grego. Sem reparo, fuzzy matching ou atribuição de Strong. Ausência não é conclusiva em uma fonte malformada.',
              'summary': dict(summary), 'records': sorted(grouped.values(), key=lambda row: -row['occurrences']),
              'broken_records': broken, 'nonstandard_records': nonstandard}
    additional = [row for row in grouped.values() if not row['matches']
                  and (row['transliteration_candidates'] or row['identifier_candidates'])]
    report['summary_additional_candidates'] = {
        'lemmas': len(additional), 'occurrences': sum(row['occurrences'] for row in additional),
        'note': 'Apenas candidatos por transliteração ou identificador TBESG; não confirmam presença do lema grego nem tradução adequada.'}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ['source', 'pending', 'summary']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'tools/relatorios/lxx-ancientbible-cobertura.json')
    args = parser.parse_args()
    audit(args.source, args.output)
