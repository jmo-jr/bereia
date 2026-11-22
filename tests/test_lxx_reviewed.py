import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.lxx.generate_beta import ROOT, load_reviewed, read


class ReviewedFormsTests(unittest.TestCase):
    def setUp(self):
        self.audit_path = ROOT / 'tools/relatorios/lxx-tbesg-cobertura-etapa4.json'
        self.audit = read(self.audit_path)
        self.path = ROOT / 'tools/lxx/reviewed_step4.json'
        self.reviewed = read(self.path)

    def test_applied_choices_and_deferred_contexts(self):
        decisions, deferred = load_reviewed(self.path, self.audit_path, self.audit)
        supplement = read(ROOT / 'src/_data/lxx/supplement-beta.json')
        for record, entry in zip(self.audit['records'], supplement['entries']):
            key = tuple(record[field] for field in ['form', 'lemma', 'parsing', 'pos'])
            if key in decisions:
                self.assertEqual(entry['pt'], decisions[key]['pt'])
                self.assertEqual(entry['traducao'], entry['pt'])
                self.assertEqual(entry['forma'], record['form'])
                self.assertNotIn('strongs', entry)
            elif key in deferred:
                self.assertEqual(entry['pt'], '')
        self.assertEqual(sum(row['occurrences'] for row in decisions.values()), 394)
        self.assertEqual(sum(row['occurrences'] for row in deferred.values()), 22)
        self.assertEqual(decisions[('Χετταίου', 'Χετταῖος', 'masc gen sg', 'adjective')]['pt'], 'do heteu')
        self.assertEqual(decisions[('Χετταία', 'Χετταία', 'fem nom sg', 'adjective')]['pt'], 'heteia')
        self.assertEqual(decisions[('Μωαβιτῶν', 'Μωαβίτης', 'masc gen pl', 'noun')]['pt'], 'dos moabitas')
        fear = next(entry for record, entry in zip(self.audit['records'], supplement['entries'])
                    if record['form'] == 'ἐφοβήθην' and record['lemma'] == 'φοβέομαι')
        self.assertEqual(fear['pt'], 'temi')
        self.assertIn('Passiva', fear['morfologia'])

    def test_new_context_or_changed_audit_requires_review(self):
        for mutation in ['reference', 'count', 'audit']:
            changed = copy.deepcopy(self.reviewed)
            if mutation == 'reference':
                changed['entries'][0]['references'].append('gn 1:1')
            elif mutation == 'count':
                changed['entries'][0]['occurrences'] += 1
            else:
                changed['audit_sha256'] = 'outdated'
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'reviewed.json'
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    load_reviewed(path, self.audit_path, self.audit)

    def test_duplicate_or_proper_name_is_rejected(self):
        for mutation in ['duplicate', 'proper noun']:
            changed = copy.deepcopy(self.reviewed)
            if mutation == 'duplicate':
                changed['entries'].append(changed['entries'][0])
            else:
                record = next(row for row in self.audit['records'] if row['pos'] == 'proper noun')
                changed['entries'].append({**record, 'pt': 'nome indevido',
                                           'estado': 'APLICAR_BETA', 'evidence': ['teste']})
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'reviewed.json'
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    load_reviewed(path, self.audit_path, self.audit)


if __name__ == '__main__':
    unittest.main()
