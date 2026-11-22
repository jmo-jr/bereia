import json
import tempfile
import unittest
from pathlib import Path

from tools.lxx.prepare_tbesg_bases import ROOT, load_translations, digest


class LexicalBaseTests(unittest.TestCase):
    def test_ids_cannot_be_silently_merged(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'bases.tsv'
            file.write_text('G0001G\tprimeiro\nG0001H\tsegundo\n', encoding='utf-8')
            self.assertEqual(load_translations(file), {'G0001G': 'primeiro', 'G0001H': 'segundo'})
            file.write_text('G0001G\tprimeiro\nG0001G\tsegundo\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'duplicado'):
                load_translations(file)

    def test_registry_preserves_source_and_blocks_uncertainty(self):
        registry = json.loads((ROOT / 'tools/lxx/tbesg_bases_pt.json').read_text())
        audit = json.loads((ROOT / 'tools/relatorios/lxx-tbesg-cobertura-beta.json').read_text())
        entries = {row['dStrong'].split()[0]: row for row in audit['lexicon']}
        for identifier, base in registry['entries'].items():
            source = entries[identifier]
            self.assertEqual(base['lema'], source['greek'])
            self.assertEqual(base['definition_en'], source['meaning'])
            self.assertEqual(base['morph_lexical'], source['morph'])
            self.assertEqual(base['dStrong'], source['dStrong'])
            if base['estado'] == 'INCERTO':
                self.assertIsNone(base['base_pt'])
            else:
                self.assertTrue(base['base_pt'])
        self.assertEqual(registry['entries']['G5339']['base_pt'], 'poupar')
        self.assertEqual(registry['entries']['G4876']['base_pt'], 'encontrar-se')
        self.assertEqual(registry['entries']['G8308']['base_pt'], 'elevado')
        summary = registry['summary']
        self.assertEqual(summary['single_candidate_ids'], len(registry['entries']))
        self.assertEqual(summary['single_candidate_ids'], summary['bases_beta'] + summary['uncertain_ids'])
        self.assertEqual(summary['single_candidate_occurrences'], summary['occurrences_with_base'] + summary['uncertain_occurrences'])
        self.assertEqual(summary['pending_occurrences'], summary['single_candidate_occurrences'] + sum(summary['other_occurrences'].values()))
        current_hash = digest(ROOT / 'src/_data/lxx/supplement-beta.json')
        if current_hash != registry['inputs_sha256']['supplement']:
            # A etapa 2 aplica as bases; a ligação com o retrato da etapa 1 continua explícita.
            applied = json.loads((ROOT / 'tools/relatorios/lxx-beta-aplicacao.json').read_text())
            self.assertEqual(applied['input_hashes']['bases'], digest(ROOT / 'tools/lxx/tbesg_bases_pt.json'))
            self.assertEqual(applied['previous_supplement_sha256'], registry['inputs_sha256']['supplement'])


if __name__ == '__main__':
    unittest.main()
