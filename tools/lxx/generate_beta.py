#!/usr/bin/env python3
"""Gera suplemento beta por ocorrência; não escreve no dicionário aprovado."""
import argparse
import csv
import hashlib
import itertools
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.update_interlinear_translit import transliterate
from tools.flexiona_verbos import PortugueseConjugator, build_translation_value, strip_subject_pronoun
from tools.flexiona_nao_verbos import PortugueseNominalInflector
from tools.lxx.inflect_beta import BetaConjugator

def read(file):
    return json.loads(Path(file).read_text(encoding='utf-8'))

def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()

def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c)).replace('ς', 'σ')

def form_key(text):
    return re.sub("['’᾿ʼ]", "'", norm(text))

def load_aliases(path, source_hash):
    if not path:
        return {'entries': {}}
    aliases = read(path)
    source = next((ROOT / 'tools/lxx/fontes').glob('TBESG*'))
    if aliases['source_sha256'] != source_hash or digest(source) != source_hash:
        raise ValueError('Correspondências pertencem a outra versão TBESG')
    fields = ['eStrong', 'dStrong', 'uStrong', 'greek', 'transliteration', 'morph', 'gloss', 'meaning']
    rows = {}
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        columns = line.split('\t')
        if len(columns) >= 8 and re.fullmatch(r'G\d+', columns[0]):
            rows[columns[0]] = dict(zip(fields, columns[:8]))
    for alias in aliases['entries'].values():
        if rows.get(alias['source_id']) != alias['source_entry']:
            raise ValueError('Evidência da correspondência diverge da fonte TBESG')
        if 'proper noun' in alias['allowed_pos']:
            raise ValueError('Correspondências lexicais não substituem nomes próprios')
    return aliases

def load_reviewed(path, report_path, report):
    """Decisões editoriais limitadas às formas, análises e referências revisadas."""
    if not path:
        return {}, {}
    reviewed = read(path)
    if reviewed['audit_sha256'] != digest(report_path):
        raise ValueError('Revisão editorial pertence a outra auditoria')
    fields = ['form', 'lemma', 'parsing', 'pos']
    records = {tuple(row.get(field) for field in fields): row for row in report['records']}
    decisions, deferred = {}, {}
    approval = reviewed.get('explicit_approval')
    approved_candidates = {}
    if approval:
        approved_path = ROOT / approval['review_file']
        if not approval.get('instruction') or digest(approved_path) != approval['review_sha256']:
            raise ValueError('Aprovação explícita não corresponde ao arquivo revisado')
        approved_candidates = {row['id']: row for row in read(approved_path)['com_candidato']}
    for row in reviewed['entries'] + reviewed.get('pending', []):
        key = tuple(row.get(field) for field in fields)
        record = records.get(key)
        if key in decisions or key in deferred:
            raise ValueError('Decisão editorial duplicada')
        if record is None or row['references'] != record['references'] or row['occurrences'] != record['occurrences']:
            raise ValueError('Ocorrências da revisão editorial divergiram; revisar os contextos novamente')
        if row['estado'] == 'APLICAR_BETA':
            if record['pos'] == 'proper noun' or not row.get('pt') or not row.get('evidence'):
                raise ValueError('Decisão editorial sem tradução/evidência ou aplicada a nome próprio')
            if row.get('allow_uncertain'):
                identifiers = row.get('approved_candidate_ids', [])
                if not identifiers or any(identifier not in approved_candidates
                    or approved_candidates[identifier]['termo_faltante'] != record['lemma'] for identifier in identifiers):
                    raise ValueError('Liberação de INCERTO exige aprovação explícita dos candidatos deste lema')
            decisions[key] = row
        elif row['estado'] == 'INCERTO':
            deferred[key] = row
        else:
            raise ValueError('Estado editorial inválido')
    return decisions, deferred

