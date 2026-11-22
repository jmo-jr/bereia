import copy
import json
import unittest
from pathlib import Path

from tools.audit.promote_lemma_verbetes import ROOT, MANIFEST, plan, sha
from tools.audit.apply_approved_accents import members


def replace_roots(text, rows, field):
    spans = {s: (a, b) for s, a, b in members(text)}
    edits = []
    for row in rows:
        if row['estado'] != 'APLICAR':
            continue
        a, _ = spans[row['strong']]
        x, y = next((x, y) for k, x, y in members(text, a) if k == 'verbete')
        edits.append((x, y, json.dumps(row[field], ensure_ascii=False)))
    for a, b, value in sorted(edits, reverse=True):
        text = text[:a] + value + text[b:]
    return text


class PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / MANIFEST).read_text())
        current = (ROOT / cls.manifest['fonte']).read_text()
        cls.before = replace_roots(current, cls.manifest['itens'], 'antes')
        assert sha(cls.before) == cls.manifest['antes_sha256']
        cls.after, _ = plan(cls.before, cls.manifest)

    def test_preserves_every_field_except_selected_lemma_verbetes(self):
        before, after = json.loads(self.before), json.loads(self.after)
        self.assertEqual(list(before), list(after))
        changed = []
        for strong, old in before.items():
            new = after[strong]
            self.assertEqual(list(old), list(new))
            self.assertEqual(old['flexoes'], new['flexoes'])
            if old['verbete'] != new['verbete']:
                changed.append(strong)
            new['verbete'] = old['verbete']
            self.assertEqual(old, new)
        expected = [r['strong'] for r in self.manifest['itens'] if r['estado'] == 'APLICAR']
        self.assertEqual(changed, expected)
        self.assertEqual(len(changed), 73)

    def test_preserves_formatting_and_is_idempotent(self):
        self.assertEqual(replace_roots(self.after, self.manifest['itens'], 'antes'), self.before)
        again, state = plan(self.after, self.manifest)
        self.assertEqual(again, self.after)
        self.assertEqual(state, 'aplicado')

    def test_refuses_unreviewed_input(self):
        with self.assertRaisesRegex(ValueError, 'Fonte alterada'):
            plan(self.before.replace('G1: Alfa', 'G1: alfa', 1), self.manifest)

    def test_refuses_changed_decision_and_duplicate_strong(self):
        bad = copy.deepcopy(self.manifest)
        row = next(r for r in bad['itens'] if r['estado'] == 'APLICAR')
        row['depois'] += ', outra opção não revisada'
        with self.assertRaisesRegex(ValueError, 'Resultado diverge'):
            plan(self.before, bad)
        bad = copy.deepcopy(self.manifest)
        bad['itens'].append(copy.deepcopy(bad['itens'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicado'):
            plan(self.before, bad)

    def test_arche_homographs_and_overrides_untouched(self):
        before, after = json.loads(self.before), json.loads(self.after)
        self.assertEqual(before['746'], after['746'])
        forms = {f['grego']: f for f in after['746']['flexoes']}
        self.assertIn('ἀρχῇ', forms)
        self.assertIn('ἀρχή', forms)
        self.assertEqual(forms['ἀρχῇ']['pt'], 'no princípio')
        overrides = lambda lex: sum('verbete' in f for g in lex.values() for f in g['flexoes'])
        self.assertEqual(overrides(before), 4784)
        self.assertEqual(overrides(after), 4784)
        for strong in ['3739', '2303', '2878', '3134']:
            self.assertEqual(before[strong], after[strong])

    def test_effective_projection_changes_only_three_inherited_verbetes(self):
        before, after = json.loads(self.before), json.loads(self.after)
        def project(lex):
            result = {}
            for strong, group in lex.items():
                for flex in group['flexoes']:
                    result.setdefault(flex['grego'], (strong, flex.get('verbete', group['verbete'])))
            return result
        old, new = project(before), project(after)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({f for f in old if old[f] != new[f]}, {'αἰτοῦντί', 'ἀσπάσησθε', 'ἔσχατον'})
        self.assertEqual(json.loads(self.after)['2864']['verbete'], 'G2864: cabelo, cabeleira')
        self.assertIn('imposto ou taxa', json.loads(self.after)['5056']['verbete'])


if __name__ == '__main__':
    unittest.main()
