#!/usr/bin/env python3
"""Inclui variantes gráficas com Strong e morfologia confirmados no parsing auxiliar."""
import argparse
import copy
import hashlib
import json
from collections import defaultdict

from tools.audit.apply_approved_accents import LEXICON, members
from tools.audit.audit_accents import collect_lxx, compare_codes
from tools.audit.audit_tm import ROOT, digest, nfc, read, write
from tools.update_interlinear_translit import transliterate


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def selected(report, source):
    known = {nfc(f['grego']) for group in source.values() for f in group['flexoes']}
    accepted, deferred = [], []
    for item in report['propostas']:
        candidates = item['candidatos']
        identities = {(c['strong'], c['forma'], c.get('abrev_morf'), c.get('morfologia')) for c in candidates}
        analyses = item['evidencias']['analises_observadas']
        if len(identities) != 1 or not analyses:
            deferred.append(item['forma_tm'])
            continue
        candidate = candidates[0]
        comparisons = {compare_codes(candidate['abrev_morf'], evidence['parsing']) for evidence in analyses}
        if ({evidence['strong'] for evidence in analyses} != {candidate['strong']} or
                not comparisons <= {'identico', 'compativel', 'compativel_nom_acus_neutro'}):
            deferred.append(item['forma_tm'])
            continue
        strong, index = candidate['strong'], candidate['flexao']
        current = source.get(strong, {}).get('flexoes', [])
        if index >= len(current) or current[index].get('grego') != candidate['forma']:
            raise ValueError(f'Candidato desatualizado: {strong}/{index}.')
        form = item['forma_tm']
        if nfc(form) in known:
            raise ValueError(f'Forma já coberta literalmente/NFC: {form}.')
        known.add(nfc(form))
        accepted.append({'forma_tm': form, 'strong': strong, 'flexao_origem': index,
                         'referencias_tm': item['referencias'], 'campos_origem': current[index]})
    return accepted, deferred


def append(text, rows, lxx):
    before = json.loads(text)
    grouped = defaultdict(list)
    applications = []
    for row in rows:
        draft = copy.deepcopy(row['campos_origem'])
        draft.update(grego=row['forma_tm'], transliteracao=transliterate(row['forma_tm']),
                     ocorrencias=str(len(row['referencias_tm'])), lxx=[],
                     ocorrencias_lxx=len(lxx[nfc(row['forma_tm'])]))
        strong = row['strong']
        new_index = len(before[strong]['flexoes']) + len(grouped[strong])
        grouped[strong].append(draft)
        applications.append({k: v for k, v in row.items() if k != 'campos_origem'} |
                            {'flexao_nova': new_index, 'campos': draft})
    roots = {key: start for key, start, _ in members(text)}
    insertions = []
    for strong, additions in grouped.items():
        fields = {key: (start, end) for key, start, end in members(text, roots[strong])}
        start, end = fields['flexoes']; position = len(text[:end - 1].rstrip())
        if text[start] != '[' or text[end - 1] != ']' or text[position:end] != '\n    ]':
            raise ValueError(f'Formatação da lista diferente do padrão: {strong}.')
        block = ',\n' + ',\n'.join('\n'.join('      ' + line for line in
            json.dumps(entry, ensure_ascii=False, indent=2).splitlines()) for entry in additions)
        insertions.append((position, block))
    result = text
    for position, block in sorted(insertions, reverse=True): result = result[:position] + block + result[position:]
    after = json.loads(result)
    if list(after) != list(before): raise ValueError('Ordem dos Strong alterada.')
    for strong, group in before.items():
        if after[strong] != {**group, 'flexoes': group['flexoes'] + grouped.get(strong, [])}:
            raise ValueError(f'Entrada anterior alterada: {strong}.')
    return result, applications


def plan(report_path):
    text = (ROOT / LEXICON).read_text(encoding='utf-8')
    report = read(report_path)
    if report['fontes_sha256'].get(LEXICON) != sha(text):
        raise ValueError('Triagem foi gerada para outro estado do léxico.')
    rows, deferred = selected(report, json.loads(text))
    lxx, _ = collect_lxx([row['forma_tm'] for row in rows])
    after, applications = append(text, rows, lxx)
    return {'schema_version': 1,
            'criterio': 'Candidato único, Strong auxiliar unânime e código morfológico compatível; somente grafias próprias são acrescentadas.',
            'relatorio_origem': str(report_path.relative_to(ROOT)), 'relatorio_origem_sha256': digest(report_path),
            'fonte': LEXICON, 'fonte_antes_sha256': sha(text), 'fonte_depois_sha256': sha(after),
            'quantidade': len(applications), 'pendentes': deferred, 'aplicacoes': applications}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True); parser.add_argument('--output', required=True); parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    report_path, output_path = (ROOT / args.report).resolve(), (ROOT / args.output).resolve()
    if not report_path.is_relative_to((ROOT / 'reports/audit').resolve()) or not output_path.is_relative_to((ROOT / 'reports/audit').resolve()):
        parser.error('relatório e saída devem ficar em reports/audit')
    result = plan(report_path)
    if args.apply:
        text = (ROOT / LEXICON).read_text(encoding='utf-8')
        if sha(text) != result['fonte_antes_sha256']: raise ValueError('Léxico mudou durante o planejamento.')
        rows, _ = selected(read(report_path), json.loads(text)); lxx, _ = collect_lxx([r['forma_tm'] for r in rows])
        updated, applications = append(text, rows, lxx)
        if sha(updated) != result['fonte_depois_sha256'] or applications != result['aplicacoes']: raise ValueError('Plano não reproduzível.')
        write(ROOT / LEXICON, updated)
    write(output_path, json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f"{result['quantidade']} flexões com evidência aplicável; {len(result['pendentes'])} pendências preservadas.")


if __name__ == '__main__': main()
