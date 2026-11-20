#!/usr/bin/env python3
"""Revisão estrutural de agudo/grave. Propostas somente; nenhuma escrita no léxico.

Executar: python3 -B -m tools.audit.audit_accents
"""
import argparse
import copy
import re
import unicodedata as ud
from collections import Counter
from pathlib import Path

from tools.audit.audit_tm import ROOT, digest, dump, nfc, read, write
from tools.audit.triage_tm import candidate_difference, classify_gap, verify_sources
from tools.update_interlinear_translit import transliterate

VERSION = 1
LEXICON = 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json'
COMPATIBLE = {'identico', 'compativel', 'compativel_nom_acus_neutro'}
INVARIABLE = {'Adv': ('ADV', 'Advérbio'), 'Prep': ('PREP', 'Preposição'),
              'Conj': ('CONJ', 'Conjunção'), 'Prtcl': ('PRT', 'Partícula')}
CASES = dict(zip('NGDAV', ('nominativo', 'genitivo', 'dativo', 'acusativo', 'vocativo')))
GENDERS = dict(zip('MFN', ('masculino', 'feminino', 'neutro')))
NUMBERS = {'S': 'singular', 'P': 'plural'}


def morphology(code, source=False):
    """Adaptador explícito. Convenções não documentadas aqui ficam pendentes."""
    nominal = (r'(N|A)-([NGDAV])([SP])([MFN])' if source else
               r'(S|Adj)-([NGDAV])([MFN])([SP])')
    match = re.fullmatch(nominal, code or '')
    if match:
        kind, case, a, b = match.groups()
        number, gender = (a, b) if source else (b, a)
        return {'classe': {'N': 'S', 'A': 'Adj'}.get(kind, kind),
                'caso': case, 'genero': gender, 'numero': number}
    if source:
        for local, (external, _) in INVARIABLE.items():
            if code == external:
                return {'classe': local}
    elif code in INVARIABLE:
        return {'classe': code}
    # BEREIA: tempo, modo, voz; Robinson: tempo, voz, modo.
    # O prefixo 2 é mantido como detalhe da fonte, sem inventar um segundo
    # paradigma no código local. Vozes deponentes O/D/N não são equiparadas.
    verb = (r'V-(2[AR]|[PIFARL])([AMPE])([ISOMNP])(?:-([123][SP]|[NGDAV][SP][MFN]))?' if source else
            r'V-([PIFARL])([ISOMNP])([AMPE])(?:-([123][SP]|[NGDAV][MFN][SP]))?')
    match = re.fullmatch(verb, code or '')
    if not match:
        return None
    tense, a, b, ending = match.groups()
    mood, voice = (b, a) if source else (a, b)
    result = {'classe': 'V', 'tempo': tense.lstrip('2'), 'modo': mood, 'voz': voice}
    if mood == 'N':
        return result if ending is None else None
    if ending is None:
        return None
    if mood == 'P' and re.fullmatch(r'[NGDAV][SP][MFN]' if source else r'[NGDAV][MFN][SP]', ending):
        case, a, b = ending
        number, gender = (a, b) if source else (b, a)
        result.update(caso=case, genero=gender, numero=number)
    elif mood != 'P' and re.fullmatch(r'[123][SP]', ending):
        result.update(pessoa=ending[0], numero=ending[1])
    else:
        return None
    return result


def compare_codes(local, external):
    if local == external:
        return 'identico'
    a, b = morphology(local), morphology(external, source=True)
    if a is None or b is None:
        return 'nao_comparavel'
    if a == b:
        return 'compativel'
    # Não transformar o sincretismo neutro nominativo/acusativo em pendência
    # independente; a ausência gráfica continua sendo o objeto do relatório.
    if (a.get('genero') == b.get('genero') == 'N' and
            {a.get('caso'), b.get('caso')} == {'N', 'A'} and
            {k: v for k, v in a.items() if k != 'caso'} ==
            {k: v for k, v in b.items() if k != 'caso'}):
        return 'compativel_nom_acus_neutro'
    return 'divergente'


