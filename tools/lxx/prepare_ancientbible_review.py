#!/usr/bin/env python3
"""Prepara pares para revisão humana, preservando campos da concordância."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def prepare(audit_path, output, translations_path=None):
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    matched, missing = [], []
    for index, row in enumerate(audit['records'], 1):
        candidates = {}
        for label, entries in [(row['status'], row['matches']),
                               ('transliteracao', row['transliteration_candidates']),
                               ('identificador_tbesg', row['identifier_candidates'])]:
            for entry in entries:
                identity = (entry['id'], entry['head_original'], entry['transliteration'], entry['gloss'])
                candidate = candidates.setdefault(identity, {'entry': entry, 'matches': []})
                if label not in candidate['matches']:
                    candidate['matches'].append(label)
                if entry['complete_json_record']:
                    candidate['entry'] = entry
        common = {'termo_faltante': row['lemma'], 'ocorrencias_pendentes': row['occurrences'],
                  'formas_pendentes': row['forms'], 'referencias': row['references']}
        if not candidates:
            missing.append({'id': f'LXX-AB-{index:03d}', **common,
                            'candidato_concordance': None, 'traducao_concordance': None,
                            'traducao_revisada': None, 'aplicar': False, 'observacoes': ''})
        for number, candidate in enumerate(candidates.values(), 1):
            entry = candidate['entry']
            matched.append({'id': f'LXX-AB-{index:03d}-{number:02d}', **common,
                            'candidato_concordance': entry['head_original'],
                            'traducao_concordance': entry['gloss'],
                            'identificador_concordance': entry['id'],
                            'transliteracao_concordance': entry['transliteration'],
                            'correspondencias': candidate['matches'],
                            'registro_completo_legivel': entry['complete_json_record'],
                            'campos_originais_legiveis': entry['fields_read_original'],
                            'traducao_revisada': None, 'aplicar': False, 'observacoes': ''})
    source = Path(audit['source']['path'])
    if hashlib.sha256(source.read_bytes()).hexdigest() != audit['source']['sha256']:
        raise ValueError('A concordância mudou desde a auditoria; execute a auditoria novamente')
    pending = ROOT / audit['pending']['file']
    if hashlib.sha256(pending.read_bytes()).hexdigest() != audit['pending']['sha256']:
        raise ValueError('A lista de pendências mudou desde a auditoria')
    unique = {row['termo_faltante']: row['ocorrencias_pendentes'] for row in matched}
    result = {
        'versao': 1,
        'fonte': str(source), 'fonte_sha256': audit['source']['sha256'],
        'fonte_json_valido': audit['source']['valid_json'], 'primeiro_erro_json_fonte': audit['source']['json_error'],
        'pendencias_sha256': audit['pending']['sha256'],
        'instrucoes': [
            'candidato_concordance e traducao_concordance preservam exatamente os campos legíveis da fonte, inclusive erros e espaços.',
            'Quando o grego está ausente ou misturado com outros alfabetos, candidato_concordance preserva o campo original, sem reconstrução.',
            'Correspondências por transliteração ou identificador são apenas candidatos. Nenhuma equivalência lexical está aprovada.',
            'Preencha traducao_revisada com a base lexical portuguesa desejada (infinitivo para verbos) e marque aplicar como true no candidato escolhido.',
            'Use observacoes para exceções, restrições de contexto ou dúvidas. A aplicação futura precisará respeitar as formas e referências.',
            'Os termos sem candidato ficam separados. Sua tradução revisada também pode ser preenchida manualmente.',
            'Não houve aplicação de traduções nem alteração dos campos da fonte.'
        ],
        'resumo': {'lemas_pendentes': audit['pending']['lemmas'], 'ocorrencias_pendentes': audit['pending']['occurrences'],
                   'lemas_com_candidato': len(unique), 'pares_para_revisao': len(matched),
                   'ocorrencias_com_candidato': sum(unique.values()), 'lemas_sem_candidato': len(missing)},
        'com_candidato': matched, 'sem_candidato': missing}
    if translations_path:
        proposals = json.loads(translations_path.read_text(encoding='utf-8'))
        if proposals['source_sha256'] != audit['source']['sha256']:
            raise ValueError('Propostas de tradução pertencem a outra versão da concordância')
        registry = json.loads((ROOT / 'tools/lxx/tbesg_bases_pt.json').read_text(encoding='utf-8'))
        uncertain = {key for key, entry in registry['entries'].items() if entry['estado'] == 'INCERTO'}
        homographs = Counter(row['termo_faltante'] for row in matched)
        for row in matched:
            row['traducao_proposta_pt'] = proposals['translations'][row['traducao_concordance']]
            alerts = ['Tradução da glosa inglesa; sentido bíblico e flexão ainda não validados.']
            if row['identificador_concordance'] in uncertain:
                alerts.append('Este identificador já está INCERTO no cadastro TBESG; a glosa inglesa não libera sua aplicação.')
            if not any(label.startswith(('exact', 'case_or_sigma_only', 'without_diacritics')) for label in row['correspondencias']):
                alerts.append('Não há igualdade do lema grego: apenas candidato por transliteração ou identificador; conferir classe e sentido.')
            if homographs[row['termo_faltante']] > 1:
                alerts.append('Há mais de um candidato para o mesmo termo; não combinar nem escolher automaticamente.')
            row['alertas_revisao'] = alerts
        result['idioma_glosas_fonte'] = 'en'
        result['propostas_sha256'] = hashlib.sha256(translations_path.read_bytes()).hexdigest()
        result['referencias_traducao_glosas'] = proposals.get('references', {})
        result['instrucoes'].insert(0, 'traducao_proposta_pt traduz apenas a glosa inglesa, inclusive quando ela é questionável. Não representa tradução aprovada para o lema grego.')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['resumo'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, default=ROOT / 'tools/relatorios/lxx-ancientbible-cobertura-formatado.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'tools/relatorios/lxx-ancientbible-revisao.json')
    parser.add_argument('--translations', type=Path, help='Traduções das glosas, separadas da revisão e da aplicação')
    args = parser.parse_args()
    prepare(args.audit, args.output, args.translations)
