#!/usr/bin/env python3
"""Prepara bases lexicais em português. Não altera o gerador, as flexões ou o site."""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REPORTS = ROOT / 'tools/relatorios'


def read(file):
    return json.loads(Path(file).read_text(encoding='utf-8'))


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def load_translations(file):
    result = {}
    for line, fields in enumerate(csv.reader(Path(file).read_text(encoding='utf-8').splitlines(), delimiter='\t'), 1):
        if len(fields) != 2 or not re.fullmatch(r'G\d+[A-Za-z]*', fields[0]) or not fields[1].strip():
            raise ValueError(f'Tradução-base inválida na linha {line}')
        key, base = fields
        if key in result:
            raise ValueError(f'Identificador duplicado: {key}')
        if base != base.strip():
            raise ValueError(f'Espaços indevidos na base de {key}')
        result[key] = base
    return result


# Não resolver pelo contexto uma divergência ou uma identificação insuficiente.
UNCERTAIN = {
    'G6494': 'A fonte fornece somente “to cure”; a base proposta não está fundamentada na definição disponível.',
    'G20524': 'A glosa “sanctuary” e a análise lexical precisam ser conferidas antes de escolher a base portuguesa.',
    'G7660': 'A fonte fornece somente “a tong”; a proposta e a identificação do objeto precisam de conferência.',
    'G20078': 'A fonte fornece apenas “(woad)”, em aparente desacordo com o lema; informação insuficiente.',
    'G9118': 'A fonte fornece apenas “moonlight”; a proposta portuguesa diverge dessa glosa e requer conferência.',
    'G20525': 'A glosa “templecourtesans” envolve uma identificação cultual específica; não presumir equivalência contextual.',
    'G8519': 'Nome de criatura; a identificação e a opção entre tradução e transliteração dependem da política editorial.',
    'G8364': 'Nome de criatura; conferir a identificação antes da aplicação contextual.',
    'G6771': 'Nome de criatura com alternativas na definição; não decidir a identificação zoológica automaticamente.',
    'G8344': '“Unicórnio” é uma opção lexical literal; a identificação do animal no texto permanece incerta.',
    'G9063': '“Sereia” é uma opção lexical; não pressupor a identificação contextual da criatura.',
    'G8074': 'A definição contém ave e diversos objetos curvos; a escolha do objeto exige a ocorrência.',
    'G8825': 'O sentido de pneuma e a voz verbal exigem conferência contextual; a base proposta segue a glosa disponível.',
}

EDITORIAL_NOTES = {
    'G8308': 'Base apoiada em “raised from the ground” da definição completa; não na glosa “a meteorite”.',
    'G7688': 'Base apoiada em “fragment” da definição completa; não na glosa “outbreak”.',
    'G7732': 'Base apoiada em “a sail” da definição completa; não na glosa resumida “a shroud”.',
    'G4162': 'Base nominal apoiada em “a making / a doing”; não na glosa verbal “he did”.',
    'G6706': 'Base apoiada em “a clod” da definição completa; não em “a droplet”.',
    'G7182': 'Base apoiada em “twisted” da definição completa; não em “kneaded”.',
    'G7626': 'Nome da liga/material; a definição inclui âmbar e liga de ouro e prata. Conferir o sentido na ocorrência.',
    'G9517': 'Base apoiada em “sovereignty” da definição completa; não na glosa sobre esposa do soberano.',
    'G21222': 'Base apoiada em “bringing to an end” da definição completa; não em “sorceress”.',
    'G6316': 'Base apoiada em “overthrow” da definição completa; não em “a diet”.',
    'G21111': 'Base apoiada em “a pointed stake” da definição completa; não em “evil, ruin”.',
    'G20685': 'Base apoiada em “with a great name” da definição completa; não na glosa numérica.',
    'G20744': 'Base apoiada em “hating knaves” da definição completa; não em hostilidade genérica.',
    'G4876': 'Base verbal normalizada para infinitivo pronominal; a conjugação será tratada separadamente.',
    'G5339': 'Base verbal no infinitivo; “poupe” não é uma base de dicionário.',
    'G6593': 'Base segue “free from impurities” da definição; não inferir um sentido pela composição da palavra.',
}

PT_CLASS_OVERRIDES = {
    'G6838': 'substantivo', 'G8078': 'substantivo', 'G7021': 'adjetivo',
    'G20592': 'advérbio', 'G6231': 'substantivo', 'G6343': 'substantivo',
    'G6347': 'adjetivo', 'G7118': 'substantivo', 'G7161': 'substantivo',
    'G8116': 'substantivo', 'G8588': 'substantivo',
}


