#!/usr/bin/env python3
"""Aplicação editorial separada: somente campos técnicos do lote prioritário.

python3 -B -m tools.audit.apply_morphology_priorities --apply
python3 -B -m tools.audit.apply_morphology_priorities --check
"""
import argparse
import hashlib
import json
from pathlib import Path

from tools.audit.apply_approved_accents import members
from tools.audit.audit_tm import ROOT

MANIFEST = 'tools/audit/approvals/morfologia-prioritarios.json'
OUTPUT = 'reports/audit/morfologia-aplicacao'
TECHNICAL = {'abrev_morf', 'morfologia'}
DECODER = json.JSONDecoder()


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def array_members(text, start):
    if text[start] != '[': raise ValueError('Lista esperada.')
    position = start + 1
    while True:
        while text[position].isspace(): position += 1
        if text[position] == ']': return
        first = position
        _, position = DECODER.raw_decode(text, position)
        yield first, position
        while text[position].isspace(): position += 1
        if text[position] == ',': position += 1
        elif text[position] == ']': return
        else: raise ValueError('Separador de lista inválido.')


def replacements(text, items, after=True):
    """Somente strings existentes; conserva todos os demais bytes e índices."""
    roots = {key: start for key, start, _ in members(text)}
    edits = []
    identifiers = set()
    for item in items:
        key = (item['strong'], item['flexao'])
        if key in identifiers: raise ValueError('Registro duplicado no manifesto.')
        identifiers.add(key)
        fields = {k: a for k, a, _ in members(text, roots[item['strong']])}
        flexes = list(array_members(text, fields['flexoes']))
        start, _ = flexes[item['flexao']]
        positions = {k: (a, b) for k, a, b in members(text, start)}
        changes = item['alteracoes']
        if not changes or not set(changes) <= TECHNICAL:
            raise ValueError('Alteração fora dos campos técnicos autorizados.')
        for field, change in changes.items():
            a, b = positions[field]
            expected = change['antes'] if after else change['depois']
            new = change['depois'] if after else change['antes']
            if json.loads(text[a:b]) != expected:
                raise ValueError(f'Campo desatualizado: {key}/{field}.')
            edits.append((a, b, json.dumps(new, ensure_ascii=False)))
    for a, b, value in sorted(edits, reverse=True):
        text = text[:a] + value + text[b:]
    return text


def plan(text, manifest):
    before = json.loads(text)  # Sem reparação implícita de sintaxe.
    if sha(text) == manifest['depois_sha256']:
        return text, 'aplicado'
    if sha(text) != manifest['antes_sha256']:
        raise ValueError('Fonte desatualizada; revisar novamente antes de aplicar.')
    for item in manifest['itens']:
        actual = before[item['strong']]['flexoes'][item['flexao']]
        if actual != item['campos_antes'] or actual['grego'] != item['forma']:
            raise ValueError('Registro revisado desatualizado.')
    result = replacements(text, manifest['itens'])
    after = json.loads(result)
    restored = json.loads(result)
    for item in manifest['itens']:
        current = restored[item['strong']]['flexoes'][item['flexao']]
        for field, change in item['alteracoes'].items(): current[field] = change['antes']
    if restored != before or replacements(result, manifest['itens'], after=False) != text:
        raise ValueError('Alteração fora dos intervalos autorizados.')
    if sha(result) != manifest['depois_sha256']:
        raise ValueError('Resultado diverge do manifesto revisado.')
    if list(before) != list(after) or any(len(before[s]['flexoes']) != len(after[s]['flexoes']) for s in before):
        raise ValueError('Grupos ou índices alterados.')
    return result, 'pendente'


