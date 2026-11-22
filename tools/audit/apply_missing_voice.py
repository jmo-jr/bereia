#!/usr/bin/env python3
"""Aplicação separada da revisão autorizada dos 48 alertas de voz.

python3 -B -m tools.audit.apply_missing_voice --apply
python3 -B -m tools.audit.apply_missing_voice --check
"""
import argparse
import hashlib
import json
from collections import Counter

from tools.audit.apply_morphology_priorities import plan, sha
from tools.audit.audit_tm import ROOT

MANIFEST = 'tools/audit/approvals/vozes-48.json'
OUTPUT = 'reports/audit/vozes-48'


def validate_manifest(manifest):
    items=manifest['itens']
    if len(items)!=47 or len(manifest['nao_aplicavel'])!=1:
        raise ValueError('Lote deve conter 47 correções e um registro genérico preservado.')
    for item in items:
        if item['strong'] not in {'1510','1751','3918'}:
            raise ValueError('Grupo fora da revisão autorizada.')
        changes=item['alteracoes'];old=item['campos_antes']
        if set(changes)!={'abrev_morf','morfologia'}:
            raise ValueError('Somente código e descrição de voz são autorizados.')
        parts=old['abrev_morf'].split('-')
        if len(parts)<2 or len(parts[1])!=2:
            raise ValueError('Código anterior não é uma análise com voz omitida.')
        voice=item['voz_revisada']
        if voice not in {'A','M'}:raise ValueError('Voz fora das escolhas revisadas.')
        if voice!=('M' if parts[1][0]=='F' else 'A'):
            raise ValueError('Voz divergente do paradigma copular revisado.')
        parts[1]+=voice
        sections=old['morfologia'].split(' - ')
        if len(sections)<2:raise ValueError('Descrição sem análise flexional.')
        sections[1]+=' '+{'A':'Ativa','M':'Média'}[voice]
        expected={'abrev_morf':'-'.join(parts),'morfologia':' - '.join(sections)}
        for field,value in expected.items():
            if changes[field]!={'antes':old[field],'depois':value}:
                raise ValueError('Mudança além da indicação de voz revisada.')
    if Counter(i['voz_revisada'] for i in items)!=Counter({'A':38,'M':9}):
        raise ValueError('Distribuição das vozes diverge da revisão.')
    generic=manifest['nao_aplicavel'][0]
    if (generic['strong'],generic['flexao'])!=('1507',0) or generic['campos_preservados']['abrev_morf']!='V':
        raise ValueError('Registro genérico não reconhecido.')


def reports(manifest,text):
    current=json.loads(text)
    for row in manifest['nao_aplicavel']:
        if current[row['strong']]['flexoes'][row['flexao']]!=row['campos_preservados']:
            raise ValueError('Registro genérico alterado.')
    summary={'estado':'APLICADO','revisados':48,'corrigidos':47,'campos_tecnicos':94,
             'ativas':38,'medias':9,'genericos_preservados':1,
             'antes_sha256':manifest['antes_sha256'],'depois_sha256':manifest['depois_sha256'],
             'manifesto_sha256':sha((ROOT/MANIFEST).read_text()),
             'fontes_gramaticais':manifest['fontes_gramaticais'],
             'itens':manifest['itens'],'nao_aplicavel':manifest['nao_aplicavel'],
             'preservacao':'Somente abrev_morf e morfologia alterados; traduções, grego, contagens, verbetes, LXX e índices de flexão preservados.'}
    lines=['# Revisão dos 48 alertas de voz','',
           'Foram examinados os 48 alertas anteriores: 47 registros corrigidos '
           '(38 com voz ativa e nove com voz média), em 94 campos técnicos. '
           'Um registro genérico foi preservado e retirado da categoria indevida de omissão de voz.','',
           '## Critérios e limites','',
           '- Preservadas todas as demais características das análises. Não foram combinados casos, gêneros, pessoas ou números nesta rodada.',
           '- Nos futuros de εἰμί e πάρειμι, a voz é média. O código Robinson D identifica média deponente; não foi convertido em ativa nem estendido a outras famílias.',
           '- Sete registros não têm parsing auxiliar integralmente alinhado para a grafia exata. A decisão sobre voz usa o paradigma e a identificação lexical; não se atribui parsing auxiliar a essas ocorrências.',
           '- Grafias sem ocorrência literal no TM foram preservadas; não foi removido nenhum diacrítico para provar identidade.',
           '- A tradução portuguesa não foi usada para inferir voz e permaneceu intacta.','',
           '## Registro genérico G1507','',
           '`εἱλίσσω` está registrado com `abrev_morf: V`, `morfologia: Verbo`, '
           'contagem NT vazia e sem ocorrência literal/NFC no TM. Isso informa a classe verbal, '
           'não uma análise de tempo/modo/pessoa à qual faltaria voz. O registro permanece '
           'inteiramente preservado e explicitamente contado como genérico no auditor. '
           'Não foi inventada uma flexão nem uma ocorrência NT.','',
           '## Alterações aplicadas','']
    for row in manifest['itens']:
        old=row['campos_antes'];new=row['alteracoes']
        lines += [f"- **G{row['strong']}/{row['flexao']} — {row['forma']}**: "
                  f"`{old['abrev_morf']}` → `{new['abrev_morf']['depois']}`; "
                  f"`{new['morfologia']['depois']}`. Base: {row['base_da_decisao']}.",'']
    lines += ['## Fontes gramaticais','']
    for source in manifest['fontes_gramaticais']:
        lines += [f"- [{source['titulo']}]({source['url']}): {source['uso']}",'']
    lines += ['## Reprodução','',
              '`python3 -B -m tools.audit.apply_missing_voice --apply` aplica somente o manifesto revisado. '
              '`--check` verifica o resultado. Ambas as operações recusam fontes alteradas; '
              'reaplicar o lote sobre seu resultado é idempotente.', '',
              'O balanço geral atualizado está em `reports/audit/morfologia/resumo.md`. '
              'As demais divergências e o registro G1510/49 com marcador invisível continuam fora desta aplicação.','']
    return {'aplicacao.json':json.dumps(summary,ensure_ascii=False,indent=2)+'\n',
            'resumo.md':'\n'.join(lines)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply',action='store_true');mode.add_argument('--check',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
    validate_manifest(manifest)
    for path,expected in manifest['fontes_evidencia_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError(f'Evidência alterada: {path}')
    path=ROOT/manifest['fonte'];text=path.read_bytes().decode('utf-8')
    result,state=plan(text,manifest)
    if args.check and state!='aplicado':raise ValueError('Lote ainda não aplicado.')
    files=reports(manifest,result)
    if args.apply and state!='aplicado':
        if path.read_bytes().decode('utf-8')!=text:raise ValueError('Fonte mudou durante a aplicação.')
        path.write_bytes(result.encode('utf-8'))
    directory=ROOT/OUTPUT
    if not args.check:directory.mkdir(parents=True,exist_ok=True)
    for name,content in files.items():
        target=directory/name;encoded=content.encode('utf-8')
        if args.check:
            if not target.exists() or target.read_bytes()!=encoded:raise ValueError('Relatório desatualizado.')
        elif not target.exists() or target.read_bytes()!=encoded:target.write_bytes(encoded)
    print('48 alertas revisados: 47 registros corrigidos (38 ativa, 9 média); um registro genérico preservado.')


if __name__=='__main__':main()
