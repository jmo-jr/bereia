#!/usr/bin/env python3
"""Aplicação separada da auditoria, limitada ao manifesto aprovado de agudo/grave."""
import argparse
import hashlib
import json
from collections import defaultdict

from tools.audit.audit_tm import ROOT, digest, dump, nfc, read, write

LEXICON = 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json'
DECODER = json.JSONDecoder()


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def members(text, start=0):
    """Campos de um objeto JSON com posições, sem reserializar seus valores."""
    if text[start] != '{':
        raise ValueError('Objeto JSON esperado.')
    position = start + 1
    while True:
        while text[position].isspace():
            position += 1
        if text[position] == '}':
            return
        key, position = DECODER.raw_decode(text, position)
        if not isinstance(key, str):
            raise ValueError('Chave inválida.')
        while text[position].isspace():
            position += 1
        if text[position] != ':':
            raise ValueError('Separador inválido.')
        position += 1
        while text[position].isspace():
            position += 1
        value_start = position
        _, position = DECODER.raw_decode(text, position)
        yield key, value_start, position
        while text[position].isspace():
            position += 1
        if text[position] == ',':
            position += 1
        elif text[position] == '}':
            return
        else:
            raise ValueError('Fim de campo inválido.')


def plan_append(text, items):
    before = json.loads(text)
    if not isinstance(before, dict):
        raise ValueError('Léxico deve ser objeto.')
    known = {nfc(f['grego']) for g in before.values() for f in g['flexoes']}
    grouped, approved, identifiers = defaultdict(list), [], set()
    for item in items:
        if (item['estado'] != 'SUGERIR' or item.get('sinais') or
                item.get('aplicado') or len(item['candidatos']) != 1 or
                item.get('referencias_sem_parsing_alinhado')):
            raise ValueError('Item fora do escopo aprovado ou evidência incompleta.')
        if item['id'] in identifiers:
            raise ValueError('Item duplicado.')
        identifiers.add(item['id'])
        candidate = item['candidatos'][0]
        strong, index = candidate['strong'], candidate['flexao']
        if strong not in before or before[strong]['flexoes'][index] != candidate['campos_atuais']:
            raise ValueError(f'Candidato desatualizado: {strong}/{index}.')
        draft = item['minuta_inclusao']
        if not draft or draft['grego'] != item['forma_tm']:
            raise ValueError('Minuta ausente ou grafia divergente.')
        if list(draft) != list(candidate['campos_atuais']):
            raise ValueError('Campos ou ordem da minuta divergentes.')
        if nfc(draft['grego']) in known:
            raise ValueError(f'Forma já coberta literalmente/NFC: {draft["grego"]}.')
        known.add(nfc(draft['grego']))
        new_index = len(before[strong]['flexoes']) + len(grouped[strong])
        grouped[strong].append(draft)
        approved.append({'id': item['id'], 'strong': strong, 'flexao': new_index,
                         'campos': draft, 'referencias_tm': item['referencias_tm'],
                         'referencias_lxx': item['referencias_lxx_literal_nfc']})
    root_fields = {key: start for key, start, _ in members(text)}
    insertions = []
    for strong, additions in grouped.items():
        fields = {key: (start, end) for key, start, end in members(text, root_fields[strong])}
        start, end = fields['flexoes']
        if text[start] != '[' or text[end - 1] != ']' or not before[strong]['flexoes']:
            raise ValueError('Lista de flexões não reconhecida.')
        position = len(text[:end - 1].rstrip())
        if text[position:end] != '\n    ]':
            raise ValueError('Formatação da lista diferente do padrão; não reformatar automaticamente.')
        block = ',\n' + ',\n'.join(
            '\n'.join('      ' + line for line in json.dumps(f, ensure_ascii=False, indent=2).splitlines())
            for f in additions)
        insertions.append((position, block))
    after_text = text
    for position, block in sorted(insertions, reverse=True):
        after_text = after_text[:position] + block + after_text[position:]
    # Conferência estrutural independente do posicionamento textual.
    after = json.loads(after_text)
    if list(after) != list(before):
        raise ValueError('Ordem dos Strong alterada.')
    for strong, group in before.items():
        expected = {**group, 'flexoes': group['flexoes'] + grouped.get(strong, [])}
        if after[strong] != expected or list(after[strong]) != list(group):
            raise ValueError(f'Entrada anterior alterada: {strong}.')
    # Reversão em memória demonstra que só blocos novos foram inseridos.
    restored = after_text
    for position, block in sorted(insertions):
        if restored[position:position + len(block)] != block:
            raise ValueError('Inserção não reproduzível.')
        restored = restored[:position] + restored[position + len(block):]
    if restored != text:
        raise ValueError('Bytes anteriores alterados.')
    return after_text, approved


def selected(report, approval):
    if approval['estado'] != 'APROVADO' or approval['tipo'] != 'agudo_grave':
        raise ValueError('Manifesto não aprovado.')
    rows = [r for r in report['itens'] if r['estado'] == 'SUGERIR']
    if [r['id'] for r in rows] != approval['itens_ids'] or len(rows) != approval['quantidade']:
        raise ValueError('Lote diverge da aprovação.')
    return rows


def check_applied(text, approval):
    lexicon = json.loads(text)
    for item in approval['aplicacoes']:
        group = lexicon.get(item['strong'])
        if not group or len(group['flexoes']) <= item['flexao'] or group['flexoes'][item['flexao']] != item['campos']:
            raise ValueError(f'Aplicação diverge da aprovação: {item["strong"]}/{item["flexao"]}.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval', required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    approval_path = (ROOT / args.approval).resolve()
    approval = read(approval_path)
    source = ROOT / LEXICON
    text = source.read_text(encoding='utf-8')
    if args.check:
        if approval['estado'] != 'APROVADO':
            raise ValueError('Manifesto não aprovado.')
        check_applied(text, approval)
        print(f'{approval["quantidade"]} inclusões aprovadas conferidas.')
        return
    report_path = ROOT / approval['relatorio']
    if digest(report_path) != approval['relatorio_sha256']:
        raise ValueError('Relatório aprovado foi alterado.')
    report = read(report_path)
    rows = selected(report, approval)
    if sha(text) == approval['fonte_depois_sha256']:
        check_applied(text, approval)
        print('Lote já aplicado; nenhuma escrita.')
        return
    if sha(text) != approval['fonte_antes_sha256']:
        raise ValueError('Dicionário mudou desde a aprovação; revisar conflitos.')
    for path, expected in report['fontes_sha256'].items():
        if not (ROOT / path).exists() or digest(ROOT / path) != expected:
            raise ValueError(f'Fonte mudou desde a revisão: {path}.')
    result, applications = plan_append(text, rows)
    if sha(result) != approval['fonte_depois_sha256'] or applications != approval['aplicacoes']:
        raise ValueError('Plano difere da aprovação registrada.')
    if digest(source) != approval['fonte_antes_sha256']:
        raise ValueError('Fonte mudou durante a aplicação.')
    write(source, result)
    print(f'{len(applications)} flexões acrescentadas; registros e índices anteriores preservados.')


if __name__ == '__main__':
    main()
