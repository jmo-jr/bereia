#!/usr/bin/env python3
"""Auditoria local, somente leitura; biblioteca padrão Python 3.9+."""
import argparse
import csv
import hashlib
import json
import re
import unicodedata as ud
import sys
from collections import Counter, defaultdict
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.audit.accent_alias_rules import AccentAliases

ROOT = Path(__file__).resolve().parents[2]
VERSION = 1
BOOKS = dict(zip(
    'MT MC LC JO AT RM 1CO 2CO GL EF FP CL 1TS 2TS 1TM 2TM TT FM HB TG 1PE 2PE 1JO 2JO 3JO JD AP'.split(),
    'MAT MAR LUK JOH ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAM 1PE 2PE 1JO 2JO 3JO JUD REV'.split()))
TOKEN = re.compile(r'(\S+)\s+(\d+)\s+\{([^}]+)\}')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nfc(s):
    return ud.normalize('NFC', s)


def folded(s):
    """Candidatos/alinhamento auxiliar somente; nunca identidade de flexão."""
    return ''.join(c for c in ud.normalize('NFD', s) if not ud.category(c).startswith('M')).lower()


def legacy_key(s, exceptions):
    # Espelha src/_data/nt/index.js, incluindo suas exceções especiais.
    trimmed = s if s.strip() in {'ὦ ', 'Ὦ\u200b'} else s.strip()
    stripped = re.sub('[\u0300-\u036f]', '', ud.normalize('NFD', trimmed)).lower()
    return nfc(trimmed.lower()) if stripped in exceptions else stripped


def exceptions_from(text):
    match = re.search(r'const NORMALIZATION_EXCEPTIONS = new Set\((\[.*?\])\)', text, re.S)
    if not match:
        raise ValueError('Lista de exceções não reconhecida; atualizar adaptador da auditoria.')
    return json.loads(match[1])


def inventory(chapters, book):
    verses = []
    for chapter in chapters:
        for pericope in chapter['pericopes']:
            for verse in pericope['verses']:
                forms = [t['lemma'] for t in verse['tokens']]
                if any(not isinstance(f, str) or not f for f in forms):
                    raise ValueError(f'{book}: token sem forma grega')
                verses.append({'ref': f"{book} {chapter['chapter']}:{verse['verse']}",
                               'chapter': str(chapter['chapter']), 'verse': str(verse['verse']),
                               'forms': forms, 'tokens': verse['tokens']})
    return verses


def parsing(path):
    result = {}
    with path.open(encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle):
            matches = list(TOKEN.finditer(row['text']))
            # Não aceitar silenciosamente um CSV parcialmente reconhecido.
            remainder = TOKEN.sub('', row['text']).strip()
            key = (row['chapter'], row['verse'])
            if key in result:
                raise ValueError(f'{path}: referência duplicada {key}')
            result[key] = {'tokens': [m.groups() for m in matches], 'valid': not remainder and bool(matches)}
    return result


def align(verse, auxiliary):
    if auxiliary is None:
        return 'sem_fonte'
    if not auxiliary['valid']:
        return 'parsing_invalido'
    tokens = auxiliary['tokens']
    if len(tokens) != len(verse['forms']):
        return 'quantidade_divergente'
    if any(folded(f) != folded(t[0]) for f, t in zip(verse['forms'], tokens)):
        return 'sequencia_divergente'
    return 'alinhado'


def noun_signature(code, source=False):
    # Apenas substantivos simples: Robinson N-DSF versus BEREIA S-DFS.
    pattern = r'N-([NGDAV])([SP])([MFN])' if source else r'S-([NGDAV])([MFN])([SP])'
    m = re.fullmatch(pattern, code or '')
    if not m:
        return None
    a, b, c = m.groups()
    return (a, c, b) if source else (a, b, c)


