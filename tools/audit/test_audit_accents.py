"""Contratos de evidência para o lote agudo/grave; sem alterações nos dados."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.audit.audit_tm import ROOT, digest
from tools.audit.audit_accents import build, check_description, compare_codes, morphology, review
from tools.audit.triage_tm import classify_gap


def fixture():
    flex = {'grego': 'ἀρχή', 'transliteracao': 'archē', 'ocorrencias': '1',
            'traducao': 'princípio', 'pt': 'princípio', 'abrev_morf': 'S-NFS',
            'morfologia': 'Substantivo - Nominativo Feminino Singular',
            'lxx': ['referência do candidato'], 'ocorrencias_lxx': 999}
    lexicon = {'746': {'lema': 'ἀρχή', 'flexoes': [flex]}}
    row = {'forma_tm': 'ἀρχὴ', 'classe': 'ausente', 'referencias': ['TESTE 1:1#1'],
           'candidatos_sem_diacriticos': [{'strong': '746', 'flexao': 0, 'forma': 'ἀρχή'}],
           'evidencias': [{'strong_fonte': '746', 'morfologia_fonte': 'N-NSF', 'referencias': ['TESTE 1:1#1']}]}
    return row, lexicon


class AccentTests(unittest.TestCase):
    def test_nominal_order_and_gender_are_explicit(self):
        self.assertEqual(compare_codes('S-DFS', 'N-DSF'), 'compativel')
        self.assertEqual(compare_codes('Adj-NMP', 'A-NPM'), 'compativel')
        self.assertEqual(compare_codes('Adj-AMS', 'A-ASN'), 'divergente')
        self.assertEqual(compare_codes('S', 'N-PRI'), 'nao_comparavel')

    def test_neuter_syncretism_is_not_an_independent_error(self):
        self.assertEqual(compare_codes('Adj-NNS', 'A-ASN'), 'compativel_nom_acus_neutro')
        self.assertEqual(compare_codes('V-RPA-NNS', 'V-2RAP-ASN'), 'compativel_nom_acus_neutro')
        self.assertEqual(compare_codes('S-NMS', 'N-ASM'), 'divergente')

    def test_verb_order_voice_person_and_second_paradigm(self):
        self.assertEqual(compare_codes('V-APA-NMS', 'V-2AAP-NSM'), 'compativel')
        self.assertEqual(compare_codes('V-AMA-2S', 'V-2AAM-2S'), 'compativel')
        self.assertEqual(compare_codes('V-AMA-2S', 'V-2AMM-2S'), 'divergente')
        self.assertEqual(compare_codes('V-PIA-1S', 'V-PAI-3S'), 'divergente')
        self.assertEqual(compare_codes('V-PI-1S', 'V-PAI-1S'), 'nao_comparavel')
        self.assertIsNone(morphology('V-AOP-NSM', source=True))
        self.assertIsNone(morphology('V-2PAI-1S', source=True))
        self.assertIsNone(morphology('V-APA'))

    def test_description_must_agree_with_code(self):
        self.assertEqual(check_description('S-DFS', 'Substantivo - Dativo Feminino Singular'), 'coerente')
        self.assertEqual(check_description('S-DFS', 'Substantivo - Genitivo Feminino Singular'), 'revisar_descricao')
        self.assertEqual(check_description('V-RIA-3S', 'Verbo - Imperfeito Indicativo Ativa - 3ª Pessoa Singular'), 'revisar_descricao')
        self.assertEqual(check_description('V-RIA-3S', 'Verbo - Mais-que-perfeito Indicativo Ativa - 3ª Pessoa Singular'), 'revisar_descricao')
        self.assertEqual(check_description('V-APA-NMS', 'Verbo — Aoristo Particípio Ativo — Nominativo Masculino Singular'), 'coerente')

    def test_complete_matching_evidence_produces_unapplied_draft(self):
        row, lexicon = fixture()
        before = copy.deepcopy((row, lexicon))
        result = review(row, lexicon, ['gn.json 1:1#1', 'gn.json 2:1#1'])
        self.assertEqual(result['estado'], 'SUGERIR')
        self.assertFalse(result['aplicado'])
        self.assertEqual(result['minuta_inclusao']['grego'], 'ἀρχὴ')
        self.assertEqual(result['minuta_inclusao']['traducao'], 'princípio')
        self.assertEqual(result['minuta_inclusao']['ocorrencias_lxx'], 2)
        self.assertEqual(result['minuta_inclusao']['lxx'], [])
        self.assertEqual((row, lexicon), before)

    def test_partial_coverage_never_assigns_unaligned_parsing(self):
        row, lexicon = fixture()
        row['referencias'].append('TESTE 1:2#1')
        result = review(row, lexicon, [])
        self.assertEqual(result['grupo'], 'cobertura_parcial_do_parsing')
        self.assertEqual(result['referencias_sem_parsing_alinhado'], ['TESTE 1:2#1'])
        self.assertIsNone(result['minuta_inclusao'])

    def test_strong_is_literal_and_divergence_blocks_draft(self):
        row, lexicon = fixture()
        row['evidencias'][0]['strong_fonte'] = '746 '
        result = review(row, lexicon, [])
        self.assertEqual(result['grupo'], 'strong_divergente')
        self.assertIsNone(result['minuta_inclusao'])

    def test_morphology_conflicts_and_extra_candidates_block_draft(self):
        row, lexicon = fixture()
        row['evidencias'][0]['morfologia_fonte'] = 'N-DSF'
        self.assertEqual(review(row, lexicon, [])['grupo'], 'morfologia_divergente')
        row, lexicon = fixture()
        row['candidatos_sem_diacriticos'].append({'strong': '746', 'flexao': 1, 'forma': 'ἀρχῇ'})
        result = review(row, lexicon, [])
        self.assertIn('outros_candidatos_sem_marcas', result['sinais'])
        self.assertIsNone(result['minuta_inclusao'])

    def test_no_evidence_never_becomes_positive_by_graphic_similarity(self):
        row, lexicon = fixture()
        row['evidencias'] = []
        self.assertEqual(review(row, lexicon, [])['grupo'], 'sem_parsing_alinhado')

    def test_only_requested_graphic_group_is_read(self):
        row, lexicon = fixture()
        excluded = copy.deepcopy(row)
        excluded['forma_tm'] = 'ἀρχῇ'
        self.assertEqual(len(build([row, excluded], lexicon, {})), 1)

    def test_real_batch_is_reproducible_and_sources_stay_unchanged(self):
        (ROOT / 'reports/audit').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'reports/audit') as directory:
            temporary = Path(directory)
            inventory = temporary / 'tm/inventario.json'
            subprocess.run(['python3', '-B', 'tools/audit/audit_tm.py', '--output', str(temporary / 'tm')],
                           cwd=ROOT, check=True, capture_output=True)
            expected_forms = {r['forma_tm'] for r in json.loads(inventory.read_text())['formas']
                              if r['classe'] == 'ausente' and classify_gap(r) == 'agudo_grave_mesma_posicao'}
            output = temporary / 'lote'
            cmd = ['python3', '-B', '-m', 'tools.audit.audit_accents', '--output', str(output), '--inventory', str(inventory)]
            subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
            hashes = {p.name: digest(p) for p in output.iterdir()}
            subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(hashes, {p.name: digest(p) for p in output.iterdir()})
            result = json.loads((output / 'revisao.json').read_text())
            self.assertEqual(result['resumo']['formas'], len(result['itens']))
            self.assertEqual({r['forma_tm'] for r in result['itens']}, expected_forms)
            for row in result['itens']:
                self.assertFalse(row['aplicado'])
                self.assertEqual(row['decisao'], 'pendente')
                if row['estado'] == 'SUGERIR':
                    self.assertEqual(row['referencias_sem_parsing_alinhado'], [])
                    self.assertEqual(row['sinais'], [])
            for path, expected in result['fontes_sha256'].items():
                self.assertEqual(digest(ROOT / path), expected, path)


if __name__ == '__main__':
    unittest.main()
