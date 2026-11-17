#!/usr/bin/env python3
"""Materializa a aprovação explícita das propostas AncientBible no suplemento beta."""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.lxx.generate_beta import (read, digest, descriptions, render_translation,
                                    BetaNominalInflector, POS)
from tools.lxx.inflect_beta import BetaConjugator

ADVERBS = {'ἀληθινῶς': 'verdadeiramente', 'ἀνοσίως': 'profanamente',
           'διαφόρως': 'diferentemente', 'εὐσήμως': 'inteligivelmente', 'πιστῶς': 'fielmente'}


def render_approved(record, base, conjugator, nominal):
    """Flexão portuguesa das bases aprovadas; mantém a análise grega original."""
    working = dict(record)
    parsing = working.get('parsing') or ''
    notes, mode = [], 'flexao_portuguesa'
    if record['pos'] == 'adverb' and record['lemma'] in ADVERBS:
        notes.append('Adaptação da proposta adjetiva à classe adverbial da ocorrência.')
        return ADVERBS[record['lemma']], 'adaptacao_de_classe', notes
    if record['pos'] == 'adjective' and base == 'benevolentemente':
        base = 'benevolente'
        notes.append('Adaptação do advérbio português à classe adjetiva da ocorrência.')
    if record['pos'] == 'noun' and base == 'cortesãs do templo':
        text = 'cortesãos do templo'
        if 'gen' in parsing.split():
            text = 'dos ' + text
        elif 'dat' in parsing.split():
            text = 'aos ' + text
        return text, 'concordancia_nominal', ['Masculino plural português cortesãos, conforme a análise grega; glosa original cortesãs preservada na evidência.']
    if base == 'ser usado':
        base = 'usar'
        working['parsing'] = ' '.join('pass' if token in {'act', 'mid', 'mid/pass'} else token for token in parsing.split())
        notes.append('A locução portuguesa ser usado é flexionada como passiva de usar; a voz grega original é preservada.')
    if record['pos'] == 'adjective' and base == 'chuva precoce':
        return base, 'glosa_nominal', ['Locução nominal portuguesa mantida, sem impor gênero adjetival ao substantivo chuva.']
    if parsing.startswith('futperf ind ') and base in {'clamar', 'chamar', 'gritar'}:
        tokens = parsing.split()
        auxiliary = {('1st', 'sg'): 'terei', ('2nd', 'sg'): 'terás', ('3rd', 'sg'): 'terá',
                     ('1st', 'pl'): 'teremos', ('2nd', 'pl'): 'tereis', ('3rd', 'pl'): 'terão'}
        person = tuple(tokens[-2:])
        if person in auxiliary:
            participle = conjugator._past_participle(base)
            alternatives = []
            for voice in tokens[2].split('/'):
                phrase = auxiliary[person] + (' sido ' if voice == 'pass' else ' ') + participle
                if phrase not in alternatives:
                    alternatives.append(phrase)
            return ' / '.join(alternatives), 'futuro_perfeito', ['futperf traduzido como futuro perfeito conforme a análise original; alternativas de voz preservadas.']
    comparative = 'comp' in parsing.split()
    if comparative:
        working['parsing'] = ' '.join(token for token in parsing.split() if token != 'comp')
    pt, reason = render_translation(working, base, descriptions(working), conjugator, nominal)
    if pt:
        if base == 'reunir' and pt == 'reuna':
            pt = 'reúna'
            notes.append('Acentuação objetiva da forma portuguesa reúna.')
        if comparative:
            pt = 'mais ' + pt
            notes.append('Grau comparativo preservado com mais; parsing original não alterado.')
        return pt, mode, notes
    return base, 'glosa_lexical_sem_flexao', notes + [reason + '; exibida a glosa aprovada sem inferir a flexão ausente/incompatível.']


def source_description(record):
    parsing = record.get('parsing') or ''
    if 'futperf' in parsing.split():
        working = {**record, 'parsing': parsing.replace('futperf', 'fut')}
        return ' / '.join(descriptions(working)).replace('Futuro ', 'Futuro Perfeito ')
    if 'comp' in parsing.split():
        working = {**record, 'parsing': ' '.join(token for token in parsing.split() if token != 'comp')}
        return ' / '.join(description + ' - Comparativo' for description in descriptions(working))
    return ''