def check_description(code, description):
    features = morphology(code)
    if features is None:
        return 'nao_comparavel'
    text = (description or '').lower()
    def found(words):
        pattern = r'(?<!\w)(?:' + '|'.join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r')(?!\w)'
        return set(re.findall(pattern, text))
    expected = []
    if features['classe'] in {'S', 'Adj'}:
        expected.append('substantivo' if features['classe'] == 'S' else 'adjetivo')
    elif features['classe'] in INVARIABLE:
        expected.append(INVARIABLE[features['classe']][1].lower())
    elif features['classe'] == 'V':
        tenses = {'P': 'presente', 'I': 'imperfeito', 'F': 'futuro', 'A': 'aoristo', 'R': 'perfeito', 'L': 'mais-que-perfeito'}
        moods = {'I': 'indicativo', 'S': 'subjuntivo', 'O': 'optativo', 'M': 'imperativo', 'N': 'infinitivo', 'P': 'particípio'}
        voices = {'ativa': 'A', 'ativo': 'A', 'média': 'M', 'médio': 'M', 'passiva': 'P', 'passivo': 'P'}
        voice = {'M', 'P'} if features['voz'] == 'E' else {features['voz']}
        if (found(tenses.values()) != {tenses[features['tempo']]} or
                found(moods.values()) != {moods[features['modo']]} or
                {voices[w] for w in found(voices)} != voice):
            return 'revisar_descricao'
        expected.append('verbo')
    for key, words in [('caso', CASES), ('genero', GENDERS), ('numero', NUMBERS)]:
        if key in features:
            expected_values = {words[features[key]]}
            observed = found(words.values())
            if key == 'caso' and features.get('genero') == 'N' and features[key] in {'N', 'A'} and observed == {'nominativo', 'acusativo'}:
                continue
            if observed != expected_values:
                return 'revisar_descricao'
    if 'pessoa' in features and not re.search(r'\b' + features['pessoa'] + r'(?:ª|º)?\s+pessoa\b', text):
        return 'revisar_descricao'
    return 'coerente' if all(found([word]) for word in expected) else 'revisar_descricao'


def collect_lxx(forms):
    """Inventário de grafias literalmente/NFC iguais, sem atribuir Strong."""
    targets = {nfc(f) for f in forms}
    result, hashes = {f: [] for f in targets}, {}
    for path in sorted((ROOT / 'src/interlinear/at').glob('*.json')):
        hashes[str(path.relative_to(ROOT))] = digest(path)
        for chapter in read(path):
            verses = ([v for p in chapter['pericopes'] for v in p['verses']]
                      if chapter.get('pericopes') else chapter.get('verses', []))
            for verse in verses:
                for position, token in enumerate(verse['tokens'], 1):
                    form = nfc(token['lemma'])
                    if form in targets:
                        result[form].append(f"{path.name} {chapter['chapter']}:{verse['verse']}#{position}")
    return result, hashes


