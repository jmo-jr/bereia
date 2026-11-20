"""Consulta experimental, isolada da produção; somente literal e NFC."""
from tools.audit.audit_tm import index_lexicon, nfc


class StrictLookup:
    def __init__(self, lexicon):
        self.literal, self.canonical, _, _ = index_lexicon(lexicon)

    def resolve(self, form):
        if form in self.literal:
            entries, match = self.literal[form], 'literal'
        elif nfc(form) in self.canonical:
            entries, match = self.canonical[nfc(form)], 'nfc'
        else:
            entries, match = [], 'ausente'
        # Mesmo havendo uma entrada literal, conservar outras análises
        # canonicamente equivalentes. A preferência é de grafia, não de análise.
        if entries:
            entries = self.canonical[nfc(form)]
        return {'forma_tm': form, 'correspondencia': match,
                'estado': 'ausente' if not entries else 'unica' if len(entries) == 1 else 'multipla',
                'entradas': [dict(row) for row in entries]}
