#!/usr/bin/env python3
"""Aplica escolhas editoriais explícitas ao lema, sem consolidar flexões.

python3 -B -m tools.audit.promote_lemma_verbetes --apply
python3 -B -m tools.audit.promote_lemma_verbetes --check

Sem --apply, apenas emite relatórios. Recusa fontes diferentes das revisadas.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from tools.audit.apply_approved_accents import members

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = 'tools/audit/approvals/verbetes-lema.json'
OUTPUT = 'reports/audit/verbetes-lema'


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def plan(text, manifest):
    """Substitui somente strings verbete diretamente nos grupos Strong."""
    current = sha(text)
    if current == manifest['depois_sha256']:
        return text, 'aplicado'
    if current != manifest['antes_sha256']:
        raise ValueError('Fonte alterada desde a revisão; não reaplicar escolhas em dados novos.')
    original = json.loads(text)
    rows = manifest['itens']
    if len({r['strong'] for r in rows}) != len(rows):
        raise ValueError('Strong duplicado no manifesto.')
    indexed = {s for s, g in original.items() if any('verbete' in f for f in g['flexoes'])}
    if indexed != {r['strong'] for r in rows}:
        raise ValueError('Manifesto não cobre o inventário de verbetes flexionais.')
    spans = {s: (a, b) for s, a, b in members(text)}
    edits = []
    for row in rows:
        s = row['strong']
        group = original[s]
        flexes = [{'flexao': i, 'grego': f['grego'], 'verbete': f['verbete']}
                  for i, f in enumerate(group['flexoes']) if 'verbete' in f]
        if (group['verbete'] != row['antes'] or group['lema'] != row['lema']
                or flexes != row['fontes_flexionais']):
            raise ValueError(f'Valores revisados divergentes: G{s}.')
        if row['estado'] not in {'APLICAR', 'MANTER', 'INCERTO'}:
            raise ValueError('Estado editorial inválido.')
        if row['estado'] != 'APLICAR':
            if row['antes'] != row['depois']:
                raise ValueError('Alteração sem decisão APLICAR.')
            continue
        if not row['depois'].startswith(f'G{s}: ') or row['antes'] == row['depois']:
            raise ValueError('Novo verbete inválido.')
        start, _ = spans[s]
        fields = {k: (a, b) for k, a, b in members(text, start)}
        a, b = fields['verbete']
        edits.append((a, b, json.dumps(row['depois'], ensure_ascii=False)))
    result = text
    for a, b, replacement in sorted(edits, reverse=True):
        result = result[:a] + replacement + result[b:]
    after = json.loads(result)
    for row in rows:
        if row['estado'] == 'APLICAR':
            after[row['strong']]['verbete'] = row['antes']
    if after != original:
        raise ValueError('Alteração fora dos campos verbete dos lemas.')
    if sha(result) != manifest['depois_sha256']:
        raise ValueError('Resultado diverge da revisão aprovada.')
    return result, 'pendente'


def reports(manifest, text, state):
    counts = Counter(r['estado'] for r in manifest['itens'])
    pending = [r for r in manifest['itens'] if r.get('pendencia')]
    different = sum(any(f['verbete'] != r['antes'] for f in r['fontes_flexionais'])
                    for r in manifest['itens'])
    data = {'versao': 1, 'estado_dados': state,
            'fonte': manifest['fonte'], 'fonte_atual_sha256': sha(text),
            'antes_sha256': manifest['antes_sha256'], 'depois_sha256': manifest['depois_sha256'],
            'manifesto_sha256': sha((ROOT / MANIFEST).read_text(encoding='utf-8')),
            'fontes_sha256': manifest['fontes_sha256'],
            'resumo': {'lemas_avaliados': len(manifest['itens']),
                       'lemas_com_divergencia_textual': different,
                       'lemas_selecionados': counts['APLICAR'],
                       'lemas_mantidos': len(manifest['itens']) - counts['APLICAR'],
                       'pendencias': len(pending),
                       'verbetes_flexionais_preservados': sum(len(r['fontes_flexionais']) for r in manifest['itens'])},
            'itens': manifest['itens']}
    lines = ['# Revisão dos verbetes no lema e nas flexões', '',
             f"Estado dos dados: **{state}**. {len(manifest['itens'])} lemas avaliados; "
             f"{counts['APLICAR']} selecionados para alteração; {len(pending)} pendências.", '',
             f'Dos lemas avaliados, {different} tinham divergência textual entre lema e flexão; '
             'nos outros cinco, o campo flexional repetia o lema.', '',
             'Foram preservados os 4.784 campos `verbete` das flexões e todos os demais campos '
             'do léxico. TM e traduções revisadas não foram alterados. Os valores anteriores e '
             'as fontes flexionais, com índices, estão registrados no JSON e no manifesto.', '',
             'Critério editorial: promover sentidos lexicais válidos, melhorar a adequação à '
             'classe gramatical e corrigir equívocos claros. Maior extensão, diferença de ordem '
             'ou mera preferência de sinônimos não bastam para escolher a flexão. As acepções '
             'listadas não são traduções obrigatórias de cada ocorrência.', '',
             'Fonte de conferência: TBESG, baseado em Abbott-Smith, Tyndale House/STEPBible, '
             'CC BY 4.0 ([projeto de origem](https://STEPBible.github.io/STEPBible-Data)). '
             'O manifesto indica arquivo, linha e hash da cópia local consultada. As escolhas '
             'portuguesas são decisões editoriais desta revisão, não traduções oficiais do TBESG.', '',
             '## Alterações selecionadas', '']
    for row in manifest['itens']:
        if row['estado'] == 'APLICAR':
            lines.extend([f"- **G{row['strong']} — {row['lema']}**: `{row['antes']}` → `{row['depois']}`. {row['motivo']}", ''])
    lines.extend(['## Pendências antes da remoção dos campos flexionais', ''])
    for r in pending:
        lines.extend([f"- **G{r['strong']} — {r['lema']}**: {r['pendencia']}", ''])
    lines.extend(['## Limites e próxima etapa', '',
        'Os demais lemas foram mantidos nesta rodada. Isso não certifica a correção de cada '
        'sinônimo anterior e não aprova excluir seus overrides. Exemplos de opções não '
        'promovidas: “pneu” em Tiro (G5184), “descanso” em λοιποί (G3062), '
        '“licenciamento” em ἀσέλγεια (G766) e “G2304: divino” dentro de G2303.', '',
        'O gerador ainda dá precedência a `flexao.verbete`. Nesta rodada, somente três formas '
        'sem override herdam o verbete atualizado: `αἰτοῦντί` (G154), `ἀσπάσησθε` (G782) '
        'e `ἔσχατον` (G2078). Os overrides existentes continuam prevalecendo. '
        'A consolidação posterior deverá resolver as '
        'pendências, revisar cada override e comparar as saídas antes/depois, mantendo '
        'Strong, homógrafos, índices e parsing. Não há exclusões autorizadas nesta aplicação.', '',
        'Reprodução: `python3 -B -m tools.audit.promote_lemma_verbetes --apply`; '
        'verificação: `python3 -B -m tools.audit.promote_lemma_verbetes --check`. '
        'A reaplicação é idempotente; uma fonte diferente das duas versões registradas é recusada.', ''])
    table = io.StringIO(newline='')
    writer = csv.writer(table)
    writer.writerow(['strong', 'lema', 'estado', 'pendencia'])
    for r in pending:
        writer.writerow([r['strong'], r['lema'], 'INCERTO', r['pendencia']])
    return {'revisao.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n',
            'resumo.md': '\n'.join(lines), 'pendencias.csv': table.getvalue()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / MANIFEST).read_text(encoding='utf-8'))
    for p, expected in manifest['fontes_sha256'].items():
        if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Fonte de conferência alterada: {p}')
    path = ROOT / manifest['fonte']
    text = path.read_bytes().decode('utf-8')
    result, state = plan(text, manifest)
    if args.check and state != 'aplicado':
        raise ValueError('Escolhas ainda não aplicadas.')
    if args.apply and state == 'pendente':
        path.write_bytes(result.encode('utf-8'))
        text, state = result, 'aplicado'
    files = reports(manifest, text, state)
    for name, content in files.items():
        target = ROOT / OUTPUT / name
        if args.check:
            if not target.exists() or target.read_bytes() != content.encode('utf-8'):
                raise ValueError(f'Relatório desatualizado: {target}')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content.encode('utf-8'))
    print(f'{state}: 551 lemas avaliados; relatório em {OUTPUT}/resumo.md')


if __name__ == '__main__':
    main()
