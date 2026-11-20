"""Testes de comportamento; nenhum dado de produção é alterado."""
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.audit.audit_tm import (ROOT, align, audit, classify, compatibility,
                                 exceptions_from, folded, index_lexicon, inventory, nfc, parsing)


def lexical():
    return {'746': {'lema': 'ἀρχή', 'verbete': 'G746', 'flexoes': [
        {'grego': 'ἀρχή', 'abrev_morf': 'S-NFS', 'morfologia': 'Nominativo'}]}}


def verse(forms):
    return {'ref': 'JO 1:1', 'chapter': '1', 'verse': '1', 'forms': forms,
            'tokens': [{'lemma': f} for f in forms]}


class AuditTests(unittest.TestCase):
    def test_iota_subscript_is_not_nfc_equivalence(self):
        self.assertEqual(folded('ἀρχῇ'), folded('ἀρχή'))
        self.assertNotEqual(nfc('ἀρχῇ'), nfc('ἀρχή'))
        idx = index_lexicon(lexical())
        self.assertEqual(classify('ἀρχή', idx)[0], 'exata')
        self.assertEqual(classify('ἀρχῇ', idx), ('ausente', []))
        self.assertEqual(classify('Ἀρχή', idx), ('ausente', []))

    def test_canonical_equivalence_only(self):
        self.assertEqual(classify('α\u0313ρχη\u0301', index_lexicon(lexical()))[0], 'somente_nfc')

    def test_homographs_remain_separate(self):
        lex = lexical()
        lex['999'] = copy.deepcopy(lex['746'])
        rows = classify('ἀρχή', index_lexicon(lex))[1]
        self.assertEqual([r['strong'] for r in rows], ['746', '999'])
        self.assertEqual([r['flexao'] for r in rows], [0, 0])

    def test_alignment_requires_full_verse(self):
        v = verse(['ἐν', 'ἀρχῇ'])
        aux = {'valid': True, 'tokens': [('εν', '1722', 'PREP'), ('αρχη', '746', 'N-DSF')]}
        self.assertEqual(align(v, aux), 'alinhado')
        aux['tokens'].reverse()
        self.assertEqual(align(v, aux), 'sequencia_divergente')
        aux['tokens'].pop()
        self.assertEqual(align(v, aux), 'quantidade_divergente')
        self.assertEqual(align(v, None), 'sem_fonte')
        aux['valid'] = False
        self.assertEqual(align(v, aux), 'parsing_invalido')

    def test_morphology_conventions_and_strong_literal(self):
        rows = [{'strong': '746', 'abrev_morf': 'S-DFS'}]
        self.assertEqual(compatibility(rows, '746', 'N-DSF'), 'substantivo_compativel')
        self.assertEqual(compatibility(rows, '746', 'N-NSF'), 'morfologia_divergente')
        self.assertEqual(compatibility(rows, '746 ', 'N-DSF'), 'strong_divergente')
        self.assertEqual(compatibility(rows, '746', 'V-PAI-3S'), 'nao_comparavel')

    def test_legacy_wrong_association_is_reported_without_mutation(self):
        lex = lexical()
        flat = {'ἀρχή': {'strongs': '746', 'grego': 'ἀρχή', 'abrev_morf': 'S-NFS'}}
        before = copy.deepcopy((lex, flat))
        sources = {('JO', '1', '1'): {'valid': True, 'tokens': [('αρχη', '746', 'N-DSF')]}}
        report = audit([verse(['ἀρχῇ'])], sources, lex, flat, [])
        row = report['formas'][0]
        self.assertEqual(row['classe'], 'ausente')
        self.assertEqual(row['consulta_atual']['grego'], 'ἀρχή')
        self.assertEqual(row['evidencias'][0]['comparacao_consulta_atual'], 'morfologia_divergente')
        self.assertEqual((lex, flat), before)

    def test_existing_exceptions_and_actual_js_lookup(self):
        # Usa a implementação real sem carregar livros nem gravar logs.
        code = """
const {createEnhanceTokenWithDict} = require('./src/_data/nt');
const dict = {'ἀρχή': {grego:'ἀρχή', abrev_morf:'S-NFS'}, 'ἡ':{grego:'ἡ'}, 'ἢ':{grego:'ἢ'}};
const lookup = createEnhanceTokenWithDict(dict, {record(){}});
console.log(JSON.stringify(['ἀρχῇ','ἡ','ἢ'].map(lemma => lookup({lemma}))));
"""
        result = subprocess.run(['node', '-e', code], cwd=ROOT, check=True, capture_output=True, text=True)
        rows = json.loads(result.stdout)
        # Fixture sem a flexão dativa: documenta o fallback legado, ainda
        # preservado durante a migração. A regressão com o léxico real é separada.
        self.assertEqual([r['grego'] for r in rows], ['ἀρχή', 'ἡ', 'ἢ'])
        self.assertIn('η', exceptions_from((ROOT / 'src/_data/nt/index.js').read_text()))

    def test_partial_parsing_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'JOH.csv'
            p.write_text('chapter,verse,text\n1,1,αρχη 746 {N-DSF} lixo\n', encoding='utf-8')
            self.assertFalse(parsing(p)[('1', '1')]['valid'])

    def test_real_inventory_and_incremental_reproducibility(self):
        # Execuções integrais, cache frio/quente/sem cache, com hashes iguais.
        with tempfile.TemporaryDirectory(dir=ROOT / 'reports/audit') as directory:
            output = Path(directory)
            cmd = ['python3', '-B', 'tools/audit/audit_tm.py', '--output', str(output)]
            hashes = []
            for options in [[], [], ['--no-cache']]:
                subprocess.run(cmd + options, cwd=ROOT, check=True, capture_output=True)
                hashes.append({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*') if p.is_file()})
            self.assertEqual(hashes[0], hashes[1])
            self.assertEqual(hashes[1], hashes[2])
            report = json.loads((output / 'inventario.json').read_text())
            self.assertEqual(report['resumo']['tokens_tm'], sum(len(r['referencias']) for r in report['formas']))
            self.assertTrue(all(report['produtos'].values()))
            arche = next(r for r in report['formas'] if r['forma_tm'] == 'ἀρχῇ')
            self.assertIn('JO 1:1#2', arche['referencias'])
            # Cache adulterado com chave antiga é recalculado.
            cache = next((output / '.cache').glob('*.json'))
            cache.write_text('{"key":"obsoleto"}', encoding='utf-8')
            subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(hashes[0], {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