def compatibility(rows, strong, morph):
    same = [r for r in rows if r['strong'] == strong]
    if not same:
        return 'strong_divergente'
    if any(r['abrev_morf'] == morph for r in same):
        return 'codigo_identico'
    expected = noun_signature(morph, True)
    signatures = [noun_signature(r['abrev_morf']) for r in same]
    if expected and expected in signatures:
        return 'substantivo_compativel'
    if expected and expected[1] == 'N' and expected[0] in {'N', 'A'} and any(
            signature and signature[1:] == expected[1:] and signature[0] in {'N', 'A'}
            for signature in signatures):
        # Regra do projeto: não gerar pendência apenas pelo sincretismo neutro
        # nominativo/acusativo com a mesma tradução.
        return 'substantivo_compativel_nom_acus_neutro'
    if expected and signatures and all(signatures):
        return 'morfologia_divergente'
    return 'nao_comparavel'  # Nunca confundir convenções distintas com erro.


def index_lexicon(lexicon):
    literal, canonical, case, candidates = (defaultdict(list) for _ in range(4))
    for strong, group in lexicon.items():
        for i, flex in enumerate(group['flexoes']):
            row = {'strong': strong, 'flexao': i, 'lema': group.get('lema'),
                   'forma': flex['grego'], 'abrev_morf': flex.get('abrev_morf'),
                   'morfologia': flex.get('morfologia')}
            for index, key in ((literal, row['forma']), (canonical, nfc(row['forma'])),
                               (case, nfc(row['forma'].lower())), (candidates, folded(row['forma']))):
                index[key].append(row)
    return literal, canonical, case, candidates


def classify(form, indexes, ignore_case=False):
    literal, canonical, case, candidates = indexes
    if literal.get(form):
        return 'exata', literal[form]
    if canonical.get(nfc(form)):
        return 'somente_nfc', canonical[nfc(form)]
    if ignore_case and case.get(nfc(form.lower())):
        return 'somente_caixa', case[nfc(form.lower())]
    # Caixa é separada de equivalência Unicode e não autoriza associação.
    return 'ausente', []


