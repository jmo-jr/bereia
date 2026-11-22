"""Regressões de classificação, consulta estrita e evidências não inferidas."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.audit.audit_tm import ROOT, digest
from tools.audit.strict_lookup import StrictLookup
from tools.audit.triage_tm import (candidate_difference, classify_gap, compare_lookup,
                                  apply_gloss_decision, evidence_for_gap, pilot, proposal, verify_sources)


def row(form, candidates=()):
    return {'forma_tm': form, 'classe': 'ausente', 'referencias': ['JO 1:1#2'],
            'evidencias': [], 'consulta_atual': None,
            'candidatos_sem_diacriticos': [{'forma': f, 'strong': '746', 'flexao': i,
                'abrev_morf': 'S-NFS', 'morfologia': 'Nominativo'} for i, f in enumerate(candidates)]}


def lexicon():
    return {'746': {'lema': 'ἀρχή', 'verbete': 'G746', 'flexoes': [
        {'grego': 'ἀρχή', 'abrev_morf': 'S-NFS', 'morfologia': 'Nominativo'}]}}


class TriageTests(unittest.TestCase):
    def test_acute_grave_preserves_position_and_other_accents(self):
        self.assertEqual(candidate_difference('ἀρχὴ', 'ἀρχή'), 'agudo_grave_mesma_posicao')
        self.assertEqual(candidate_difference('Βηθλέεμ', 'Βηθλεέμ'), 'outros_acentos')
        self.assertEqual(candidate_difference('γάμων', 'γαμῶν'), 'outros_acentos')
        self.assertEqual(candidate_difference('αὐτοῦ', 'αὐτοὺ'), 'outros_acentos')

    def test_breathings_iota_and_diaeresis_are_not_accents(self):
        for a, b in [('ἀρχῇ', 'ἀρχή'), ('ἕκτος', 'ἐκτός'), ('ἰ', 'ἱ'), ('ϊ', 'ι')]:
            self.assertEqual(candidate_difference(a, b), 'outras_marcas')

    def test_whitespace_is_retained_and_other_candidate_risks_visible(self):
        r = row('Ὦ ', ['ὦ '])
        self.assertEqual(classify_gap(r), 'espacos_marginais')
        p = proposal(r, lexicon(), 'hash')
        self.assertEqual(p['forma_tm'], 'Ὦ ')
        self.assertEqual(p['candidatos'][0]['diferenca'], 'somente_caixa')
        self.assertTrue(p['riscos']['candidatos_de_outros_grupos_graficos'])

    def test_strict_lookup_has_no_case_or_marks_fallback(self):
        resolver = StrictLookup(lexicon())
        self.assertEqual(resolver.resolve('ἀρχή')['estado'], 'unica')
        self.assertEqual(resolver.resolve('Ἀρχή')['correspondencia'], 'caixa')
        for form in ['ἀρχῇ', 'αρχη', 'ἀρχή ']:
            self.assertEqual(resolver.resolve(form)['entradas'], [])

    def test_canonical_collision_retains_all_analyses_even_with_literal(self):
        lex = lexicon()
        lex['746 '] = {'lema': None, 'flexoes': [{'grego': 'α\u0313ρχη\u0301',
            'abrev_morf': 'S-NFS', 'morfologia': 'Outra análise'}]}
        resolver = StrictLookup(lex)
        literal = resolver.resolve('ἀρχή')
        self.assertEqual(literal['estado'], 'multipla')
        self.assertEqual([e['strong'] for e in literal['entradas']], ['746', '746 '])
        self.assertEqual(literal['entradas'], resolver.resolve('α\u0313ρχη\u0301')['entradas'])
        literal['entradas'][0]['strong'] = 'alterado'
        self.assertEqual(resolver.resolve('ἀρχή')['entradas'][0]['strong'], '746')

    def test_shadowed_exact_form_is_detected_without_replacing_it(self):
        lex = lexicon()
        lex['746']['flexoes'].append({'grego': 'ἀρχῇ', 'abrev_morf': 'S-DFS', 'morfologia': 'Dativo'})
        r = row('ἀρχῇ', ['ἀρχή'])
        r['consulta_atual'] = {'strongs': '746', 'grego': 'ἀρχή', 'abrev_morf': 'S-NFS', 'morfologia': 'Nominativo'}
        before = copy.deepcopy(r)
        result = compare_lookup([r], StrictLookup(lex))
        self.assertTrue(result['formas'][0]['sombreamento'])
        self.assertEqual(result['tokens_por_classificacao']['forma_coberta_mas_sombreada'], 1)
        self.assertEqual(r, before)

    def test_nominal_evidence_uses_literal_strong_and_aligned_references_only(self):
        r = row('ἀρχῇ', ['ἀρχή'])
        r['referencias'].append('AT 11:15#19')
        r['evidencias'] = [{'strong_fonte': '746', 'morfologia_fonte': 'N-DSF', 'referencias': ['JO 1:1#2']}]
        evidence = evidence_for_gap(r, lexicon())
        self.assertEqual(evidence['nominais'][0]['abrev_morf_candidata'], 'S-DFS')
        self.assertEqual(evidence['referencias_sem_parsing_alinhado'], ['AT 11:15#19'])
        r['evidencias'][0]['strong_fonte'] = '746 '
        self.assertEqual(evidence_for_gap(r, lexicon())['nominais'], [])

    def test_pilot_never_copies_translation_or_assigns_unaligned_parsing(self):
        r = row('ἀρχῇ', ['ἀρχή'])
        r['evidencias'] = [{'strong_fonte': '746', 'morfologia_fonte': 'N-DSF', 'referencias': r['referencias']}]
        p = proposal(r, lexicon(), 'hash')
        case = pilot([p], lexicon())
        self.assertEqual(case['inclusao_em_revisao']['abrev_morf'], 'S-DFS')
        self.assertIsNone(case['inclusao_em_revisao']['traducao'])
        self.assertIsNone(case['inclusao_em_revisao']['pt'])
        self.assertFalse(case['aplicado'])
        r['evidencias'].append({'strong_fonte': '746', 'morfologia_fonte': 'N-NSF', 'referencias': []})
        self.assertIsNone(pilot([proposal(r, lexicon(), 'hash')], lexicon())['inclusao_em_revisao']['abrev_morf'])

    def test_stale_inventory_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'desatualizado'):
            verify_sources({'schema_version': 1, 'fontes_sha256': {'tools/audit/triage_tm.py': 'obsoleto'}})

    def test_approved_glosses_apply_only_to_pilot_proposal(self):
        lex = lexicon()
        before = copy.deepcopy(lex)
        proposals = [proposal(row('ἀρχῇ', ['ἀρχή']), lex, 'hash'),
                     proposal(row('Ἀρχή', ['ἀρχή']), lex, 'hash')]
        case = pilot(proposals, lex)
        contextual = {'avaliacao_humana_preparada': {'proposta_glosas': {'traducao': 'anterior', 'pt': 'anterior'}}}
        decisions = json.loads((ROOT / 'tools/audit/decisions.json').read_text())
        apply_gloss_decision(case, contextual, proposals, decisions)
        self.assertEqual(case['inclusao_em_revisao']['traducao'], 'no princípio, ao principado')
        self.assertEqual(case['inclusao_em_revisao']['pt'], 'no princípio')
        self.assertEqual(contextual['avaliacao_humana_preparada']['proposta_anterior']['traducao'], 'anterior')
        self.assertIsNone(proposals[1]['traducao_proposta'])
        self.assertFalse(case['aplicado'])
        self.assertEqual(lex, before)

    def test_end_to_end_is_reproducible_and_covers_all_missing_forms(self):
        (ROOT / 'reports/audit').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'reports/audit') as directory:
            output = Path(directory)
            # Gerar inventário atualizado em área temporária; fontes sempre em leitura.
            subprocess.run(['python3', '-B', 'tools/audit/audit_tm.py', '--output', str(output / 'tm'),
                '--books', 'JO', 'AP'], cwd=ROOT, check=True, capture_output=True)
            cmd = ['python3', '-B', '-m', 'tools.audit.triage_tm', '--inventory',
                str(output / 'tm/inventario.json'), '--output', str(output / 'triagem')]
            subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
            before = {p.name: digest(p) for p in (output / 'triagem').iterdir()}
            subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(before, {p.name: digest(p) for p in (output / 'triagem').iterdir()})
            summary = json.loads((output / 'triagem/resumo.json').read_text())
            self.assertEqual(sum(summary['grupos'].values()), summary['formas_sem_cobertura'])
            case = json.loads((output / 'triagem/piloto-arche.json').read_text())
            self.assertEqual(case['referencias_tm'], ['JO 1:1#2', 'JO 1:2#4'])
            self.assertEqual(case['inclusao_em_revisao']['traducao'], 'no princípio, ao principado')
            self.assertEqual(case['inclusao_em_revisao']['pt'], 'no princípio')
            self.assertTrue(case['aplicado'])
            proposals = json.loads((output / 'triagem/propostas.json').read_text())['propostas']
            self.assertNotIn('ἀρχῇ', [p['forma_tm'] for p in proposals])


if __name__ == '__main__':
    unittest.main()