WORDS = {'pres': 'Presente', 'aor': 'Aoristo', 'imperf': 'Imperfeito', 'perf': 'Perfeito',
         'plup': 'Pluperfeito', 'fut': 'Futuro', 'ind': 'Indicativo', 'subj': 'Subjuntivo',
         'opt': 'Optativo', 'imperat': 'Imperativo', 'inf': 'Infinitivo', 'part': 'Particípio',
         'ptc': 'Particípio', 'act': 'Ativa', 'mid': 'Média', 'pass': 'Passiva', 'masc': 'Masculino',
         'fem': 'Feminino', 'neut': 'Neutro', 'nom': 'Nominativo', 'acc': 'Acusativo',
         'gen': 'Genitivo', 'dat': 'Dativo', 'voc': 'Vocativo', 'sg': 'Singular', 'pl': 'Plural',
         '1st': '1ª Pessoa', '2nd': '2ª Pessoa', '3rd': '3ª Pessoa'}
POS = {'noun': 'Substantivo', 'proper noun': 'Nome próprio', 'adjective': 'Adjetivo',
       'verb': 'Verbo', 'adverb': 'Advérbio', 'preposition': 'Preposição', 'conjunction': 'Conjunção',
       'pronoun': 'Pronome', 'article': 'Artigo', 'numeral': 'Numeral', 'particle': 'Partícula',
       'interjection': 'Interjeição', 'participle': 'Verbo'}

# Ajustes editoriais somente do suplemento, sem reescrever o dicionário existente.
BASE_OVERRIDES = {'ενυπνιον': 'sonho', 'απαιρω': 'partir', 'χιλιασ': 'mil'}
POS_CODES = {'noun': 'S', 'proper noun': 'NP', 'adjective': 'Adj', 'verb': 'V',
             'adverb': 'Adv', 'preposition': 'Prep', 'conjunction': 'Conj',
             'pronoun': 'Pron', 'article': 'Art', 'numeral': 'Num', 'particle': 'Part', 'interjection': 'Intj', 'participle': 'V'}

class BetaNominalInflector(PortugueseNominalInflector):
    @staticmethod
    def noun_gender(word):
        if word.lower() == 'levita':
            return 'masculino'
        return PortugueseNominalInflector.noun_gender(word)

    def _to_plural(self, word):
        return {'mil': 'mil', 'deus': 'deuses'}.get(word, super()._to_plural(word))

    def _inflect_phrase(self, phrase, gender, number):
        words = phrase.split()
        if len(words) > 1 and all(word.endswith(('ésimo', 'écimo', 'sétimo', 'oitavo', 'nono', 'terceiro', 'quarto', 'quinto', 'sexto')) for word in words):
            return ' '.join(super(BetaNominalInflector, self)._inflect_phrase(word, gender, number) for word in words)
        return super()._inflect_phrase(phrase, gender, number)

def descriptions(record):
    tokens = (record.get('parsing') or '').split()
    options = [token.split('/') for token in tokens]
    if any(not all(option in WORDS for option in group) for group in options):
        return []
    if len(list(itertools.product(*options))) > 24:
        return []
    variants = list(itertools.product(*options)) if tokens else [()]
    if '1st/3rd' in tokens and 'sg/pl' in tokens:
        pi, ni = tokens.index('1st/3rd'), tokens.index('sg/pl')
        variants = [variant for variant in variants if (variant[pi], variant[ni]) in {('1st', 'sg'), ('3rd', 'pl')}]
    result = []
    for variant in variants[:24]:
        if any(token not in WORDS for token in variant):
            continue
        values = [WORDS[token] for token in variant]
        pos = POS.get(record['pos'], '')
        if pos == 'Verbo':
            core = [v for t, v in zip(variant, values) if t in {'pres','aor','imperf','perf','plup','fut','ind','subj','opt','imperat','inf','part','ptc','act','mid','pass'}]
            tail = [v for t, v in zip(variant, values) if t not in {'pres','aor','imperf','perf','plup','fut','ind','subj','opt','imperat','inf','part','ptc','act','mid','pass'}]
            result.append('Verbo - ' + ' '.join(core) + (' - ' + ' '.join(tail) if tail else ''))
        else:
            result.append(pos + (' - ' + ' '.join(values) if values else ''))
    return list(dict.fromkeys(result))

