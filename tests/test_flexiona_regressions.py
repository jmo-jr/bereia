"""Regressões linguísticas comprovadas na consolidação dos verbetes."""
import unittest
from tools.flexiona_nao_verbos import PortugueseNominalInflector, extract_base_phrase
from tools.flexiona_verbos import PortugueseConjugator, Morphology


class NominalRegressions(unittest.TestCase):
    def setUp(self):
        self.inflector = PortugueseNominalInflector()

    def render(self, base, description):
        return self.inflector.expand_forms(base, self.inflector.parser.parse(description))[0]

    def test_portuguese_noun_gender_overrides_greek_gender(self):
        for word, gender, expected in [('caminho', 'Feminino', 'do caminho'),
                                       ('dia', 'Feminino', 'do dia'),
                                       ('profeta', 'Masculino', 'do profeta'),
                                       ('semente', 'Neutro', 'da semente'),
                                       ('multidão', 'Masculino', 'da multidão')]:
            with self.subTest(word=word):
                self.assertEqual(self.render(word, f'Substantivo - Genitivo {gender} Singular'), expected)

    def test_singular_lexical_heads_are_not_mutilated(self):
        self.assertEqual(self.render('mês', 'Substantivo - Nominativo Masculino Singular'), 'mês')
        self.assertEqual(self.render('luz', 'Substantivo - Nominativo Feminino Singular'), 'luz')
        self.assertEqual(self.render('Marcos', 'Substantivo - Genitivo Masculino Singular'), 'de Marcos')

    def test_plural_exceptions_and_adjective_gender(self):
        self.assertEqual(self.render('aceitável', 'Adjetivo - Nominativo Masculino Plural'), 'aceitáveis')
        self.assertEqual(self.render('notável', 'Adjetivo - Nominativo Masculino Plural'), 'notáveis')
        self.assertEqual(self.render('visível', 'Adjetivo - Nominativo Masculino Plural'), 'visíveis')
        self.assertEqual(self.render('ancião', 'Adjetivo - Nominativo Feminino Plural'), 'anciãs')
        self.assertEqual(self.render('bom', 'Adjetivo - Genitivo Feminino Plural'), 'das boas')

    def test_article_contracts_only_once(self):
        self.assertEqual(self.render('o', 'Artigo - Genitivo Feminino Singular'), 'da')
        self.assertEqual(self.render('o', 'Artigo - Dativo Masculino Plural'), 'aos')

    def test_parenthetical_commas_do_not_truncate_gloss(self):
        self.assertEqual(extract_base_phrase({'verbete':'G696: prata (o metal, nos artigos ou moeda), dinheiro'}), 'prata')


class VerbalRegressions(unittest.TestCase):
    def test_regular_radical_spelling(self):
        conjugator = PortugueseConjugator()
        for lemma, expected in [('tocar', 'toque'), ('negar', 'negue'),
                                ('lançar', 'lance'), ('conhecer', 'conheça')]:
            with self.subTest(lemma=lemma):
                self.assertEqual(conjugator._conjugate_simple_verb(lemma, 'presente_subjuntivo', 2), expected)

    def test_passive_participle_agrees_with_plural_subject(self):
        conjugator = PortugueseConjugator()
        morph = Morphology(tense='aoristo', mood='indicativo', voice='passiva', person=3, number='plural')
        self.assertEqual(conjugator.build_phrase('conduzir', morph)[1], 'foram conduzidos')