def prepare(review_path, output, instruction):
    review = read(review_path)
    source = Path(review['fonte'])
    if digest(source) != review['fonte_sha256']:
        raise ValueError('A concordância aprovada mudou')
    audit_path = ROOT / 'tools/relatorios/lxx-tbesg-cobertura-etapa4.json'
    audit = read(audit_path)
    application = read(ROOT / 'tools/relatorios/lxx-beta-aplicacao.json')
    current_audit = read(ROOT / application['input_files']['audit'])
    if current_audit['records'] != audit['records']:
        raise ValueError('Auditoria atual divergente; renovar a revisão')
    supplement = read(ROOT / 'src/_data/lxx/supplement-beta.json')
    by_lemma = defaultdict(list)
    for candidate in review['com_candidato']:
        if not (candidate.get('traducao_revisada') or candidate.get('traducao_proposta_pt')):
            raise ValueError('Candidato aprovado sem tradução')
        by_lemma[candidate['termo_faltante']].append(candidate)
    result = {'schema_version': 1, 'stage': 5, 'audit_sha256': digest(audit_path),
              'scope': 'Aplicação de todos os 44 pares AncientBible aprovados explicitamente pelo usuário; alternativas conservadas. Traduções beta, sem edição do léxico ou das fontes gregas.',
              'explicit_approval': {'instruction': instruction,
                                    'review_file': str(review_path.resolve().relative_to(ROOT)),
                                    'review_sha256': digest(review_path)},
              'entries': [], 'pending': []}
    conjugator, nominal = BetaConjugator(), BetaNominalInflector()
    for record, current, provenance in zip(audit['records'], supplement['entries'], application['entries']):
        if record['lemma'] not in by_lemma or current['pt'] and provenance.get('generation_stage') != 5:
            continue
        candidates = by_lemma[record['lemma']]
        if any(record['form'] not in candidate['formas_pendentes']
               or not set(record['references']).issubset(candidate['referencias']) for candidate in candidates):
            raise ValueError('Contexto não incluído na aprovação')
        outputs, bases, details = [], [], []
        for candidate in candidates:
            base = candidate.get('traducao_revisada') or candidate['traducao_proposta_pt']
            pt, mode, notes = render_approved(record, base, conjugator, nominal)
            if pt not in outputs:
                outputs.append(pt)
            if base not in bases:
                bases.append(base)
            details.append({'review_id': candidate['id'], 'source_id': candidate['identificador_concordance'],
                            'candidate_original': candidate['candidato_concordance'],
                            'gloss_en_original': candidate['traducao_concordance'], 'approved_base_pt': base,
                            'pt': pt, 'mode': mode, 'notes': notes})
        row = {key: record[key] for key in ['form', 'lemma', 'parsing', 'pos', 'occurrences', 'references']}
        row.update(id=f'etapa5:{len(result["entries"])+1:03d}', estado='APLICAR_BETA',
                   origin='ancientbible_en_aprovado', pt=' / '.join(outputs), base_pt=' / '.join(bases),
                   allow_uncertain=True, approved_candidate_ids=[candidate['id'] for candidate in candidates],
                   classification='tradução beta aprovada explicitamente; ressalvas originais preservadas',
                   evidence=details)
        description = source_description(record)
        if description:
            row['morfologia_pt'] = description
        result['entries'].append(row)
    if len(by_lemma) != review['resumo']['lemas_com_candidato']:
        raise ValueError('Contagem de lemas aprovados divergente')
    if sum(row['occurrences'] for row in result['entries']) != review['resumo']['ocorrencias_com_candidato']:
        raise ValueError('Nem todas as ocorrências aprovadas foram selecionadas')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'groups': len(result['entries']), 'lemmas': len(by_lemma),
                      'occurrences': sum(row['occurrences'] for row in result['entries'])}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, default=ROOT / 'tools/relatorios/lxx-ancientbible-en-revisao.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'tools/lxx/reviewed_step5.json')
    parser.add_argument('--instruction', required=True, help='Instrução explícita de aprovação dada pelo usuário')
    args = parser.parse_args()
    prepare(args.review, args.output, args.instruction)
