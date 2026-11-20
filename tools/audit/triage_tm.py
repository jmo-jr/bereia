#!/usr/bin/env python3
"""Classifica lacunas e compara consulta estrita sem escrever dados originais.

Executar como módulo: python3 -B -m tools.audit.triage_tm
"""
import argparse
from collections import Counter
from pathlib import Path
import unicodedata as ud

from tools.audit.audit_tm import ROOT, digest, dump, inventory, nfc, noun_signature, read, write
from tools.audit.strict_lookup import StrictLookup

VERSION = 1
LEXICON = 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json'
DECISIONS = 'tools/audit/decisions.json'


def acute_grave_key(form):
    # A marca continua na mesma vogal; não apagar posição, ausência de acento,
    # circunflexo, espíritos, trema ou iota subscrito.
    return ud.normalize('NFD', form.lower()).replace('\u0300', '\u0301')


def accent_key(form):
    return ''.join(c for c in ud.normalize('NFD', form.lower())
                   if c not in '\u0300\u0301\u0342')


def candidate_difference(form, candidate):
    if nfc(form.lower()) == nfc(candidate.lower()):
        return 'somente_caixa'
    if acute_grave_key(form) == acute_grave_key(candidate):
        return 'agudo_grave_mesma_posicao'
    if accent_key(form) == accent_key(candidate):
        return 'outros_acentos'
    return 'outras_marcas'


def classify_gap(row):
    form = row['forma_tm']
    if form.strip() != form:
        return 'espacos_marginais'
    differences = [candidate_difference(form, c['forma'])
                   for c in row['candidatos_sem_diacriticos']]
    for category in ('somente_caixa', 'agudo_grave_mesma_posicao', 'outros_acentos', 'outras_marcas'):
        if category in differences:
            return category
    return 'sem_candidato'


def evidence_for_gap(row, lexicon):
    """Sinais independentes do agrupamento gráfico. Nenhuma análise é copiada."""
    observed = sorted({(e['strong_fonte'], e['morfologia_fonte']) for e in row['evidencias']})
    nominal = []
    for strong, morph in observed:
        signature = noun_signature(morph, source=True)
        if signature is None or strong not in lexicon:
            continue
        code = 'S-' + ''.join(signature)
        group = lexicon[strong]
        nominal.append({'strong': strong, 'parsing_fonte': morph,
                        'abrev_morf_candidata': code,
                        'analise_presente_em_outra_forma': any(f.get('abrev_morf') == code for f in group['flexoes']),
                        'referencias': sorted({ref for e in row['evidencias']
                            if (e['strong_fonte'], e['morfologia_fonte']) == (strong, morph)
                            for ref in e['referencias']})})
    return {'analises_observadas': [{'strong': s, 'parsing': m} for s, m in observed],
            'nominais': nominal,
            'referencias_sem_parsing_alinhado': sorted(set(row['referencias']) - {
                ref for e in row['evidencias'] for ref in e['referencias']})}


def proposal(row, lexicon, lexical_hash):
    category = classify_gap(row)
    evidence = evidence_for_gap(row, lexicon)
    f = row['forma_tm']
    return {'id': 'forma:' + f.encode('utf-8').hex(), 'nivel': 'flexao',
            'estado': 'INCERTO', 'decisao': 'pendente', 'aplicado': False,
            'categoria_linguistica': 'informacao_insuficiente', 'grupo_grafico': category,
            'forma_tm': f, 'referencias': row['referencias'], 'lexico_sha256': lexical_hash,
            'candidatos': [{**c, 'diferenca': candidate_difference(f, c['forma'])}
                           for c in row['candidatos_sem_diacriticos']],
            'riscos': {'contem_iota_subscrito': '\u0345' in ud.normalize('NFD', f),
                       'candidatos_de_outros_grupos_graficos': any(
                           candidate_difference(f, c['forma']) != category
                           for c in row['candidatos_sem_diacriticos'])},
            'evidencias': evidence,
            'acao_proposta': ('Revisar espaço marginal na ocorrência do TM, sem trim automático.'
                if category == 'espacos_marginais' else
                'Revisar cobertura da grafia original e todas as análises; não criar alias sem revisão.'),
            'traducao_proposta': None, 'pt_proposto': None}