def short_base(text):
    text = re.sub(r'<[^>]+>', '', text or '')
    text = re.sub(r'^G\d+\s*:\s*', '', text).strip()
    text = re.split(r'[,;\n]', text)[0].strip().rstrip('.')
    if not text or len(text) > 65 or any(c in text for c in ':[]()='):
        return ''
    if text.lower().startswith(('lit.', 'literalmente', 'nome ', 'o termo ', 'o tradutor ')):
        return ''
    return text

def render_translation(record, base, descriptions_pt, conjugator, nominal):
    if not base:
        return '', 'Sem base portuguesa adequada'
    if not descriptions_pt:
        return '', 'Análise original não reconhecida; flexão não inferida'
    outputs = []
    for description in descriptions_pt:
        if record['pos'] in {'verb', 'participle'}:
            morph = conjugator.morph_parser.parse(description)
            lemma = conjugator._extract_lemma(base)
            if not lemma or lemma.start != 0:
                return '', 'Base não reconhecida como infinitivo português'
            if not morph.tense or not morph.mood or not morph.voice:
                return '', 'Análise verbal incompleta'
            if morph.is_finite or morph.mood == 'optativo':
                if not morph.person or not morph.number:
                    return '', 'Pessoa ou número verbal ausente'
            rendered = build_translation_value({'verbete': base, 'morfologia': description}, conjugator)
            text = strip_subject_pronoun((rendered or '').split(',', 1)[0].strip())
            if morph.is_finite and text == base:
                return '', 'Conjugação verbal não produzida'
        elif record['pos'] in {'noun', 'adjective', 'article', 'numeral'}:
            morph = nominal.parser.parse(description)
            invariant_phrase = record['pos'] == 'adjective' and base.split()[0] in {'de', 'do', 'da', 'sem', 'com', 'não', 'em'}
            cardinal = record['pos'] == 'numeral' and not base.split()[0].endswith(('ésimo', 'écimo', 'oitavo', 'sétimo', 'quarto', 'terceiro', 'segundo', 'primeiro', 'quinto', 'sexto', 'nono'))
            if invariant_phrase:
                text = base
            elif cardinal:
                prefix = {'genitivo': 'de ', 'dativo': 'a '}.get(morph.case, '')
                text = prefix + base
            else:
                values = nominal.expand_forms(base, morph)
                text = values[0] if values else ''
        else:
            text = base
        if text and text not in outputs:
            outputs.append(text)
    return ' / '.join(outputs), '' if outputs else 'Flexão portuguesa não produzida'

def load_previous():
    output = ROOT / 'src/_data/lxx/supplement-beta.json'
    application = ROOT / 'tools/relatorios/lxx-beta-aplicacao.json'
    if not output.exists() or not application.exists():
        return {}, {}, None
    supplement, applied = read(output), read(application)
    audit_path = ROOT / applied.get('input_files', {}).get('audit', 'tools/relatorios/lxx-tbesg-cobertura-beta.json')
    if digest(audit_path) != applied['input_hashes']['audit']:
        raise ValueError('Auditoria anterior diverge do suplemento aplicado')
    audit = read(audit_path)
    if not len(audit['records']) == len(supplement['entries']) == len(applied['entries']):
        raise ValueError('Listas do suplemento anterior desalinhadas')
    previous = {}
    stage2_file = ROOT / 'tools/relatorios/lxx-beta-etapa2.json'
    stage2_groups = set()
    if 'bases' in applied['input_hashes'] and stage2_file.exists():
        stage2_groups = {(row['form'], row['lemma'], row['parsing'], row.get('pos')) for row in read(stage2_file)['changes']}
    for row, entry, provenance in zip(audit['records'], supplement['entries'], applied['entries']):
        if entry['forma'] != row['form'] or provenance['form'] != row['form']:
            raise ValueError('Formas do suplemento anterior desalinhadas')
        key = tuple(row.get(field) for field in ['form', 'lemma', 'parsing', 'pos'])
        provenance = dict(provenance)
        identity = (row['form'], row['lemma'], row['parsing'], row['pos'])
        legacy_identity = (row['form'], row['lemma'], row['parsing'], None)
        if identity in stage2_groups or row['pos'] != 'proper noun' and legacy_identity in stage2_groups:
            provenance['generation_stage'] = 2
        previous[key] = (entry, provenance)
    return previous, applied, digest(output)

