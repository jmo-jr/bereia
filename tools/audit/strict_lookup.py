"""Consulta sem retirada de marcas; NFC e equivalência por caixa autorizada."""
from tools.audit.audit_tm import index_lexicon, nfc


class StrictLookup:
    def __init__(self, lexicon, ignore_case=True):
        self.literal, self.canonical, self.case, _ = index_lexicon(lexicon)
        self.ignore_case = ignore_case

    def resolve(self, form):
        if form in self.literal:
            entries, match = self.literal[form], 'literal'
        elif nfc(form) in self.canonical:
            entries, match = self.canonical[nfc(form)], 'nfc'
        elif self.ignore_case and nfc(form.lower()) in self.case:
            entries, match = self.case[nfc(form.lower())], 'caixa'
        else:
            entries, match = [], 'ausente'
        # Mesmo havendo uma entrada literal, conservar outras análises
        # canonicamente equivalentes. A preferência é de grafia, não de análise.
        if entries and match != 'caixa':
            entries = self.canonical[nfc(form)]
        return {'forma_tm': form, 'correspondencia': match,
                'estado': 'ausente' if not entries else 'unica' if len(entries) == 1 else 'multipla',
                'entradas': [dict(row) for row in entries]}