def audit(verses, sources, lexicon, flat, exceptions, prefer_exact=False, ignore_case=False,
          accent_aliases=None, alias_valid_books=()):
    indexes = index_lexicon(lexicon)
    form_index = {form: [{'strongs': r['strong'], 'flexao': r['flexao']} for r in entries]
                  for form, entries in indexes[0].items()}
    alias_resolver = AccentAliases(accent_aliases, flat, form_index, alias_valid_books)
    forms = {}
    alignment = []
    legacy = {}
    exact, canonical = {}, {}
    for key, entry in flat.items():
        selected = {'chave': key, **{k: entry.get(k) for k in ('strongs', 'grego', 'abrev_morf', 'morfologia')}}
        exact[key] = selected
        canonical.setdefault(nfc(key), selected)
        legacy.setdefault(legacy_key(key, exceptions), selected)
    for verse in verses:
        aux = sources.get((verse['ref'].split()[0], verse['chapter'], verse['verse']))
        status = align(verse, aux)
        alignment.append({'ref': verse['ref'], 'estado': status})
        for pos, form in enumerate(verse['forms'], 1):
            if form not in forms:
                category, entries = classify(form, indexes, ignore_case=ignore_case)
                selected = legacy.get(legacy_key(form, exceptions))
                ambiguous_case = False
                multiple_case_analyses = False
                if prefer_exact:
                    selected = exact.get(form) or canonical.get(nfc(form)) or selected
                if ignore_case and form not in exact and nfc(form) not in canonical:
                    case_entries = indexes[2].get(nfc(form.lower()), [])
                    if (len({nfc(entry['forma']) for entry in case_entries}) > 1 or
                            len({entry['strong'] for entry in case_entries}) > 1):
                        ambiguous_case, selected = True, None
                    elif case_entries:
                        selected = canonical[nfc(case_entries[0]['forma'])]
                        multiple_case_analyses = len(case_entries) > 1
                controlled_accent = False
                if form not in exact and nfc(form) not in canonical and not (ignore_case and indexes[2].get(nfc(form.lower()))):
                    controlled_accent = alias_resolver.resolve(form)['estado'] != 'fora_escopo'
                    if controlled_accent:
                        selected = None  # Sem referência, não há escolha contextual.
                forms[form] = {'forma_tm': form, 'classe': category, 'referencias': [],
                               'entradas': entries,
                               'candidatos_sem_diacriticos': indexes[3].get(folded(form), []),
                               'candidatos_caixa': indexes[2].get(nfc(form.lower()), []),
                               'ambiguidades': len(entries) > 1,
                               'consulta_ambigua_caixa': ambiguous_case,
                               'consulta_multianalise_caixa': multiple_case_analyses,
                               'origem_controlada_acento': controlled_accent,
                               'consultas_contextuais': {},
                               'candidatos_multiplos': len(indexes[3].get(folded(form), [])) > 1,
                               'situacao_normalizacao': ('equivalencia_caixa' if category == 'somente_caixa' else
                                   'equivalencia_nfc' if category == 'somente_nfc' else
                                   'somente_caixa_candidata' if category == 'ausente' and indexes[2].get(nfc(form.lower())) else
                                   'somente_sem_marcas_candidata' if category == 'ausente' and indexes[3].get(folded(form)) else
                                   'sem_candidato' if category == 'ausente' else 'literal'),
                               'consulta_atual': selected, 'evidencias': {}}
            row = forms[form]
            ref = f"{verse['ref']}#{pos}"
            row['referencias'].append(ref)
            current_selected = row['consulta_atual']
            if row['origem_controlada_acento']:
                resolved = alias_resolver.resolve(form, ref)
                entry = resolved.get('entrada')
                current_selected = ({'chave': entry['grego'], **{k: entry.get(k) for k in
                    ('strongs', 'grego', 'abrev_morf', 'morfologia')}} if entry else None)
                alias_id = resolved.get('alias', {}).get('id')
                key = (resolved['estado'], alias_id)
                if key not in row['consultas_contextuais']:
                    row['consultas_contextuais'][key] = {'estado': resolved['estado'], 'alias_id': alias_id,
                        'destino': current_selected, 'referencias': []}
                row['consultas_contextuais'][key]['referencias'].append(ref)
            if status == 'alinhado':
                _, strong, morph = aux['tokens'][pos - 1]
                outcome = compatibility(row['entradas'], strong, morph) if row['entradas'] else 'forma_ausente'
                selected = current_selected
                current = compatibility([{'strong': selected.get('strongs'), 'abrev_morf': selected.get('abrev_morf')}], strong, morph) if selected else 'sem_resultado'
                if row['consulta_ambigua_caixa']:
                    current = 'ambiguidade_caixa'
                if row['origem_controlada_acento'] and not current_selected:
                    current = 'alias_acento_pendente'
                key = (strong, morph, outcome, current)
                if key not in row['evidencias']:
                    row['evidencias'][key] = {'strong_fonte': strong, 'morfologia_fonte': morph,
                        'comparacao_exata_nfc': outcome, 'comparacao_consulta_atual': current, 'referencias': []}
                row['evidencias'][key]['referencias'].append(ref)
            # Campos originais opcionais do TM também são evidência, nunca sobrescritos.
            token = verse['tokens'][pos - 1]
            if len(token) > 1:
                row.setdefault('metadados_tm', []).append({'ref': ref, 'token': token})
    rows = sorted(forms.values(), key=lambda x: x['forma_tm'])
    for row in rows:
        row['evidencias'] = list(row['evidencias'].values())
        row['consultas_contextuais'] = list(row['consultas_contextuais'].values())
    return {'resumo': {'tokens_tm': sum(len(r['referencias']) for r in rows), 'formas_tm': len(rows),
        'classes': dict(sorted(Counter(r['classe'] for r in rows).items())),
        'ausentes_com_candidatos': sum(r['classe'] == 'ausente' and bool(r['candidatos_sem_diacriticos']) for r in rows),
        'formas_com_multiplas_analises': sum(r['ambiguidades'] for r in rows),
        'formas_com_multiplos_candidatos': sum(r['candidatos_multiplos'] for r in rows),
        'ausentes_apenas_caixa': sum(r['classe'] == 'ausente' and bool(r['candidatos_caixa']) for r in rows),
        'formas_com_ambiguidade_caixa': sum(r['consulta_ambigua_caixa'] for r in rows),
        'formas_com_multiplas_analises_por_caixa': sum(r['consulta_multianalise_caixa'] for r in rows),
        'formas_com_alias_contextual_validado': sum(any(c['estado'] == 'resolvido' for c in r['consultas_contextuais']) for r in rows),
        'tokens_alias_contextual_validado': sum(len(c['referencias']) for r in rows for c in r['consultas_contextuais'] if c['estado'] == 'resolvido'),
        'tokens_alias_contextual_pendente': sum(len(c['referencias']) for r in rows for c in r['consultas_contextuais'] if c['estado'] == 'pendente'),
        'tokens_com_ambiguidade_caixa': sum(len(r['referencias']) for r in rows if r['consulta_ambigua_caixa']),
        'consulta_atual_forma_diferente_nfc': sum(bool(r['consulta_atual']) and nfc(r['consulta_atual']['grego']) != nfc(r['forma_tm']) for r in rows),
        'alinhamento_versiculos': dict(sorted(Counter(r['estado'] for r in alignment).items())),
        'comparacoes': dict(sorted(Counter(e['comparacao_exata_nfc'] for r in rows for e in r['evidencias']).items()))},
        'formas': rows, 'alinhamento': alignment}


