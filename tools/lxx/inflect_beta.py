"""Ajustes de flexão restritos ao suplemento beta; não escreve no léxico principal."""
from dataclasses import replace
from tools.flexiona_verbos import PortugueseConjugator


class BetaConjugator(PortugueseConjugator):
    # Uma análise passiva do grego não autoriza uma passiva portuguesa impossível.
    INTRANSITIVE = {'ir', 'vir', 'morrer', 'nascer', 'cair', 'chegar', 'partir',
                    'fugir', 'adoecer', 'claudicar', 'mancar', 'rastejar', 'desertar'}

    def _conjugate_predicate(self, phrase, lemma, morph):
        if morph.voice == 'passiva' and lemma.root.lower() in self.INTRANSITIVE:
            morph = replace(morph, voice='ativa')
        return super()._conjugate_predicate(phrase, lemma, morph)

    def agreed_participle(self, root, morph):
        word = self._past_participle(root)
        if morph.gender == 'feminino' and word.endswith('o'):
            word = word[:-1] + 'a'
        if morph.number == 'plural' and not word.endswith('s'):
            word += 's'
        return word

    def _conjugate_participle_phrase(self, phrase, lemma, morph):
        root = lemma.root.lower()
        passive = morph.voice == 'passiva'
        if morph.tense == 'presente':
            form = 'sendo ' + self.agreed_participle(root, morph) if passive else self._gerund(root)
            if lemma.reflexive and not passive:
                form += '-se'
        elif morph.tense in {'aoristo', 'perfeito'}:
            if passive:
                form = 'tendo sido ' + self.agreed_participle(root, morph)
            else:
                # O particípio de um tempo composto com ter não concorda com o sujeito.
                form = ('tendo se ' if lemma.reflexive else 'tendo ') + self._past_participle(root)
        elif morph.tense == 'futuro':
            form = 'prestes a ser ' + self.agreed_participle(root, morph) if passive else 'prestes a ' + root
            if lemma.reflexive and not passive:
                form += '-se'
        else:
            return ''
        return phrase[:lemma.start] + self._restore_case(lemma.root, form) + phrase[lemma.end:]

    def _conjugate_infinitive_phrase(self, phrase, lemma, morph):
        root = lemma.root.lower()
        if morph.voice == 'passiva':
            prefix = {'perfeito': 'ter sido ', 'futuro': 'vir a ser '}.get(morph.tense, 'ser ')
            form = prefix + self._past_participle(root)
        elif morph.tense == 'perfeito':
            form = ('ter se ' if lemma.reflexive else 'ter ') + self._past_participle(root)
        else:
            form = ('vir a ' if morph.tense == 'futuro' else '') + root + ('-se' if lemma.reflexive else '')
        return phrase[:lemma.start] + self._restore_case(lemma.root, form) + phrase[lemma.end:]
