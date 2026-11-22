import unittest
import json
import tempfile
from pathlib import Path
from tools.lxx.generate_beta import descriptions, BetaNominalInflector, form_key, render_translation, load_aliases, ROOT
from tools.lxx.inflect_beta import BetaConjugator
from tools.update_interlinear_translit import transliterate


class BetaTests(unittest.TestCase):
    def test_alias_evidence_and_proper_name_guard(self):
        path = ROOT / 'tools/lxx/tbesg_aliases_pt.json'
        aliases = json.loads(path.read_text())
        load_aliases(path, aliases['source_sha256'])
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / 'aliases.json'
            alias = aliases['entries']['ὀστοῦν']
            alias['allowed_pos'].append('proper noun')
            changed.write_text(json.dumps(aliases))
            with self.assertRaisesRegex(ValueError, 'nomes próprios'):
                load_aliases(changed, aliases['source_sha256'])
            alias['allowed_pos'].remove('proper noun')
            alias['source_entry']['meaning'] = 'invented evidence'
            changed.write_text(json.dumps(aliases))
            with self.assertRaisesRegex(ValueError, 'diverge da fonte'):
                load_aliases(changed, aliases['source_sha256'])

    def test_person_ambiguity_is_preserved(self):
        values = descriptions({'pos': 'verb', 'parsing': 'aor ind act 1st/3rd sg/pl'})
        self.assertTrue(any('1ª Pessoa' in value for value in values))
        self.assertTrue(any('3ª Pessoa' in value for value in values))
        self.assertFalse(any('1ª Pessoa Plural' in value for value in values))
        self.assertFalse(any('3ª Pessoa Singular' in value for value in values))

    def render(self, base, parsing, pos='verb'):
        record = {'pos': pos, 'parsing': parsing}
        return render_translation(record, base, descriptions(record), BetaConjugator(), BetaNominalInflector())

    def test_participle_voice_and_agreement(self):
        self.assertEqual(self.render('poupar', 'pres ptc pass fem nom pl', 'participle')[0], 'sendo poupadas')
        self.assertEqual(self.render('poupar', 'aor ptc act masc nom pl', 'participle')[0], 'tendo poupado')
        self.assertEqual(self.render('poupar', 'perf ptc pass fem nom pl')[0], 'tendo sido poupadas')

    def test_infinitive_voice_and_intransitive_deponent(self):
        self.assertEqual(self.render('poupar', 'pres inf pass')[0], 'ser poupado')
        self.assertEqual(self.render('encontrar-se', 'pres inf mid')[0], 'encontrar-se')
        self.assertEqual(self.render('ir', 'aor ind mid/pass 2nd sg')[0], 'foste')

    def test_unknown_analysis_stays_pending(self):
        pt, reason = self.render('poupar', 'futperf ind act 3rd sg')
        self.assertEqual(pt, '')
        self.assertTrue(reason)

    def test_compound_ordinal_and_invariant_cardinal(self):
        self.assertEqual(self.render('décimo oitavo', 'fem gen pl', 'adjective')[0], 'das décimas oitavas')
        self.assertEqual(self.render('dezesseis', 'masc gen pl', 'numeral')[0], 'de dezesseis')

    def test_nominal_regressions(self):
        inflector = BetaNominalInflector()
        self.assertEqual(inflector.expand_forms('mil', inflector.parser.parse('Substantivo - Feminino Acusativo Plural')), ['mil'])
        self.assertEqual(inflector.expand_forms('levita', inflector.parser.parse('Substantivo - Masculino Genitivo Plural')), ['dos levitas'])

    def test_lookup_does_not_rewrite_greek(self):
        form = 'ἐπ᾿'
        self.assertEqual(form_key(form), form_key("ἐπ'"))
        self.assertEqual(form, 'ἐπ᾿')
        self.assertEqual(transliterate('στέαρ'), 'stear')


if __name__ == '__main__':
    unittest.main()