def review(row, lexicon, lxx):
    form = row['forma_tm']
    candidates = [c for c in row['candidatos_sem_diacriticos']
                  if candidate_difference(form, c['forma']) == 'agudo_grave_mesma_posicao']
    source_refs = {ref for e in row['evidencias'] for ref in e['referencias']}
    unaligned = sorted(set(row['referencias']) - source_refs)
    evaluations = []
    for candidate in candidates:
        strong, index = candidate['strong'], candidate['flexao']
        original = lexicon[strong]['flexoes'][index]
        if original['grego'] != candidate['forma']:
            raise ValueError(f'Candidato desatualizado: {strong}/{index}')
        evidence = []
        for observed in row['evidencias']:
            outcome = ('strong_divergente' if strong != observed['strong_fonte'] else
                       compare_codes(original.get('abrev_morf'), observed['morfologia_fonte']))
            evidence.append({'resultado': outcome, 'strong_fonte': observed['strong_fonte'],
                             'codigo_fonte': observed['morfologia_fonte'],
                             'referencias': observed['referencias']})
        evaluations.append({'strong': strong, 'flexao': index, 'forma': original['grego'],
            'diferenca_adicional_de_caixa': ud.normalize('NFD', form).replace('\u0300', '\u0301') !=
                ud.normalize('NFD', original['grego']).replace('\u0300', '\u0301'),
            'campos_atuais': original, 'descricao': check_description(original.get('abrev_morf'), original.get('morfologia')),
            'comparacoes': evidence})
    outcomes = {e['resultado'] for c in evaluations for e in c['comparacoes']}
    extra = [c for c in row['candidatos_sem_diacriticos'] if c not in candidates]
    flags = []
    for condition, name in [
        (len(candidates) != 1, 'multiplos_candidatos_agudo_grave'),
        (bool(extra), 'outros_candidatos_sem_marcas'),
        (not source_refs, 'sem_parsing_alinhado'),
        (bool(unaligned), 'cobertura_parcial_do_parsing'),
        ('strong_divergente' in outcomes, 'strong_divergente'),
        ('divergente' in outcomes, 'morfologia_divergente'),
        ('nao_comparavel' in outcomes, 'morfologia_nao_comparavel'),
        (any(c['descricao'] != 'coerente' for c in evaluations), 'descricao_a_revisar')]:
        if condition:
            flags.append(name)
    priority = ['sem_parsing_alinhado', 'strong_divergente', 'morfologia_divergente',
                'morfologia_nao_comparavel', 'descricao_a_revisar',
                'multiplos_candidatos_agudo_grave', 'outros_candidatos_sem_marcas',
                'cobertura_parcial_do_parsing']
    group = next((name for name in priority if name in flags), 'evidencia_consistente')
    status = 'SUGERIR' if not flags else 'INCERTO'
    draft = None
    if status == 'SUGERIR':
        draft = copy.deepcopy(evaluations[0]['campos_atuais'])
        draft.update(grego=form, transliteracao=transliterate(form),
                     ocorrencias=str(len(row['referencias'])), lxx=[], ocorrencias_lxx=len(lxx))
    return {'id': 'agudo-grave:' + form.encode('utf-8').hex(), 'forma_tm': form,
            'estado': status, 'decisao': 'pendente', 'aplicado': False,
            'categoria': 'dependente_de_contexto' if status == 'SUGERIR' else 'informacao_insuficiente',
            'grupo': group, 'sinais': flags, 'ocorrencias_nt': len(row['referencias']),
            'referencias_tm': row['referencias'], 'referencias_sem_parsing_alinhado': unaligned,
            'candidatos': evaluations, 'outros_candidatos': extra,
            'referencias_lxx_literal_nfc': lxx,
            'minuta_inclusao': draft,
            'limite': 'Minuta copia as glosas do candidato apenas para revisão humana; não comprova equivalência lexical nem atribui sentido contextual.'}