def pilot(proposals, lexicon):
    row = next((p for p in proposals if p['forma_tm'] == 'ἀρχῇ'), None)
    if row is None:
        return {'estado': 'fora_do_escopo'}
    aligned = row['evidencias']['analises_observadas']
    consistent = aligned == [{'strong': '746', 'parsing': 'N-DSF'}]
    return {'id': 'piloto:746:ἀρχῇ', 'nivel': 'flexao', 'estado': 'INCERTO',
            'decisao': 'pendente', 'aplicado': False,
            'categoria_linguistica': 'dependente_de_contexto',
            'problema_estrutural': 'Forma ἀρχῇ ausente; consulta normalizada associa ao nominativo ἀρχή.',
            'lexico_sha256': row['lexico_sha256'],
            'evidencia_nominal_consistente': consistent,
            'referencias_tm': row['referencias'], 'evidencias': row['evidencias'],
            'grupo_atual': lexicon.get('746'),
            'inclusao_em_revisao': {'strong': '746', 'grego': 'ἀρχῇ',
                'abrev_morf': 'S-DFS' if consistent else None,
                'morfologia': 'Substantivo - Dativo Feminino Singular' if consistent else None,
                'traducao': None, 'pt': None},
            'decisao_humana_necessaria': 'Definir glosa dativa interlinear em traducao/pt; avaliar se varia entre as ocorrências. Não copiar o nominativo.',
            'limite': 'As ocorrências sem alinhamento não recebem parsing por analogia.'}


def pilot_contexts(case):
    """Evidência textual específica, sem decidir sentidos automaticamente."""
    if case.get('estado') == 'fora_do_escopo':
        return {}, {}
    translations = {'AT': 'atos', 'FP': 'filipenses', 'JO': 'joao', 'LC': 'lucas'}
    texts, files, contexts = {}, {}, []
    for ref in case['referencias_tm']:
        book, location = ref.split()
        chapter_verse, position = location.split('#')
        chapter, verse = chapter_verse.split(':')
        tm = ROOT / f'src/interlinear/nt/{book}.json'
        pt = ROOT / f'src/biblia/nt/{translations[book]}/{chapter}.txt'
        if book not in texts:
            texts[book] = {v['ref']: v for v in inventory(read(tm), book)}
        files[str(tm.relative_to(ROOT))] = digest(tm)
        verse_data = texts[book][f'{book} {chapter}:{verse}']
        if verse_data['forms'][int(position) - 1] != 'ἀρχῇ':
            raise ValueError(f'Referência do piloto não corresponde à grafia: {ref}')
        approved = None
        if pt.exists():
            files[str(pt.relative_to(ROOT))] = digest(pt)
            approved = next((line for line in pt.read_text(encoding='utf-8').splitlines()
                             if line.startswith(verse + ' ')), None)
        contexts.append({'ref': ref, 'grego_tm': ' '.join(verse_data['forms']),
                         'traducao_existente': approved,
                         'arquivo_traducao': str(pt.relative_to(ROOT)),
                         'parsing_alinhado': any(ref in e['referencias'] for e in case['evidencias']['nominais'])})
    return {'contextos': contexts,
            'avaliacao_humana_preparada': {
                'estado': 'SUGERIR', 'aplicado': False,
                'proposta_glosas': {'traducao': 'ao princípio, ao poder', 'pt': 'ao princípio/ao poder'},
                'fundamento': 'As traduções existentes usam princípio em AT 11:15, FP 4:15 e JO 1:1–2; LC 20:20 usa poder e autoridade. Conferir os contextos registrados. A proposta expressa o dativo conforme outras flexões S-DFS do projeto.',
                'limite': 'Acepções sugeridas para revisão; nenhuma é atribuída automaticamente às ocorrências. Não alterar capítulos aprovados.',
                'regra': 'AGENTS.md: Não automatize escolhas lexicais ou exegéticas dependentes de contexto.'}}, files


def compare_lookup(rows, resolver):
    result = []
    for row in rows:
        strict = resolver.resolve(row['forma_tm'])
        current = row['consulta_atual']
        entries = strict['entradas']
        belongs = bool(current) and any(current['strongs'] == e['strong'] and
            current['grego'] == e['forma'] and current['abrev_morf'] == e['abrev_morf'] and
            current['morfologia'] == e['morfologia'] for e in entries)
        shadowed = bool(entries) and bool(current) and not belongs
        result.append({'forma_tm': row['forma_tm'], 'referencias': row['referencias'],
            'consulta_estrita': strict, 'consulta_atual': current,
            'analise_atual_pertence_ao_conjunto_estrito': belongs,
            'sombreamento': shadowed,
            'classificacao': ('forma_coberta_mas_sombreada' if shadowed else
                             'sem_cobertura_estrita_com_fallback_atual' if current and not entries else
                             'sem_cobertura_nas_duas' if not current and not entries else
                             'multiplas_analises_preservadas' if len(entries) > 1 else
                             'cobertura_estrita')})
    token_counts = Counter()
    for item in result:
        token_counts[item['classificacao']] += len(item['referencias'])
    return {'resumo': dict(sorted(Counter(r['classificacao'] for r in result).items())),
            'tokens_por_classificacao': dict(sorted(token_counts.items())), 'formas': result}