def write(path, content):
    if not path.exists() or path.read_text(encoding='utf-8') != content:
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(content, encoding='utf-8')
        tmp.replace(path)


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', default='reports/audit/tm')
    ap.add_argument('--books', nargs='+', choices=sorted(BOOKS), help='Escopo parcial explícito')
    ap.add_argument('--no-cache', action='store_true')
    args = ap.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / 'reports/audit').resolve()):
        ap.error('--output deve estar em reports/audit (proteção das fontes)')
    output.mkdir(parents=True, exist_ok=True)
    paths = {name: ROOT / path for name, path in {
        'lexico': 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json',
        'derivado': 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json',
        'indice': 'src/_data/nt/dict_form_index_nt-lxx_greek-pt.json',
        'consulta': 'src/_data/nt/index.js', 'painel': 'src/assets/js/strong-drawer.js',
        'chave_caixa': 'src/lib/greek-form-lookup.js',
        'resolvedor_acento': 'src/lib/greek-accent-aliases.js',
        'regras_acento': 'tools/audit/accent_alias_rules.py',
        'gerador': 'tools/dictionary/generate.js', 'core': 'tools/dictionary/core.js',
        'strong_archive': 'src/_data/archive/strongsg.js',
        'tbesg': 'tools/lxx/fontes/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt',
        'strong_pt_legado': 'src/_data/strongs_greek_pt_defs.json',
        'auditor': 'tools/audit/audit_tm.py'}.items()}
    verses, sources = [], {}
    aliases_path = ROOT / 'src/_data/nt/greek_accent_aliases.json'
    if aliases_path.exists():
        paths['aliases'] = aliases_path
    for book in sorted(args.books or BOOKS):
        tm = ROOT / f'src/interlinear/nt/{book}.json'
        csv_path = ROOT / f'tools/tmnt/with-parsing/{BOOKS[book]}.csv'
        paths[f'tm/{book}'] = tm
        if csv_path.exists():
            paths[f'parsing/{book}'] = csv_path
        key = hashlib.sha256(f'{VERSION}:{digest(Path(__file__))}:{digest(tm)}:{digest(csv_path) if csv_path.exists() else "ausente"}'.encode()).hexdigest()
        cache = output / '.cache' / f'{book}.json'
        try:
            cached = read(cache) if not args.no_cache and cache.exists() else None
        except (ValueError, OSError):
            cached = None
        if cached and cached.get('key') == key:
            book_verses, book_sources = cached['verses'], cached['sources']
        else:
            book_verses = inventory(read(tm), book)
            book_sources = [[*k, v] for k, v in parsing(csv_path).items()] if csv_path.exists() else []
            if not args.no_cache:
                cache.parent.mkdir(exist_ok=True)
                write(cache, dump({'key': key, 'verses': book_verses, 'sources': book_sources}))
        verses.extend(book_verses)
        sources.update({(book, c, v): t for c, v, t in book_sources})
    missing_sources = [str(p.relative_to(ROOT)) for p in paths.values() if not p.exists()]
    manifest = {str(p.relative_to(ROOT)): digest(p) for p in paths.values() if p.exists()}
    lexicon, flat = read(paths['lexico']), read(paths['derivado'])
    lookup_source = paths['consulta'].read_text(encoding='utf-8')
    prefer_exact = 'const canonicalDictIndex = new Map();' in lookup_source
    ignore_case = 'const caseDictIndex = buildCaseDictIndex(' in lookup_source
    accent_manifest = read(aliases_path) if aliases_path.exists() and 'const accentAliasIndex = buildAccentAliasIndex(' in lookup_source else None
    valid_books = {book for book, evidence in (accent_manifest or {}).get('evidencia_por_livro', {}).items()
                   if len(evidence) == 2 and all(manifest.get(p) == h for p, h in evidence.items())}
    report = audit(verses, sources, lexicon, flat, exceptions_from(lookup_source), prefer_exact=prefer_exact,
                   ignore_case=ignore_case, accent_aliases=accent_manifest, alias_valid_books=valid_books)
    report['consulta_modo'] = ('literal_nfc_caixa_alias_contextual' if accent_manifest else
                             'literal_nfc_caixa_antes_do_fallback_legado' if ignore_case else
                             'literal_nfc_antes_do_fallback_legado' if prefer_exact else 'normalizacao_legada')
    expected_flat, expected_index = {}, defaultdict(list)
    for strong, group in lexicon.items():
        for i, f in enumerate(group['flexoes']):
            expected_index[f['grego']].append({'strongs': strong, 'flexao': i})
            expected_flat.setdefault(f['grego'], {'strongs': strong, **f,
                'verbete': f.get('verbete', group.get('verbete'))})
    report['produtos'] = {'derivado_coerente': expected_flat == flat,
                          'indice_coerente': dict(expected_index) == read(paths['indice'])}
    report['fontes_ausentes'] = missing_sources
    report['schema_version'] = VERSION
    report['fontes_sha256'] = manifest
    report['excecoes_normalizacao_atuais'] = exceptions_from(paths['consulta'].read_text(encoding='utf-8'))
    report['escopo'] = sorted(args.books or BOOKS)
    report['criterios'] = {
        'exata': 'Igualdade literal com flexoes[].grego; caixa preservada.',
        'somente_nfc': 'Equivalência canônica NFC, sem remover marcas nem converter caixa.',
        'somente_caixa': 'Correspondência por minúsculas + NFC, sem retirar marcas ou espaços. Uma única forma canônica mantém a projeção de compatibilidade e todas as referências de análises; formas canônicas diferentes bloqueiam o fallback.',
        'ausente': 'Sem flexão literal/NFC ou equivalente por caixa; candidatos sem marcas não são correspondências.',
        'ambiguidades': 'Múltiplas entradas literais/NFC/caixa preservadas; não são erros por si só.',
        'evidencia': 'CSV local alinhado por versículo inteiro; grafia sem diacríticos não prova identidade morfológica.',
        'morfologia': 'Código idêntico ou mapeamento explícito N-caso-número-gênero → S-caso-gênero-número; sincretismo neutro nominativo/acusativo não cria divergência própria. Demais convenções: não comparável.',
        'inconsistencias': 'Divergências entre fontes, sujeitas a revisão; sem correção automática.',
        'aliases': 'Equivalência agudo/grave somente nas referências validadas; consultas_contextuais detalha os resultados por ocorrência. Origem controlada sem prova não usa fallback legado.',
        'contagens': 'Comparações contam grupos forma/Strong/parsing/resultado, não tokens. Referências usam token iniciado em 1.',
        'incremental': 'Cache por livro e SHA256; relatório completo recalculado. --books restringe explicitamente o escopo.'}
    # As fontes não podem mudar durante a execução.
    if any(not (ROOT / p).exists() or digest(ROOT / p) != h for p, h in manifest.items()):
        raise RuntimeError('Fonte mudou durante a execução; repetir auditoria.')
    write(output / 'inventario.json', dump(report))
    write(output / 'ambiguidades-caixa.json', dump({'schema_version': VERSION,
        'formas': [r for r in report['formas'] if r['consulta_ambigua_caixa']]}))
    issues = [r for r in report['formas'] if any(e['comparacao_exata_nfc'] in {'strong_divergente', 'morfologia_divergente'} or e['comparacao_consulta_atual'] in {'strong_divergente', 'morfologia_divergente'} for e in r['evidencias'])]
    write(output / 'inconsistencias.json', dump({'schema_version': VERSION, 'formas': issues}))
    case = [r for r in report['formas'] if nfc(r['forma_tm'].lower()) in {'ἀρχῇ', 'ἀρχή', 'ἀρχὴ'}]
    write(output / 'caso-arche.json', dump({'schema_version': VERSION, 'formas': case, 'grupo_746': lexicon.get('746')}))
    dative = next((r for r in case if r['forma_tm'] == 'ἀρχῇ'), None)
    pilot_status = ('A flexão própria ἀρχῇ está no dicionário e a consulta atual a retorna separadamente de ἀρχή.'
                    if dative and dative['entradas'] and dative['consulta_atual'] and dative['consulta_atual']['grego'] == 'ἀρχῇ'
                    else 'A consulta atual exige revisão: confira a cobertura e a entrada retornada para ἀρχῇ em caso-arche.json.')
    lines = ['# Auditoria do TM — etapa 1', '', f"Escopo: {', '.join(report['escopo'])}.", '',
        'Dados originais preservados. Hashes, critérios e referências em inventario.json.', '',
        *[f'- {k}: {json.dumps(v, ensure_ascii=False)}' for k, v in report['resumo'].items()],
        f'- Fontes referenciadas ausentes: {missing_sources}.',
        f'- Produtos derivados: {json.dumps(report["produtos"], ensure_ascii=False)}',
        f'- Formas com divergências nas fontes ou na consulta atual: {len(issues)}.', '',
        '## Caso ἀρχῇ / ἀρχή', '',
        pilot_status + ' Historicamente, a consulta removia marcas e selecionava ἀρχή para a chave αρχη. '
        'Em JO 1:1#2 e JO 1:2#4, '
        'o CSV alinhado informa G746 / N-DSF (dativo singular feminino). A associação '
        'ao nominativo perde o iota subscrito. NFC preserva essa distinção. Veja caso-arche.json.', '',
        '## Limites e proposta de correção', '',
        '- Três grafias sem candidatos contêm espaço final: Εὗρον , βασιλείας , εὗρον . Preservadas; conferir referências no inventário antes de propor qualquer ajuste.',
        '- Ausências incluem caixa, acentos contextuais e flexões distintas; examinar as referências antes de propor inclusão.',
        '- Fontes Strong históricas referenciadas pelos scripts (strongsg.js e strongs_greek_pt_defs.json) estão ausentes. TBESG está disponível; não foi usado para decidir flexões nesta etapa.',
        '- Falhas de alinhamento ficam sem comparação auxiliar; não deslocar tokens nem inferir Strong pela forma normalizada.',
        '- Divergências de parsing são evidências para revisão. Códigos verbais e compostos sem adaptador ficam não comparáveis.',
        '- Substituir futuramente a consulta por índice literal/NFC multianálise, mantendo identificadores Strong e flexão. Em ambiguidade, conservar todas as análises.',
        '- Usar candidatos sem diacríticos somente na revisão; não os usar como fallback automático. Validar cobertura e regressões antes de retirar exceções.',
        '- Acompanhar a aplicação aprovada de ἀρχῇ em tools/audit/decisions.json; não renomear ἀρχή nem transferir sua tradução.',
        '- Aplicar a mesma distinção no painel Strong. A projeção plana perde análises adicionais; usar o índice e a fonte completa.',
        '- Etapa 2: propostas separadas por lema/Strong literal e por flexão, com IDs strong + flexao, hashes, referências e decisão humana. Nenhuma consolidação nesta etapa.', '']
    write(output / 'resumo.md', '\n'.join(lines))
    print(dump(report['resumo']))


if __name__ == '__main__':
    main()
