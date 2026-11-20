#!/usr/bin/env python3
"""Auditoria local, somente leitura; biblioteca padrão Python 3.9+."""
import argparse
import csv
import hashlib
import json
import re
import unicodedata as ud
from collections import Counter, defaultdict
from pathlib import Path

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


def classify(form, indexes):
    literal, canonical, case, candidates = indexes
    if literal.get(form):
        return 'exata', literal[form]
    if canonical.get(nfc(form)):
        return 'somente_nfc', canonical[nfc(form)]
    # Caixa é separada de equivalência Unicode e não autoriza associação.
    return 'ausente', []


def audit(verses, sources, lexicon, flat, exceptions):
    indexes = index_lexicon(lexicon)
    forms = {}
    alignment = []
    legacy = {}
    for key, entry in flat.items():
        legacy.setdefault(legacy_key(key, exceptions), {'chave': key, **{k: entry.get(k) for k in ('strongs', 'grego', 'abrev_morf', 'morfologia')}})
    for verse in verses:
        aux = sources.get((verse['ref'].split()[0], verse['chapter'], verse['verse']))
        status = align(verse, aux)
        alignment.append({'ref': verse['ref'], 'estado': status})
        for pos, form in enumerate(verse['forms'], 1):
            if form not in forms:
                category, entries = classify(form, indexes)
                selected = legacy.get(legacy_key(form, exceptions))
                forms[form] = {'forma_tm': form, 'classe': category, 'referencias': [],
                               'entradas': entries,
                               'candidatos_sem_diacriticos': indexes[3].get(folded(form), []),
                               'candidatos_caixa': indexes[2].get(nfc(form.lower()), []),
                               'ambiguidades': len(entries) > 1,
                               'candidatos_multiplos': len(indexes[3].get(folded(form), [])) > 1,
                               'situacao_normalizacao': ('equivalencia_nfc' if category == 'somente_nfc' else
                                   'somente_caixa_candidata' if category == 'ausente' and indexes[2].get(nfc(form.lower())) else
                                   'somente_sem_marcas_candidata' if category == 'ausente' and indexes[3].get(folded(form)) else
                                   'sem_candidato' if category == 'ausente' else 'literal'),
                               'consulta_atual': selected, 'evidencias': {}}
            row = forms[form]
            ref = f"{verse['ref']}#{pos}"
            row['referencias'].append(ref)
            if status == 'alinhado':
                _, strong, morph = aux['tokens'][pos - 1]
                outcome = compatibility(row['entradas'], strong, morph) if row['entradas'] else 'forma_ausente'
                selected = row['consulta_atual']
                current = compatibility([{'strong': selected.get('strongs'), 'abrev_morf': selected.get('abrev_morf')}], strong, morph) if selected else 'sem_resultado'
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
    return {'resumo': {'tokens_tm': sum(len(r['referencias']) for r in rows), 'formas_tm': len(rows),
        'classes': dict(sorted(Counter(r['classe'] for r in rows).items())),
        'ausentes_com_candidatos': sum(r['classe'] == 'ausente' and bool(r['candidatos_sem_diacriticos']) for r in rows),
        'formas_com_multiplas_analises': sum(r['ambiguidades'] for r in rows),
        'formas_com_multiplos_candidatos': sum(r['candidatos_multiplos'] for r in rows),
        'ausentes_apenas_caixa': sum(r['classe'] == 'ausente' and bool(r['candidatos_caixa']) for r in rows),
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
        'gerador': 'tools/dictionary/generate.js', 'core': 'tools/dictionary/core.js',
        'strong_archive': 'src/_data/archive/strongsg.js',
        'tbesg': 'tools/lxx/fontes/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt',
        'strong_pt_legado': 'src/_data/strongs_greek_pt_defs.json',
        'auditor': 'tools/audit/audit_tm.py'}.items()}
    verses, sources = [], {}
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
    report = audit(verses, sources, lexicon, flat, exceptions_from(paths['consulta'].read_text(encoding='utf-8')))
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
        'ausente': 'Sem flexão literal/NFC; candidatos por caixa ou marcas não são correspondências.',
        'ambiguidades': 'Múltiplas entradas literais/NFC preservadas; não são erros por si só.',
        'evidencia': 'CSV local alinhado por versículo inteiro; grafia sem diacríticos não prova identidade morfológica.',
        'morfologia': 'Código idêntico ou mapeamento explícito N-caso-número-gênero → S-caso-gênero-número. Demais convenções: não comparável.',
        'inconsistencias': 'Divergências entre fontes, sujeitas a revisão; sem correção automática.',
        'contagens': 'Comparações contam grupos forma/Strong/parsing/resultado, não tokens. Referências usam token iniciado em 1.',
        'incremental': 'Cache por livro e SHA256; relatório completo recalculado. --books restringe explicitamente o escopo.'}
    # As fontes não podem mudar durante a execução.
    if any(not (ROOT / p).exists() or digest(ROOT / p) != h for p, h in manifest.items()):
        raise RuntimeError('Fonte mudou durante a execução; repetir auditoria.')
    write(output / 'inventario.json', dump(report))
    issues = [r for r in report['formas'] if any(e['comparacao_exata_nfc'] in {'strong_divergente', 'morfologia_divergente'} or e['comparacao_consulta_atual'] in {'strong_divergente', 'morfologia_divergente'} for e in r['evidencias'])]
    write(output / 'inconsistencias.json', dump({'schema_version': VERSION, 'formas': issues}))
    case = [r for r in report['formas'] if nfc(r['forma_tm'].lower()) in {'ἀρχῇ', 'ἀρχή', 'ἀρχὴ'}]
    write(output / 'caso-arche.json', dump({'schema_version': VERSION, 'formas': case, 'grupo_746': lexicon.get('746')}))
    lines = ['# Auditoria do TM — etapa 1', '', f"Escopo: {', '.join(report['escopo'])}.", '',
        'Dados originais preservados. Hashes, critérios e referências em inventario.json.', '',
        *[f'- {k}: {json.dumps(v, ensure_ascii=False)}' for k, v in report['resumo'].items()],
        f'- Fontes referenciadas ausentes: {missing_sources}.',
        f'- Produtos derivados: {json.dumps(report["produtos"], ensure_ascii=False)}',
        f'- Formas com divergências nas fontes ou na consulta atual: {len(issues)}.', '',
        '## Caso ἀρχῇ / ἀρχή', '',
        'A consulta atual remove marcas e seleciona a primeira entrada da chave αρχη. '
        'O grupo 746 contém ἀρχή (S-NFS), mas não ἀρχῇ. Em JO 1:1#2 e JO 1:2#4, '
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
        '- Incluir futuramente ἀρχῇ como flexão própria após revisão humana da evidência; não renomear ἀρχή nem transferir sua tradução.',
        '- Aplicar a mesma distinção no painel Strong. A projeção plana perde análises adicionais; usar o índice e a fonte completa.',
        '- Etapa 2: propostas separadas por lema/Strong literal e por flexão, com IDs strong + flexao, hashes, referências e decisão humana. Nenhuma consolidação nesta etapa.', '']
    write(output / 'resumo.md', '\n'.join(lines))
    print(dump(report['resumo']))


if __name__ == '__main__':
    main()
