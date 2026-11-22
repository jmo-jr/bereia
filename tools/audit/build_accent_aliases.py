#!/usr/bin/env python3
"""Constrói a lista positiva autorizada, com equivalências por ocorrência."""
import argparse
from collections import Counter, defaultdict

from tools.audit.audit_tm import ROOT, BOOKS, align, inventory, parsing, digest, dump, nfc, read, write
from tools.audit.triage_tm import candidate_difference, classify_gap
from tools.audit.audit_accents import compare_codes, check_description, COMPATIBLE
from tools.audit.accent_alias_rules import regular_pair, target_signature
from tools.audit.accent_alias_rules import case_key

REGISTRY = 'src/_data/nt/greek_accent_aliases.json'
LEXICON = 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json'
FLAT = 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'
INDEX = 'src/_data/nt/dict_form_index_nt-lxx_greek-pt.json'


def build(report, lexicon, dictionary, index):
    rows = [r for r in report['formas'] if r['classe'] == 'ausente' and classify_gap(r) == 'agudo_grave_mesma_posicao']
    aliases, pending = [], []
    for row in rows:
        origin = row['forma_tm']
        candidates = [c for c in row['candidatos_sem_diacriticos']
                      if candidate_difference(origin, c['forma']) == 'agudo_grave_mesma_posicao']
        reason, valid_refs = None, set()
        target = candidates[0] if len(candidates) == 1 else None
        if not target or len(row['candidatos_sem_diacriticos']) != 1:
            reason = 'candidatos_concorrentes'
        elif not regular_pair(origin, target['forma']):
            reason = 'regra_grafica_nao_validada'
        else:
            flex = lexicon[target['strong']]['flexoes'][target['flexao']]
            entry = dictionary.get(target['forma'])
            expected_refs = [{'strongs': target['strong'], 'flexao': target['flexao']}]
            if not entry or entry['strongs'] != target['strong'] or index.get(target['forma']) != expected_refs:
                reason = 'destino_nao_univoco'
            elif check_description(flex['abrev_morf'], flex['morfologia']) != 'coerente':
                reason = 'descricao_ou_codigo_pendente'
            else:
                observations = defaultdict(set)
                for evidence in row['evidencias']:
                    pair = (evidence['strong_fonte'], evidence['morfologia_fonte'])
                    for ref in evidence['referencias']:
                        observations[ref].add(pair)
                for ref, pairs in observations.items():
                    if len(pairs) == 1:
                        strong, code = next(iter(pairs))
                        if strong == target['strong'] and compare_codes(flex['abrev_morf'], code) in COMPATIBLE:
                            valid_refs.add(ref)
                if valid_refs:
                    aliases.append({'id': 'acento:' + origin.encode('utf-8').hex(), 'origem': origin,
                        'destino': {'grego': target['forma'], 'strongs': target['strong'],
                                    'flexao': target['flexao'], 'assinatura': target_signature(entry)},
                        'ocorrencias_forma_tm': len(row['referencias']), 'referencias': sorted(valid_refs),
                        'tokens_validados': sum(ref in valid_refs for ref in row['referencias']),
                        'escopo': 'nt_ocorrencias_alinhadas',
                        'evidencias': [{'strong_fonte': e['strong_fonte'], 'morfologia_fonte': e['morfologia_fonte'],
                                       'referencias': sorted(set(e['referencias']) & valid_refs)}
                            for e in row['evidencias'] if any(ref in valid_refs for ref in e['referencias'])]})
                reason = 'ocorrencias_sem_prova_suficiente'
        remaining = [ref for ref in row['referencias'] if ref not in valid_refs]
        if remaining:
            pending.append({'forma_tm': origin, 'estado': 'INCERTO', 'motivo': reason,
                            'referencias': remaining, 'referencias_validadas': sorted(valid_refs)})
    return rows, aliases, pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', default='reports/audit/aliases/base/inventario.json')
    parser.add_argument('--output', default='reports/audit/aliases')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    source = ROOT / args.inventory
    report = read(source)
    # Somente fontes de evidência: alterações na consulta/registro não geram
    # dependência circular na reconstrução determinística da lista.
    evidence_paths = {p: h for p, h in report['fontes_sha256'].items()
                      if p.startswith(('src/interlinear/nt/', 'tools/tmnt/with-parsing/')) or p in {LEXICON, FLAT, INDEX}}
    for p, expected in evidence_paths.items():
        if digest(ROOT / p) != expected:
            raise ValueError(f'Inventário desatualizado: {p}')
    rows, aliases, pending = build(report, read(ROOT / LEXICON), read(ROOT / FLAT), read(ROOT / INDEX))
    # Revalidar diretamente nas fontes, inclusive quando uma referência aparece
    # em mais de uma perícope. Nenhuma cópia não alinhada herda parsing de outra.
    dictionary = read(ROOT / FLAT)
    verse_tables, parsing_tables = {}, {}
    for book in report['escopo']:
        verses = defaultdict(list)
        for verse in inventory(read(ROOT / f'src/interlinear/nt/{book}.json'), book):
            verses[(verse['chapter'], verse['verse'])].append(verse)
        verse_tables[book] = verses
        csv = ROOT / f'tools/tmnt/with-parsing/{BOOKS[book]}.csv'
        parsing_tables[book] = parsing(csv) if csv.exists() else {}
    for alias in aliases:
        verified = []
        for ref in alias['referencias']:
            book, location = ref.split(' ')
            chapter_verse, position = location.split('#')
            chapter, verse = chapter_verse.split(':')
            position = int(position) - 1
            copies = [v for v in verse_tables[book][(chapter, verse)] if position < len(v['forms']) and
                      case_key(v['forms'][position]) == case_key(alias['origem'])]
            auxiliary = parsing_tables[book].get((chapter, verse))
            if not copies or any(align(v, auxiliary) != 'alinhado' for v in copies):
                continue
            _, strong, code = auxiliary['tokens'][position]
            target = dictionary[alias['destino']['grego']]
            if strong == alias['destino']['strongs'] and compare_codes(target['abrev_morf'], code) in COMPATIBLE:
                verified.append(ref)
        alias['referencias'] = verified
        profiles = defaultdict(set)
        for evidence in alias['evidencias']:
            profiles[(evidence['strong_fonte'], evidence['morfologia_fonte'])].update(set(evidence['referencias']) & set(verified))
        alias['evidencias'] = [{'strong_fonte': strong, 'morfologia_fonte': code, 'referencias': sorted(refs)}
                              for (strong, code), refs in sorted(profiles.items()) if refs]
    aliases = [a for a in aliases if a['referencias']]
    by_origin = {a['origem']: a for a in aliases}
    previous_reasons = {p['forma_tm']: p['motivo'] for p in pending}
    pending = []
    for row in rows:
        alias = by_origin.get(row['forma_tm'])
        verified = set(alias['referencias']) if alias else set()
        if alias:
            alias['tokens_validados'] = sum(ref in verified for ref in row['referencias'])
        remaining = [ref for ref in row['referencias'] if ref not in verified]
        if remaining:
            pending.append({'forma_tm': row['forma_tm'], 'estado': 'INCERTO',
                'motivo': previous_reasons.get(row['forma_tm'], 'revalidacao_contextual_pendente'),
                'referencias': remaining, 'referencias_validadas': sorted(verified)})
    evidence_books = {}
    for book in report['escopo']:
        tm = f'src/interlinear/nt/{book}.json'
        parsing_path = f'tools/tmnt/with-parsing/{BOOKS[book]}.csv'
        evidence_books[book] = {p: evidence_paths[p] for p in (tm, parsing_path) if p in evidence_paths}
    manifest = {'schema_version': 1, 'regra': 'agudo_grave_final_contextual_v1',
        'fundamento_gramatical': {'referencia': 'Smyth, Greek Grammar, §154',
            'url': 'https://grammars.alpheios.net/smyth/xhtml/body.1_div1.1_div2.7.html',
            'limite': 'Troca final agudo/grave; demais sinais preservados. Interrogativos τίς/τί e elisões ficam fora.'},
        'autorizacao': 'Usuário autorizou a execução da estratégia de aliases validados, preservando as entradas existentes.',
        'origens_controladas': [r['forma_tm'] for r in rows], 'evidencia_por_livro': evidence_books,
        'dicionario_de_referencia_sha256': evidence_paths[LEXICON],
        'fontes_verificador_sha256': {p: digest(ROOT / p) for p in
            ('tools/audit/build_accent_aliases.py', 'tools/audit/accent_alias_rules.py', 'tools/audit/audit_accents.py',
             'tools/audit/audit_tm.py', 'tools/audit/triage_tm.py')},
        'aliases': aliases}
    for p, expected in evidence_paths.items():
        if digest(ROOT / p) != expected:
            raise ValueError(f'Fonte mudou durante a validação: {p}')
    if args.check:
        if read(ROOT / REGISTRY) != manifest:
            raise ValueError('Registro de equivalências desatualizado; reconstruir com as fontes atuais.')
        print('Lista de equivalências atual e reproduzível.')
        return
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / 'reports/audit').resolve()):
        parser.error('A saída de relatórios deve estar em reports/audit')
    output.mkdir(parents=True, exist_ok=True)
    write(ROOT / REGISTRY, dump(manifest))
    summary = {'formas_examinadas': len(rows), 'aliases_contextuais': len(aliases),
        'ocorrencias_validadas': sum(a['tokens_validados'] for a in aliases),
        'referencias_unicas_validadas': sum(len(a['referencias']) for a in aliases),
        'ocorrencias_pendentes': sum(len(p['referencias']) for p in pending),
        'formas_com_pendencias': len(pending), 'pendencias_por_motivo': dict(sorted(Counter(p['motivo'] for p in pending).items()))}
    write(output / 'validacao.json', dump({'schema_version': 1, 'resumo': summary,
        'registro': REGISTRY, 'registro_sha256': digest(ROOT / REGISTRY), 'pendencias': pending}))
    print(dump(summary))


if __name__ == '__main__':
    main()
