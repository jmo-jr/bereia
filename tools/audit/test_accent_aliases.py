import copy
import unittest

from tools.audit.accent_alias_rules import AccentAliases, regular_pair, target_signature
from tools.audit.build_accent_aliases import build


def fixture():
    flex = {'grego': 'καλός', 'transliteracao': 'kalos', 'ocorrencias': '1', 'traducao': 'bom', 'pt': 'bom',
            'abrev_morf': 'Adj-NMS', 'morfologia': 'Adjetivo - Nominativo Masculino Singular', 'lxx': [], 'ocorrencias_lxx': 0}
    lexicon = {'2570': {'verbete': 'G2570: bom', 'flexoes': [flex]}}
    entry = {'strongs': '2570', **flex, 'verbete': 'G2570: bom'}
    dictionary, index = {'καλός': entry}, {'καλός': [{'strongs': '2570', 'flexao': 0}]}
    row = {'forma_tm': 'καλὸς', 'classe': 'ausente', 'referencias': ['MT 1:1#1', 'MT 1:2#1'],
           'candidatos_sem_diacriticos': [{'strong': '2570', 'flexao': 0, 'forma': 'καλός'}],
           'evidencias': [{'strong_fonte': '2570', 'morfologia_fonte': 'A-NSM', 'referencias': ['MT 1:1#1']}]}
    return row, lexicon, dictionary, index


class AliasTests(unittest.TestCase):
    def test_only_final_acute_grave_is_accepted(self):
        self.assertTrue(regular_pair('καλὸς', 'καλός'))
        self.assertTrue(regular_pair('Καλός', 'καλὸς'))
        for a, b in [('τὶς', 'τίς'), ('τὶ', 'τί'), ('τὶνος', 'τίνος'), ('ἀρχῇ', 'ἀρχή'),
                     ('γάμων', 'γαμῶν'), ('ἕκτος', 'ἐκτός'), ('καλὸς ', 'καλός '), ('νὺχθ᾽', 'νύχθ᾽')]:
            self.assertFalse(regular_pair(a, b), (a, b))

    def test_partial_evidence_creates_only_a_scoped_alias(self):
        row, lexicon, dictionary, index = fixture()
        before = copy.deepcopy((row, lexicon, dictionary, index))
        rows, aliases, pending = build({'formas': [row]}, lexicon, dictionary, index)
        self.assertEqual(aliases[0]['referencias'], ['MT 1:1#1'])
        self.assertEqual(pending[0]['referencias'], ['MT 1:2#1'])
        self.assertEqual(aliases[0]['tokens_validados'], 1)
        self.assertEqual((row, lexicon, dictionary, index), before)

    def test_wrong_strong_morphology_and_conflicting_evidence_do_not_authorize(self):
        for field, value in [('strong_fonte', '2570 '), ('morfologia_fonte', 'A-DSF')]:
            row, lexicon, dictionary, index = fixture()
            row['evidencias'][0][field] = value
            self.assertEqual(build({'formas': [row]}, lexicon, dictionary, index)[1], [])
        row, lexicon, dictionary, index = fixture()
        row['evidencias'].append({'strong_fonte': '999', 'morfologia_fonte': 'A-NSM', 'referencias': ['MT 1:1#1']})
        self.assertEqual(build({'formas': [row]}, lexicon, dictionary, index)[1], [])

    def test_homographic_target_is_not_implicitly_selected(self):
        row, lexicon, dictionary, index = fixture()
        index['καλός'].append({'strongs': '2570', 'flexao': 1})
        self.assertEqual(build({'formas': [row]}, lexicon, dictionary, index)[1], [])

    def test_reference_and_evidence_book_are_required(self):
        row, lexicon, dictionary, index = fixture()
        aliases = build({'formas': [row]}, lexicon, dictionary, index)[1]
        manifest = {'schema_version': 1, 'regra': 'agudo_grave_final_contextual_v1', 'origens_controladas': ['καλὸς'], 'aliases': aliases}
        resolver = AccentAliases(manifest, dictionary, index, {'MT'})
        self.assertEqual(resolver.resolve('καλὸς', 'MT 1:1#1')['estado'], 'resolvido')
        self.assertEqual(resolver.resolve('καλὸς', 'MT 1:2#1')['estado'], 'pendente')
        self.assertEqual(resolver.resolve('καλὸς')['estado'], 'pendente')
        self.assertEqual(AccentAliases(manifest, dictionary, index).resolve('καλὸς', 'MT 1:1#1')['estado'], 'pendente')
        self.assertEqual(resolver.resolve('καλῷ', 'MT 1:1#1')['estado'], 'fora_escopo')

    def test_translation_updates_propagate_but_morphology_changes_block(self):
        row, lexicon, dictionary, index = fixture()
        aliases = build({'formas': [row]}, lexicon, dictionary, index)[1]
        manifest = {'schema_version': 1, 'regra': 'agudo_grave_final_contextual_v1', 'origens_controladas': ['καλὸς'], 'aliases': aliases}
        previous = target_signature(dictionary['καλός'])
        dictionary['καλός']['pt'] = 'glosa revisada'
        self.assertEqual(target_signature(dictionary['καλός']), previous)
        self.assertEqual(AccentAliases(manifest, dictionary, index, {'MT'}).resolve('καλὸς', 'MT 1:1#1')['entrada']['pt'], 'glosa revisada')
        dictionary['καλός']['abrev_morf'] = 'Adj-AMS'
        self.assertEqual(AccentAliases(manifest, dictionary, index, {'MT'}).resolve('καλὸς', 'MT 1:1#1')['motivo'], 'destino_desatualizado')

    def test_duplicate_ref_is_not_merged_but_token_count_is_preserved(self):
        row, lexicon, dictionary, index = fixture()
        row['referencias'].append('MT 1:1#1')
        aliases = build({'formas': [row]}, lexicon, dictionary, index)[1]
        self.assertEqual(aliases[0]['referencias'], ['MT 1:1#1'])
        self.assertEqual(aliases[0]['tokens_validados'], 2)
        manifest = {'schema_version': 1, 'regra': 'agudo_grave_final_contextual_v1', 'origens_controladas': ['καλὸς'], 'aliases': aliases * 2}
        with self.assertRaises(ValueError): AccentAliases(manifest, dictionary, index, {'MT'})


if __name__ == '__main__':
    unittest.main()