def generate(originals, report_path=None, bases_path=None, aliases_path=None, stage=2, reviewed_path=None):
    report_path = report_path or ROOT / 'tools/relatorios/lxx-tbesg-cobertura.json'
    report = read(report_path)
    dictionary_path = ROOT / 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'
    if digest(dictionary_path) != report['source']['dictionary_sha256']:
        raise ValueError('Dicionário derivado mudou: atualize a auditoria TBESG antes de gerar o suplemento.')
    lexical = read(ROOT / 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json')
    local_path = ROOT / 'src/_data/lxx/lexico_lxx_gr-pt-heb.json'
    local = read(local_path)
    gloss_path = Path(__file__).with_name('beta_glosses.json')
    glosses = read(gloss_path)
    by_line = {entry['line']: entry for entry in report['lexicon']}
    by_lemma = defaultdict(list)
    for strong, entry in lexical.items():
        if entry.get('lema'):
            by_lemma[norm(entry['lema'])].append((strong, entry))
    local_heads = defaultdict(list)
    for group, entries in local.items():
        if not isinstance(entries, dict):
            continue
        for key, entry in entries.items():
            if isinstance(entry, dict) and isinstance(entry.get('def'), str):
                local_heads[norm(key)].append((f'{group}/{key}', entry))
    registry = read(bases_path) if bases_path else {'entries': {}}
    aliases = load_aliases(aliases_path, report['source']['sha256'])
    reviewed, deferred = load_reviewed(reviewed_path, report_path, report)
    if bases_path and registry['source']['sha256'] != report['source']['sha256']:
        raise ValueError('Cadastro de bases corresponde a outra versão TBESG')
    previous, previous_application, previous_hash = load_previous()
    conjugator = BetaConjugator()
    nominal = BetaNominalInflector()
    prepared, provenance, pending = [], [], []
    record_index = {}
    counts = Counter()
    changes = []
    for record in report['records']:
        base, origin, source_id, direct = '', '', '', None
        selected = None
        if record['status'].endswith('_single'):
            selected = by_line[record['candidate_lines'][0]]
        registered = registry['entries'].get(selected['dStrong'].split()[0]) if selected and record['pos'] != 'proper noun' else None
        if registered and (registered['lema'] != selected['greek'] or registered['dStrong'] != selected['dStrong']):
            raise ValueError('Base lexical diverge do verbete TBESG selecionado')
        own = lexical.get(str(int(selected['eStrong'][1:]))) if selected else None
        if not own:
            matches = by_lemma.get(norm(record['lemma'] or ''), [])
            if len(matches) == 1:
                source_id, own = matches[0]
        if own:
            variants = [f for f in own.get('flexoes', []) if form_key(f.get('grego', '')) == form_key(record['form']) and f.get('pt')]
            if variants and len({f['pt'] for f in variants}) == 1:
                direct = variants[0]['pt']
            verbete = own.get('verbete') or next((f.get('verbete') for f in own.get('flexoes', []) if f.get('verbete')), '')
            base = short_base(verbete)
            if base:
                origin = 'bereia_lema'
                source_id = selected['eStrong'] if selected else source_id
        # Definição portuguesa local só se o lema coincide; nunca procurar pelas flexões.
        if not base and selected and selected['gloss'] in glosses:
            base, origin, source_id = glosses[selected['gloss']], 'tbesg_gloss_pt', selected['eStrong']
        if not base:
            matches = local_heads.get(norm(record['lemma'] or ''), [])
            bases = {short_base(e['def']) for _, e in matches} - {''}
            if len(bases) == 1:
                base, origin = bases.pop(), 'lexico_local_lema'
                source_id = '|'.join(key for key, _ in matches)
        if record['pos'] == 'proper noun':
            # Sem identificação segura, transliterar o nome, sem traduzi-lo como substantivo comum.
            if not base or not base[0].isupper():
                base, origin, source_id = transliterate(record['form']), 'nome_transliterado', ''
        if norm(record['lemma'] or '') in BASE_OVERRIDES:
            base = BASE_OVERRIDES[norm(record['lemma'])]
            direct = None
            origin = 'ajuste_editorial_beta'
        blocked = registered is not None and (registered['estado'] != 'BASE_BETA' or not registered['base_pt'])
        if registered:
            direct = None
            base = '' if blocked else registered['base_pt']
            origin, source_id = 'tbesg_base_por_id', selected['dStrong'].split()[0]
        alias = aliases['entries'].get(record['lemma'])
        if alias and record['pos'] in alias['allowed_pos'] and not blocked:
            base, direct = alias['base_pt'], None
            origin, source_id = 'tbesg_correspondencia_revisada', alias['source_id']
        descriptions_pt = descriptions(record)
        pt, reason = render_translation(record, base, descriptions_pt, conjugator, nominal)
        if blocked:
            reason = 'Verbete INCERTO no cadastro de bases; aplicação automática bloqueada'
        if direct:
            pt, origin = direct, 'bereia_variante_grafica'
        entry = {'forma': record['form'], 'transliteracao': transliterate(record['form']), 'pt': pt, 'traducao': pt,
                 'morfologia': ' / '.join(descriptions_pt), 'abrev_morf': POS_CODES.get(record['pos'], '')}
        # Sem análise reconhecida, não apresentar o parsing como se fosse descrição validada.
        if not descriptions_pt:
            entry['morfologia'] = POS.get(record['pos'], '')
        record_key = tuple(record.get(field) for field in ['form', 'lemma', 'parsing', 'pos'])
        decision = reviewed.get(record_key)
        if decision:
            if blocked and not decision.get('allow_uncertain'):
                raise ValueError('Revisão editorial não pode liberar verbete INCERTO do cadastro')
            entry['pt'] = entry['traducao'] = pt = decision['pt']
            if decision.get('morfologia_pt'):
                entry['morfologia'] = decision['morfologia_pt']
            origin, source_id, base = decision.get('origin', 'revisao_editorial_por_forma'), decision['id'], decision['base_pt']
        elif record_key in deferred and not pt:
            reason = deferred[record_key]['reason']
        old_entry, old_provenance = previous.get(record_key, ({}, {}))
        if old_entry.get('pt') and old_provenance.get('generation_stage') != stage:
            # Esta etapa preenche lacunas; não retraduz entradas beta já preenchidas.
            entry = dict(old_entry)
            pt, origin = entry['pt'], old_provenance['origin']
            source_id, base = old_provenance['source_id'], old_provenance['base_pt']
            counts['preserved_occurrences'] += record['occurrences']
        elif pt:
            counts['newly_translated_occurrences'] += record['occurrences']
            changes.append({'form': record['form'], 'lemma': record['lemma'], 'pt': pt,
                            'parsing': record['parsing'], 'pos': record['pos'], 'occurrences': record['occurrences'],
                            'references': record['references'], 'origin': origin, 'source_id': source_id})
        index = len(prepared)
        prepared.append(entry)
        provenance.append({'form': record['form'], 'lemma': record['lemma'], 'origin': origin,
                           'source_id': source_id, 'base_pt': base, 'parsing_source': record['parsing'],
                           'status': 'APLICADO_BETA' if pt else 'PENDENTE_TRADUCAO',
                           'confidence_source': record['source_confidence'],
                           'generation_stage': stage if old_provenance.get('generation_stage') == stage or not old_entry.get('pt') and pt else old_provenance.get('generation_stage', 1)})
        record_index[record_key] = index
        counts['translated_occurrences' if pt else 'untranslated_occurrences'] += record['occurrences']
        if pt:
            counts[origin] += record['occurrences']
        else:
            pending.append({**record, 'reason': reason})
    occurrences = {}
    source_hashes = []
    for source in report['sourceFiles']:
        original_path = Path(originals) / source['original']
        if digest(original_path) != source['original_sha256']:
            raise ValueError(f"Original mudou: {source['original']}")
        converted_path = ROOT / 'src/interlinear/at' / source['book']
        if digest(converted_path) != source['converted_sha256']:
            raise ValueError(f"Livro convertido mudou: {source['book']}")
        source_hashes.append(source)
        for verse in read(original_path):
            match = re.fullmatch(r'.+ (\d+):(\d+[a-z]?)', verse['ref'])
            chapter, number = match.groups()
            for position, word in enumerate(verse['words']):
                key = (word['surface'], word.get('lemma'), word.get('parsing'), word.get('pos'))
                if key in record_index:
                    occurrences[f"{source['book'][:-5]}:{int(chapter)}:{number}:{position}"] = record_index[key]
    if len(occurrences) != report['summary']['missingTokens']:
        raise ValueError('Total de ocorrências do suplemento não confere com a auditoria')
    output = ROOT / 'src/_data/lxx/supplement-beta.json'
    output.write_text(json.dumps({'version': 1,
        'books': {source['book'][:-5]: source['converted_sha256'] for source in source_hashes},
        'entries': prepared, 'occurrences': occurrences}, ensure_ascii=False, indent=2) + '\n')
    beta_report = {'beta': True, 'counts': dict(counts), 'entries': provenance,
                   'source_hashes': source_hashes,
                   'input_hashes': {'audit': digest(report_path), 'dictionary': digest(dictionary_path),
                                    'lexical': digest(ROOT / 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json'),
                                    'local': digest(local_path), 'glosses': digest(gloss_path)},
                   'attribution': 'TBESG: Tyndale House e STEPBible.org, CC BY 4.0; dados locais e BEREIA conforme origem. Traduções e flexões portuguesas adaptadas para versão beta.'}
    beta_report['input_files'] = {'audit': str(report_path.resolve().relative_to(ROOT))}
    if bases_path:
        beta_report['input_hashes']['bases'] = digest(bases_path)
        beta_report['previous_supplement_sha256'] = previous_application.get('previous_supplement_sha256', previous_hash)
        change_report = {'stage': stage, 'counts': dict(counts), 'previous_supplement_sha256': previous_hash,
                         'bases_sha256': digest(bases_path), 'changes': changes}
        if aliases_path:
            change_report['aliases_sha256'] = digest(aliases_path)
        if reviewed_path:
            change_report['reviewed_sha256'] = digest(reviewed_path)
        change_path = ROOT / f'tools/relatorios/lxx-beta-etapa{stage}.json'
        if change_path.exists():
            change_report['previous_supplement_sha256'] = read(change_path)['previous_supplement_sha256']
        if changes or not change_path.exists():
            change_path.write_text(json.dumps(change_report, ensure_ascii=False, indent=2) + '\n')
    if aliases_path:
        beta_report['input_hashes']['aliases'] = digest(aliases_path)
    if reviewed_path:
        beta_report['input_hashes']['reviewed'] = digest(reviewed_path)
        beta_report['input_files']['reviewed'] = str(reviewed_path.resolve().relative_to(ROOT))
    (ROOT / 'tools/relatorios/lxx-beta-aplicacao.json').write_text(json.dumps(beta_report, ensure_ascii=False, indent=2) + '\n')
    with (ROOT / 'tools/relatorios/lxx-beta-pendencias.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['estado', 'forma', 'lema', 'parsing_original', 'ocorrencias', 'motivo', 'referencias'])
        for row in pending:
            writer.writerow(['INCERTO', row['form'], row['lemma'], row['parsing'], row['occurrences'], row['reason'], '; '.join(row['references'])])
    print(json.dumps(dict(counts), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('originals', type=Path)
    parser.add_argument('--audit', type=Path, help='Auditoria TBESG atualizada, sem sobrescrever o histórico')
    parser.add_argument('--bases', type=Path, help='Cadastro de bases portuguesas por identificador TBESG')
    parser.add_argument('--aliases', type=Path, help='Correspondências explícitas revisadas')
    parser.add_argument('--stage', type=int, default=2)
    parser.add_argument('--reviewed', type=Path, help='Decisões editoriais por forma e conjunto fechado de referências')
    args = parser.parse_args()
    generate(args.originals, args.audit, args.bases, args.aliases, args.stage, args.reviewed)
