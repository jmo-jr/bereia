import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.lxx.generate_beta import ROOT, read, load_reviewed, BetaNominalInflector
from tools.lxx.inflect_beta import BetaConjugator
from tools.lxx.prepare_ancientbible_application import render_approved


class ApprovedAncientBibleTests(unittest.TestCase):
    def test_all_approved_candidates_are_applied_without_strong(self):
        reviewed = read(ROOT / 'tools/lxx/reviewed_step5.json')
        proposal = read(ROOT / reviewed['explicit_approval']['review_file'])
        audit_path = ROOT / 'tools/relatorios/lxx-tbesg-cobertura-etapa4.json'
        audit = read(audit_path)
        decisions, _ = load_reviewed(ROOT / 'tools/lxx/reviewed_step5.json', audit_path, audit)
        supplement = read(ROOT / 'src/_data/lxx/supplement-beta.json')
        self.assertEqual({identifier for row in decisions.values() for identifier in row['approved_candidate_ids']},
                         {row['id'] for row in proposal['com_candidato']})
        self.assertEqual(sum(row['occurrences'] for row in decisions.values()), 112)
        for record, entry in zip(audit['records'], supplement['entries']):
            key = tuple(record[field] for field in ['form', 'lemma', 'parsing', 'pos'])
            if key in decisions:
                self.assertEqual(entry['pt'], decisions[key]['pt'])
                self.assertEqual(entry['pt'], entry['traducao'])
                self.assertEqual(entry['forma'], record['form'])
                self.assertNotIn('strongs', entry)
                self.assertNotIn('verbete', entry)
        self.assertIn(' / ', next(row['pt'] for row in decisions.values() if row['form'] == 'ἄπεστιν'))
        self.assertIn('reúna', next(row['pt'] for row in decisions.values() if row['form'] == 'συνέστω'))

    def test_uncertainty_cannot_be_released_without_explicit_approval(self):
        reviewed = read(ROOT / 'tools/lxx/reviewed_step5.json')
        audit_path = ROOT / 'tools/relatorios/lxx-tbesg-cobertura-etapa4.json'
        for mutation in ['approval', 'hash', 'candidate']:
            changed = copy.deepcopy(reviewed)
            if mutation == 'approval':
                changed.pop('explicit_approval')
            elif mutation == 'hash':
                changed['explicit_approval']['review_sha256'] = 'changed'
            else:
                changed['entries'][0]['approved_candidate_ids'] = ['not-approved']
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'reviewed.json'
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    load_reviewed(path, audit_path, read(audit_path))

    def render(self, lemma, parsing, pos, base):
        return render_approved({'lemma': lemma, 'parsing': parsing, 'pos': pos},
                               base, BetaConjugator(), BetaNominalInflector())[0]

    def test_future_perfect_and_nominal_agreement(self):
        self.assertEqual(self.render('κράζω', 'futperf ind mid 1st sg', 'verb', 'clamar'), 'terei clamado')
        self.assertEqual(self.render('καλέω', 'futperf ind mid/pass 3rd sg', 'verb', 'chamar'),
                         'terá chamado / terá sido chamado')
        self.assertEqual(self.render('ἱερόδουλος', 'masc dat pl', 'noun', 'cortesãs do templo'),
                         'aos cortesãos do templo')
        self.assertEqual(self.render('ἄπληστος', 'masc nom sg comp', 'adjective', 'insaciável'),
                         'mais insaciável')

    def test_missing_verbal_analysis_keeps_approved_base(self):
        self.assertEqual(self.render('διορίζω', 'masc acc sg', 'participle', 'determinar'), 'determinar')
        self.assertEqual(self.render('τρυφή', 'aor ind act 3rd pl', 'verb', 'autoindulgência'), 'autoindulgência')


if __name__ == '__main__':
    unittest.main()