def apply_gloss_decision(case, contextual, proposals, decisions):
    """Atualiza a proposta em memória, nunca o léxico nem outras flexões."""
    if case.get('estado') == 'fora_do_escopo':
        return
    matches = [d for d in decisions['decisoes'] if d['strong'] == '746'
               and d['forma'] == 'ἀρχῇ' and d['estado'] == 'APROVADO']
    if not matches:
        return
    if len(matches) != 1:
        raise ValueError('Decisões conflitantes para as glosas de ἀρχῇ.')
    decision = matches[0]
    fields = decision['campos']
    if set(fields) != {'traducao', 'pt'} or any(not isinstance(v, str) or not v for v in fields.values()):
        raise ValueError('Decisão de glosas inválida.')
    case['inclusao_em_revisao'].update(fields)
    case['decisao'] = 'glosas_aprovadas_inclusao_pendente'
    case['decisao_humana_necessaria'] = None
    case['decisao_glosas'] = decision
    evaluation = contextual['avaliacao_humana_preparada']
    evaluation['proposta_anterior'] = evaluation.pop('proposta_glosas')
    evaluation['glosas_aprovadas'] = dict(fields)
    evaluation['estado'] = 'APROVADO'
    evaluation['fundamento_aprovacao'] = decision['origem']
    existing = [f for f in case['grupo_atual'].get('flexoes', []) if f['grego'] == 'ἀρχῇ']
    if existing:
        if len(existing) != 1 or any(existing[0].get(k) != v for k, v in fields.items()):
            raise ValueError('Flexão ἀρχῇ existente diverge da decisão aprovada; revisar antes de relatar aplicação.')
        case['inclusao_em_revisao'] = {'strong': '746', **existing[0]}
        case['flexao_aplicada'] = {'strong': '746', **existing[0]}
        case['estado'], case['decisao'], case['aplicado'] = 'APLICADO', 'aplicada', True
        case['problema_estrutural'] = 'Flexão própria incluída no Strong 746; conferir consulta_atual no inventário.'
        evaluation['aplicado'] = True
    for p in proposals:
        if p['forma_tm'] == 'ἀρχῇ':
            p['traducao_proposta'], p['pt_proposto'] = fields['traducao'], fields['pt']
            p['decisao'] = 'glosas_aprovadas_inclusao_pendente'
            p['decisao_glosas'] = decision