def build(rows, lexicon, lxx):
    selected = [r for r in rows if r['classe'] == 'ausente' and classify_gap(r) == 'agudo_grave_mesma_posicao']
    return [review(r, lexicon, lxx.get(nfc(r['forma_tm']), [])) for r in selected]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inventory', default='reports/audit/tm/inventario.json')
    ap.add_argument('--output', default='reports/audit/agudo-grave')
    args = ap.parse_args()
    source = (ROOT / args.inventory).resolve()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / 'reports/audit').resolve()):
        ap.error('--output deve estar em reports/audit')
    report = read(source)
    verify_sources(report)
    source_hash = digest(source)
    targets = [r['forma_tm'] for r in report['formas'] if r['classe'] == 'ausente' and classify_gap(r) == 'agudo_grave_mesma_posicao']
    lxx, lxx_hashes = collect_lxx(targets)
    rows = build(report['formas'], read(ROOT / LEXICON), lxx)
    summary = {'formas': len(rows), 'tokens_nt': sum(r['ocorrencias_nt'] for r in rows),
               'estados': dict(sorted(Counter(r['estado'] for r in rows).items())),
               'grupos': dict(sorted(Counter(r['grupo'] for r in rows).items())),
               'sinais_sobrepostos': dict(sorted(Counter(f for r in rows for f in r['sinais']).items())),
               'com_parsing_integral': sum(not r['referencias_sem_parsing_alinhado'] for r in rows)}
    summary['tokens_das_sugestoes'] = sum(r['ocorrencias_nt'] for r in rows if r['estado'] == 'SUGERIR')
    implementation = ['tools/audit/audit_accents.py', 'tools/audit/triage_tm.py',
                      'tools/audit/audit_tm.py', 'tools/update_interlinear_translit.py']
    manifest = {**report['fontes_sha256'], **lxx_hashes,
                **{p: digest(ROOT / p) for p in implementation}}
    verify_sources(report)
    if digest(source) != source_hash or any(digest(ROOT / p) != h for p, h in manifest.items()):
        raise ValueError('Fontes mudaram durante a execução; repetir revisão.')
    data = {'schema_version': VERSION, 'escopo': report['escopo'], 'inventario_sha256': source_hash,
            'fontes_sha256': manifest, 'resumo': summary,
            'criterios': {
                'graficos': 'Somente troca agudo/grave na mesma posição, admitindo diferença de caixa; espíritos, trema e iota preservados.',
                'parsing': 'Versículo inteiro alinhado pela etapa 1; sem atribuições nas referências não alinhadas.',
                'adaptadores': 'Substantivos/adjetivos simples; classes invariáveis explícitas; verbos simples com voz explícita A/M/P/E. Prefixos 2A/2R são detalhes da fonte, não apagados dos códigos originais. Deponentes e combinações permanecem não comparáveis.',
                'sugerir': 'Um candidato, todas as ocorrências alinhadas e compatíveis, descrição coerente, sem outros candidatos por marcas. Glosas copiadas somente na minuta para aprovação.',
                'incerto': 'Evidência ausente/parcial, divergência entre fontes, convenção não comparável ou candidatos adicionais. Não implica erro objetivo.',
                'aplicacao': 'Nenhuma; SUGERIR e INCERTO permanecem pendentes. Não há aliases nem aplicador.',
                'sincretismo': 'Neutro nominativo/acusativo com mesmas demais características não cria pendência morfológica própria; a lacuna gráfica é independente.'},
            'itens': rows}
    output.mkdir(parents=True, exist_ok=True)
    write(output / 'revisao.json', dump(data))
    lines = ['# Revisão do lote agudo/grave', '', f"Escopo: {', '.join(report['escopo'])}.", '',
             *[f'- {k}: {v}.' for k, v in summary.items()], '',
             'Nenhum dado original alterado. As minutas dependem de aprovação lexical; consistência morfológica não basta para copiar glosas automaticamente.', '',
             'SUGERIR indica evidência estrutural consistente em todas as ocorrências. INCERTO reúne lacunas e divergências, sem declarar erro objetivo.', '',
             'Códigos completos e referências por evidência em revisao.json; as descrições e glosas anteriores permanecem nos candidatos.', '',
             'Reprodução: `python3 -B -m tools.audit.audit_accents`.', '']
    write(output / 'resumo.md', '\n'.join(lines))
    for status, filename in [('SUGERIR', 'sugestoes.md'), ('INCERTO', 'incertos.md')]:
        entries = [r for r in rows if r['estado'] == status]
        details = [f'# {status} — agudo/grave', '', 'Todas as inclusões permanecem pendentes; nenhum original foi alterado.', '']
        for item in entries:
            candidate = item['candidatos'][0] if item['candidatos'] else None
            descriptor = (f"{candidate['forma']} (Strong literal {candidate['strong']!r}, flexão {candidate['flexao']}, {candidate['campos_atuais'].get('abrev_morf')})" if candidate else 'sem candidato único')
            draft = item['minuta_inclusao']
            proposal_text = (f" Minuta: traducao={draft['traducao']!r}; pt={draft['pt']!r}." if draft else '')
            noun = 'ocorrência' if item['ocorrencias_nt'] == 1 else 'ocorrências'
            details.append(f"- **{item['forma_tm']}** → candidato {descriptor}. {item['ocorrencias_nt']} {noun}. Grupo: {item['grupo']}. Referências: {', '.join(item['referencias_tm'])}.{proposal_text}")
            details.append('')
        write(output / filename, '\n'.join(details))
    attention = ['# Divergências que impedem inclusão direta', '',
                 'Divergência entre candidato e parsing não comprova erro. Pode revelar homógrafos, análises contextuais diferentes ou uma fonte auxiliar inconsistente. Nenhuma decisão lexical foi aplicada.', '']
    for item in rows:
        conflicts = [(c, e) for c in item['candidatos'] for e in c['comparacoes']
                     if e['resultado'] in {'strong_divergente', 'divergente'}]
        if not conflicts:
            continue
        for candidate, observed in conflicts:
            attention.append(f"- **{item['forma_tm']}**: candidato {candidate['forma']} — Strong {candidate['strong']!r}, {candidate['campos_atuais']['abrev_morf']}; fonte alinhada — Strong {observed['strong_fonte']!r}, {observed['codigo_fonte']}. Referências: {', '.join(observed['referencias'])}. Estado: INCERTO.")
            attention.append('')
    write(output / 'divergencias.md', '\n'.join(attention))
    print(dump(summary))


if __name__ == '__main__':
    main()
