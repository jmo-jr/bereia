#!/usr/bin/env python3
"""Inclui variantes finais agudo/grave de candidato único autorizadas pelo usuário.

Este aplicador não muda a consulta. Cada grafia do TM recebe uma flexão própria,
preservando a forma do candidato e todos os demais registros. Candidatos que
divergem em outros sinais permanecem apenas como evidência secundária: eles não
são escolhidos nem fundidos com a variante final agudo/grave.
"""
import argparse
import copy
import hashlib
import json
from collections import defaultdict

from tools.audit.apply_approved_accents import DECODER, LEXICON, members
from tools.audit.audit_tm import ROOT, digest, nfc, read, write
from tools.audit.triage_tm import candidate_difference
from tools.update_interlinear_translit import transliterate


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def selected(report, source):
    """Constrói minutas somente quando há um único alvo agudo/grave final."""
    known = {nfc(f['grego']) for group in source.values() for f in group['flexoes']}
    rows, skipped = [], []
    for item in report['itens']:
        candidates = item.get('candidatos', [])
        allowed = (len(candidates) == 1 and
                   candidate_difference(item['forma_tm'], candidates[0]['forma']) ==
                   'agudo_grave_mesma_posicao')
        if not allowed:
            skipped.append({'forma_tm': item['forma_tm'], 'motivo': 'sem_candidato_unico_agudo_grave',
                            'candidatos': [{'strong': c.get('strong'), 'forma': c.get('forma')}
                                           for c in candidates],
                            'outros_candidatos': item.get('outros_candidatos', [])})
            continue
        candidate = candidates[0]
        strong, index = candidate['strong'], candidate['flexao']
        current = source.get(strong, {}).get('flexoes', [])
        if index >= len(current) or current[index] != candidate['campos_atuais']:
            raise ValueError(f'Candidato desatualizado: {strong}/{index}.')
        form = item['forma_tm']
        if nfc(form) in known:
            raise ValueError(f'Forma já coberta literalmente/NFC: {form}.')
        known.add(nfc(form))
        draft = copy.deepcopy(current[index])
        draft.update(grego=form, transliteracao=transliterate(form),
                     ocorrencias=str(item['ocorrencias_nt']), lxx=[],
                     ocorrencias_lxx=len(item['referencias_lxx_literal_nfc']))
        rows.append({'forma_tm': form, 'strong': strong, 'flexao_origem': index,
                     'referencias_tm': item['referencias_tm'],
                     'motivo_original': item['grupo'], 'campos': draft})
    return rows, skipped


def append(text, rows):
    before = json.loads(text)
    grouped = defaultdict(list)
    applications = []
    for row in rows:
        strong = row['strong']
        if strong not in before:
            raise ValueError(f'Strong ausente: {strong}.')
        new_index = len(before[strong]['flexoes']) + len(grouped[strong])
        grouped[strong].append(row['campos'])
        applications.append({**row, 'flexao_nova': new_index})
    roots = {key: start for key, start, _ in members(text)}
    insertions = []
    for strong, additions in grouped.items():
        fields = {key: (start, end) for key, start, end in members(text, roots[strong])}
        start, end = fields['flexoes']
        position = len(text[:end - 1].rstrip())
        if text[start] != '[' or text[end - 1] != ']' or text[position:end] != '\n    ]':
            raise ValueError(f'Formatação da lista diferente do padrão: {strong}.')
        block = ',\n' + ',\n'.join('\n'.join('      ' + line for line in
            json.dumps(entry, ensure_ascii=False, indent=2).splitlines()) for entry in additions)
        insertions.append((position, block))
    result = text
    for position, block in sorted(insertions, reverse=True):
        result = result[:position] + block + result[position:]
    after = json.loads(result)
    if list(after) != list(before):
        raise ValueError('Ordem dos Strong alterada.')
    for strong, group in before.items():
        expected = {**group, 'flexoes': group['flexoes'] + grouped.get(strong, [])}
        if after[strong] != expected or list(after[strong]) != list(group):
            raise ValueError(f'Entrada anterior alterada: {strong}.')
    return result, applications


def plan(report_path):
    source_path = ROOT / LEXICON
    source_text = source_path.read_text(encoding='utf-8')
    report = read(report_path)
    rows, skipped = selected(report, json.loads(source_text))
    after, applications = append(source_text, rows)
    return {'schema_version': 1,
            'autorizacao': 'Usuário autorizou incluir grafias com leve suspeita de diferença apenas diacrítica.',
            'criterio': 'Somente agudo/grave final e candidato único. Candidatos com outros sinais não são selecionados. Não altera a consulta.',
            'relatorio_origem': str(report_path.relative_to(ROOT)),
            'relatorio_origem_sha256': digest(report_path),
            'fonte': LEXICON, 'fonte_antes_sha256': sha(source_text),
            'fonte_depois_sha256': sha(after), 'quantidade': len(applications),
            'aplicacoes': applications, 'excluidos': skipped}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    report_path, output_path = (ROOT / args.report).resolve(), (ROOT / args.output).resolve()
    if not report_path.is_relative_to((ROOT / 'reports/audit').resolve()):
        parser.error('--report deve estar em reports/audit')
    if not output_path.is_relative_to((ROOT / 'reports/audit').resolve()):
        parser.error('--output deve estar em reports/audit')
    result = plan(report_path)
    if args.apply:
        source_path = ROOT / LEXICON
        source_text = source_path.read_text(encoding='utf-8')
        if sha(source_text) != result['fonte_antes_sha256']:
            raise ValueError('Léxico mudou durante o planejamento.')
        report = read(report_path)
        rows, _ = selected(report, json.loads(source_text))
        updated, applications = append(source_text, rows)
        if sha(updated) != result['fonte_depois_sha256'] or applications != result['aplicacoes']:
            raise ValueError('Plano não reproduzível.')
        write(source_path, updated)
    write(output_path, json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f"{result['quantidade']} flexões planejadas; {len(result['excluidos'])} formas excluídas por ambiguidade.")


if __name__ == '__main__':
    main()
