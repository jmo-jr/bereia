"""Regras estritas e determinísticas de equivalência contextual de acento."""
import hashlib
import json
import unicodedata as ud


def case_key(form):
    return ud.normalize('NFC', form.lower())


def regular_pair(origin, target):
    a, b = (ud.normalize('NFD', s.lower()) for s in (origin, target))
    if a.replace('\u0300', '\u0301') in {ud.normalize('NFD', s) for s in ('τίς', 'τί')}:
        return False
    if len(a) != len(b) or a.replace('\u0300', '\u0301') != b.replace('\u0300', '\u0301'):
        return False
    differences = [i for i in range(len(a)) if a[i] != b[i]]
    if len(differences) != 1 or {a[differences[0]], b[differences[0]]} != {'\u0300', '\u0301'}:
        return False
    # Conservador: só letras gregas e marcas; elisão, hífen e espaços pendentes.
    if any(not (ud.category(c).startswith('M') or 'GREEK' in ud.name(c, '') and c.isalpha()) for c in a):
        return False
    vowels = [i for i, c in enumerate(a) if c in 'αεηιουω']
    return bool(vowels) and differences[0] > vowels[-1]


def target_signature(entry):
    # Traduções e contagens não definem identidade morfológica. Atualizações
    # aprovadas desses campos propagam-se a partir da entrada canônica.
    fields = [entry.get(k) for k in ('strongs', 'grego', 'abrev_morf')]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


class AccentAliases:
    def __init__(self, manifest, dictionary, form_index, valid_books=()):
        self.controlled, self.rules, self.valid_books = set(), {}, set(valid_books)
        if not manifest:
            return
        if manifest.get('schema_version') != 1 or manifest.get('regra') != 'agudo_grave_final_contextual_v1':
            raise ValueError('Manifesto de aliases de acento não reconhecido.')
        self.controlled = {case_key(f) for f in manifest['origens_controladas']}
        for alias in manifest['aliases']:
            target = alias['destino']
            entry = dictionary.get(target['grego'])
            refs = form_index.get(target['grego'], [])
            valid = (regular_pair(alias['origem'], target['grego']) and bool(entry) and
                     entry['strongs'] == target['strongs'] and target_signature(entry) == target['assinatura'] and
                     refs == [{'strongs': target['strongs'], 'flexao': target['flexao']}])
            for ref in alias['referencias']:
                key = (case_key(alias['origem']), ref)
                if key in self.rules:
                    raise ValueError('Mais de um alias para a mesma ocorrência.')
                self.rules[key] = (alias, entry, valid)

    def resolve(self, form, reference=None):
        key = case_key(form)
        if key not in self.controlled:
            return {'estado': 'fora_escopo'}
        if not reference or reference.split(' ', 1)[0] not in self.valid_books:
            return {'estado': 'pendente', 'motivo': 'referencia_ou_fonte_nao_validada'}
        selected = self.rules.get((key, reference))
        if not selected:
            return {'estado': 'pendente', 'motivo': 'ocorrencia_sem_equivalencia_validada'}
        alias, entry, valid = selected
        if not valid:
            return {'estado': 'pendente', 'motivo': 'destino_desatualizado'}
        return {'estado': 'resolvido', 'alias': alias, 'entrada': entry, 'referencia': reference}