def verify_sources(report):
    if report.get('schema_version') != 1:
        raise ValueError('Versão do inventário não suportada; executar auditoria compatível.')
    for path, expected in report['fontes_sha256'].items():
        source = ROOT / path
        if not source.exists() or digest(source) != expected:
            raise ValueError(f'Inventário desatualizado: {path}; executar audit_tm.py novamente.')
    for path in report.get('fontes_ausentes', []):
        if (ROOT / path).exists():
            raise ValueError(f'Fonte antes ausente agora disponível: {path}; repetir auditoria.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inventory', default='reports/audit/tm/inventario.json')
    ap.add_argument('--output', default='reports/audit/triagem')
    args = ap.parse_args()
    inventory_path = (ROOT / args.inventory).resolve()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / 'reports/audit').resolve()):
        ap.error('--output deve estar em reports/audit')
    report = read(inventory_path)
    verify_sources(report)
    lexical_hash = report['fontes_sha256'][LEXICON]
    lexicon = read(ROOT / LEXICON)
    proposals = [proposal(row, lexicon, lexical_hash) for row in report['formas'] if row['classe'] == 'ausente']
    comparison = compare_lookup(report['formas'], StrictLookup(lexicon))
    manifest = {'inventario_sha256': digest(inventory_path), 'fontes_sha256': report['fontes_sha256'],
                'implementacao_sha256': {p: digest(ROOT / p) for p in
                    ('tools/audit/triage_tm.py', 'tools/audit/strict_lookup.py', DECISIONS)},
                'escopo': report['escopo'], 'schema_version': VERSION}
    grouped = dict(sorted(Counter(p['grupo_grafico'] for p in proposals).items()))
    all_proposals = {**manifest, 'criterio': 'Grupos gráficos descrevem a diferença mínima entre candidatos, não identidade lexical/morfológica. Nenhuma proposta aplicada.',
        'resumo': grouped, 'propostas': proposals}
    summary = {**manifest, 'formas_sem_cobertura': len(proposals), 'grupos': grouped,
               'consulta': comparison['resumo'],
               'consulta_tokens': comparison['tokens_por_classificacao'],
               'propostas_com_evidencia_nominal': sum(bool(p['evidencias']['nominais']) for p in proposals)}
    pilot_rows = list(proposals)
    if not any(p['forma_tm'] == 'ἀρχῇ' for p in pilot_rows):
        covered = next((r for r in report['formas'] if r['forma_tm'] == 'ἀρχῇ'), None)
        if covered:
            pilot_rows.append(proposal(covered, lexicon, lexical_hash))
    case = pilot(pilot_rows, lexicon)
    contextual, contextual_hashes = pilot_contexts(case)
    apply_gloss_decision(case, contextual, proposals, read(ROOT / DECISIONS))
    summary['piloto_aplicado'] = case.get('aplicado', False)
    approved = contextual.get('avaliacao_humana_preparada', {}).get('glosas_aprovadas')
    gloss_summary = (f'Glosas aprovadas pelo usuário: traducao="{approved["traducao"]}"; pt="{approved["pt"]}".'
                     if approved else 'Sem decisão de glosas aplicável ao piloto neste escopo.')
    verify_sources(report)
    if digest(inventory_path) != manifest['inventario_sha256']:
        raise ValueError('Inventário mudou durante a triagem; repetir execução.')
    if any(digest(ROOT / path) != expected for path, expected in contextual_hashes.items()):
        raise ValueError('Contexto do piloto mudou durante a triagem; repetir execução.')
    output.mkdir(parents=True, exist_ok=True)
    write(output / 'propostas.json', dump(all_proposals))
    write(output / 'comparacao-consultas.json', dump({**manifest, **comparison}))
    write(output / 'piloto-arche.json', dump({**manifest, **case, **contextual,
                                           'contextos_sha256': contextual_hashes}))
    write(output / 'resumo.json', dump(summary))
    lines = ['# Triagem de cobertura e consulta experimental', '',
        f"Escopo: {', '.join(report['escopo'])}.", '',
        f'Formas sem cobertura literal/NFC: {len(proposals)}.', '',
        *[f'- {name}: {count}.' for name, count in grouped.items()], '',
        'As categorias descrevem diferenças gráficas. Nenhuma cria equivalência ou autoriza fusão.',
        'Agudo/grave conserva a posição da marca. Outros acentos incluem diferenças de posição, presença e circunflexo.',
        'Os grupos também podem conter candidatos de outras categorias; cada candidato tem classificação própria.', '',
        '## Consulta estrita em paralelo', '',
        *[f'- {name}: {count} formas.' for name, count in comparison['resumo'].items()], '',
        *[f'- {name}: {count} tokens.' for name, count in comparison['tokens_por_classificacao'].items()], '',
        'A consulta experimental aceita somente igualdade literal/NFC e devolve todas as análises canonicamente equivalentes.',
        f'Consulta em produção registrada no inventário: {report.get("consulta_modo", "normalizacao_legada")}.',
        'Não altera o loader, o painel, os dados ou as exceções. Diferença entre consultas não comprova erro de tradução.', '',
        '## Decisão humana', '',
        'O piloto ἀρχῇ mantém a proposta técnica S-DFS separada da decisão de glosas.',
        'O piloto registra contextos do TM e traduções existentes com hashes; o número de ocorrências depende do escopo.',
        'No escopo integral, cinco ocorrências estão registradas e quatro têm parsing auxiliar alinhado N-DSF.',
        gloss_summary,
        'Lucas 20:20 usa poder na tradução existente; as demais usam princípio. Não atribuir acepções automaticamente.',
        ('A inclusão de ἀρχῇ foi aplicada ao dicionário com as glosas aprovadas; não consta das propostas pendentes.'
         if case.get('aplicado') else 'A inclusão no dicionário continua pendente; a decisão de glosas está preservada em tools/audit/decisions.json.'), '',
        '## Reprodução', '',
        '`python3 -B -m tools.audit.triage_tm`', '',
        'A execução recusa inventários com fontes alteradas. Artefatos determinísticos, sem data ou caminho absoluto.', '']
    write(output / 'resumo.md', '\n'.join(lines))
    print(dump({k: summary[k] for k in ('formas_sem_cobertura', 'grupos', 'consulta', 'propostas_com_evidencia_nominal')}))


if __name__ == '__main__':
    main()