def report(manifest, text):
    current = json.loads(text)
    pending = manifest['pendencia_preservada']
    s, index = pending['strong'], pending['flexao']
    if current[s]['flexoes'][index] != pending['campos_preservados']:
        raise ValueError('Registro pendente alterado sem revisão específica.')
    result = {'estado': 'APLICADO', 'antes_sha256': manifest['antes_sha256'],
              'depois_sha256': manifest['depois_sha256'], 'manifesto_sha256': sha((ROOT / MANIFEST).read_text()),
              'registros_corrigidos': len(manifest['itens']),
              'campos_tecnicos_corrigidos': sum(len(i['alteracoes']) for i in manifest['itens']),
              'itens': manifest['itens'], 'pendencia_preservada': pending,
              'preservacao': 'Nenhuma alteração em forma grega, traduções, verbetes, contagens, LXX, ordem, grupos ou índices de flexão. TM intacto.'}
    lines = ['# Aplicação dos casos morfológicos prioritários', '',
             'Seis registros corrigidos, em sete campos técnicos. Todos os demais campos e bytes do léxico foram preservados.', '']
    for item in manifest['itens']:
        changes = '; '.join(f"`{field}`: `{c['antes']}` → `{c['depois']}`" for field, c in item['alteracoes'].items())
        lines += [f"- **G{item['strong']}/{item['flexao']} — {item['forma']}**: {changes}. {item['motivo']}", '']
    lines += ['## Registro preservado para decisão humana', '',
              'G1510/49 contém `ὧν` + U+200B. Não tem ocorrência literal/NFC no TM. '
              'Sem o marcador, a forma visível corresponde ao pronome relativo G3739 nas 56 ocorrências com parsing alinhado; '
              'outras 23 ocorrências ficam sem atribuição auxiliar. Isso não autoriza transformar o registro em pronome.', '',
              'O backup histórico já misturava a chave `ὧν` + U+200B com `grego: ὢν`, código verbal genitivo plural '
              'e contagem vazia. O registro atual mistura 81 ocorrências com morfologia nominativa singular e 344 ocorrências LXX. '
              'Não há base para escolher quais contagens e campos transportar.', '',
              'Proposta não aplicada: retirar isoladamente o registro contaminado, mantendo os registros verbais `ὢν`/`ὤν` '
              'em G1510 e o pronome `ὧν` em G3739. Antes de uma exclusão aprovada, comparar os índices posteriores '
              'e reconstruir os produtos; não fundir contagens nem remover globalmente U+200B.', '',
              'A duplicidade de `ὢν` foi preservada: os dois registros agora explicitam voz ativa, mas têm metadados LXX diferentes '
              '(0 e 344). A consolidação desses metadados permanece revisão manual.', '',
              'Evidências e valores completos no manifesto e em `aplicacao.json`. '
              'Os relatórios atuais da auditoria estão em `reports/audit/morfologia/`.', '']
    return {'aplicacao.json': json.dumps(result, ensure_ascii=False, indent=2) + '\n',
            'resumo.md': '\n'.join(lines)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / MANIFEST).read_text(encoding='utf-8'))
    for source, expected in manifest['fontes_evidencia_sha256'].items():
        if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Evidência alterada: {source}')
    path = ROOT / manifest['fonte']
    text = path.read_bytes().decode('utf-8')
    result, state = plan(text, manifest)
    if args.check and state != 'aplicado': raise ValueError('Correções ainda não aplicadas.')
    files = report(manifest, result)
    if args.apply and state != 'aplicado':
        if path.read_bytes().decode('utf-8') != text: raise ValueError('Fonte mudou durante aplicação.')
        path.write_bytes(result.encode('utf-8'))
    directory = ROOT / OUTPUT
    if not args.check: directory.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = directory / name
        if args.check:
            if not target.exists() or target.read_bytes() != content.encode('utf-8'):
                raise ValueError('Relatório de aplicação desatualizado.')
        elif not target.exists() or target.read_bytes() != content.encode('utf-8'):
            target.write_bytes(content.encode('utf-8'))
    print('Seis registros técnicos corrigidos; registro invisível e metadados LXX preservados para revisão.')


if __name__ == '__main__': main()