def prepare():
    audit_file = REPORTS / 'lxx-tbesg-cobertura-beta.json'
    application_file = REPORTS / 'lxx-beta-aplicacao.json'
    supplement_file = ROOT / 'src/_data/lxx/supplement-beta.json'
    translations_file = HERE / 'tbesg_base_translations.tsv'
    audit, application, supplement = read(audit_file), read(application_file), read(supplement_file)
    tbesg_file = HERE / 'fontes' / audit['source']['file']
    if digest(tbesg_file) != audit['source']['sha256']:
        raise ValueError('A TBESG local mudou; atualize a auditoria antes de preparar bases')
    if digest(audit_file) != application['input_hashes']['audit']:
        raise ValueError('A auditoria não corresponde ao suplemento beta aplicado')
    if not len(audit['records']) == len(application['entries']) == len(supplement['entries']):
        raise ValueError('As listas da auditoria e do suplemento não estão alinhadas')
    active_books = {file.stem: file for file in (ROOT / 'src/interlinear/at').glob('*.json')}
    for book, file in active_books.items():
        if supplement['books'].get(book) != digest(file):
            raise ValueError(f'O livro {book} mudou; atualize a auditoria antes de preparar bases')
    lexical = {row['line']: row for row in audit['lexicon']}
    selected, remaining = {}, Counter()
    for location, index in supplement['occurrences'].items():
        if location.split(':')[0] not in active_books or supplement['entries'][index]['pt']:
            continue
        row, applied = audit['records'][index], application['entries'][index]
        if (row['form'], row['lemma']) != (applied['form'], applied['lemma']):
            raise ValueError(f'Registro de aplicação desalinhado: {index}')
        if not row['status'].endswith('_single'):
            remaining[row['status']] += 1
            continue
        entry = lexical[row['candidate_lines'][0]]
        key = entry['dStrong'].split()[0]
        if key not in selected:
            selected[key] = {'entry': entry, 'occurrences': 0, 'forms': set(), 'references': set(), 'source_lemmas': set()}
        elif selected[key]['entry'] != entry:
            raise ValueError(f'ID TBESG associado a registros distintos: {key}')
        item = selected[key]
        item['occurrences'] += 1
        item['forms'].add(row['form'])
        item['source_lemmas'].add(row['lemma'])
        book, chapter, verse, _ = location.split(':')
        item['references'].add(f'{book} {chapter}:{verse}')
    translations = load_translations(translations_file)
    missing = set(selected) - set(translations)
    if missing:
        raise ValueError('Faltam propostas para: ' + ', '.join(sorted(missing)))
    entries = {}
    for key, item in sorted(selected.items(), key=lambda pair: (-pair[1]['occurrences'], pair[0])):
        source = item['entry']
        uncertain = key in UNCERTAIN
        entries[key] = {
            'lema': source['greek'], 'base_pt': None if uncertain else translations[key],
            'proposta_pt': translations[key], 'estado': 'INCERTO' if uncertain else 'BASE_BETA',
            'classificacao': 'dependente_de_contexto_ou_informacao_insuficiente' if uncertain else 'alternativa_de_traducao_lexical',
            'observacao': UNCERTAIN.get(key, EDITORIAL_NOTES.get(key,
                'Base lexical provisória; não equivale à tradução contextual de todas as ocorrências.')),
            'eStrong': source['eStrong'], 'dStrong': source['dStrong'], 'uStrong': source['uStrong'],
            'morph_lexical': source['morph'], 'gloss_en': source['gloss'], 'definition_en': source['meaning'],
            'transliteracao_do_lema_fonte': source['transliteration'], 'linha_tbesg': source['line'],
            'ocorrencias_pendentes': item['occurrences'], 'formas_pendentes': sorted(item['forms']),
            'lemas_dos_originais': sorted(item['source_lemmas']), 'referencias': sorted(item['references']),
        }
        if key in PT_CLASS_OVERRIDES:
            entries[key]['classe_portuguesa_da_base'] = PT_CLASS_OVERRIDES[key]
            entries[key]['observacao'] += ' O Morph da fonte é verbal, mas a base lexical portuguesa não é verbo; conferir a classificação antes de gerar flexões. O campo original foi preservado.'
    ready = [entry for entry in entries.values() if entry['base_pt'] is not None]
    summary = {
        'books': len(active_books), 'pending_occurrences': sum(item['occurrences'] for item in selected.values()) + sum(remaining.values()),
        'single_candidate_ids': len(entries), 'single_candidate_occurrences': sum(item['occurrences'] for item in selected.values()),
        'bases_beta': len(ready), 'occurrences_with_base': sum(entry['ocorrencias_pendentes'] for entry in ready),
        'uncertain_ids': len(entries) - len(ready), 'uncertain_occurrences': sum(entry['ocorrencias_pendentes'] for entry in entries.values() if entry['base_pt'] is None),
        'other_occurrences': dict(remaining),
    }
    result = {'schema_version': 1, 'stage': 'bases_lexicais_sem_aplicacao',
        'source': {'file': audit['source']['file'], 'sha256': audit['source']['sha256'],
                   'url': audit['source']['url'], 'attribution': audit['source']['attribution']},
        'inputs_sha256': {name: digest(file) for name, file in [('audit', audit_file), ('application', application_file),
                           ('supplement', supplement_file), ('translations', translations_file)]},
        'method': 'Identificador completo dStrong; glosa e definição inglesas preservadas. Somente candidatos únicos e ocorrências ainda sem tradução nos livros ativos. BASE_BETA é uma escolha lexical provisória, não aprovação contextual. INCERTO não tem base aplicável. Nenhuma flexão ou página regenerada.',
        'summary': summary, 'entries': entries}
    (HERE / 'tbesg_bases_pt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (REPORTS / 'lxx-bases-pt-pendencias.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['estado', 'id_tbesg', 'lema', 'proposta_pt', 'ocorrencias', 'observacao', 'referencias'])
        for key, entry in entries.items():
            if entry['estado'] == 'INCERTO':
                writer.writerow(['INCERTO', key, entry['lema'], entry['proposta_pt'], entry['ocorrencias_pendentes'], entry['observacao'], '; '.join(entry['referencias'])])
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    prepare()
