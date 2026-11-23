#!/usr/bin/env python3
"""Corrige as divergências técnicas comprovadas código/descrição do lote atual."""
import argparse
import hashlib
import json

from tools.audit.apply_morphology_priorities import replacements
from tools.audit.audit_tm import ROOT, write

SOURCE = 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json'
OUTPUT = 'reports/audit/morfologia-codigo-descricao/aplicacao.json'

CHANGES = [
 ('166', 4, 'αἰωνίου', {'abrev_morf': ('Adj-GFS', 'Adj-GFS/NS'), 'morfologia': ('Adjetivo - Genitivo Neutro Singular', 'Adjetivo - Genitivo Feminino/Neutro Singular')}),
 ('2052', 3, 'ἐριθείας', {'morfologia': ('Substantivo - Genitivo Feminino Singular/Acusativo Feminino Plural', 'Substantivo - Genitivo Feminino Singular')}),
 ('2064', 52, 'ἔρχου', {'abrev_morf': ('V-PIM-2S', 'V-PMM-2S')}),
 ('2478', 0, 'ἰσχυρά', {'abrev_morf': ('Adj-ANP', 'Adj-ANP/FS')}),
 ('2478', 11, 'ἰσχυρῶν', {'morfologia': ('Adjetivo - Genitivo Masculino/Feminino Plural', 'Adjetivo - Genitivo Feminino Plural')}),
 ('2588', 4, 'καρδίας', {'abrev_morf': ('S-GFS', 'S-GFS/AFP')}),
 ('2605', 4, 'καταγγέλλουσιν', {'abrev_morf': ('V-PIA-3P', 'V-PIA-3P/V-PPA-DMP'), 'morfologia': ('Verbo - Presente Indicativo/Particípio Ativa - 3ª Pessoa/Dativo Plural', 'Verbo - Presente Indicativo Ativa - 3ª Pessoa Plural/Presente Particípio Ativa - Dativo Masculino Plural')}),
 ('2634', 1, 'κατακυριεύουσιν', {'morfologia': ('Verbo - Presente Indicativo/Subjuntivo Ativa - 3ª Pessoa/Dativo Plural', 'Verbo - Presente Indicativo Ativa - 3ª Pessoa Plural')}),
 ('2635', 3, 'καταλαλοῦσιν', {'morfologia': ('Verbo - Presente Indicativo/Subjuntivo Ativa - 3ª Pessoa/Dativo Plural', 'Verbo - Presente Indicativo Ativa - 3ª Pessoa Plural')}),
 ('3498', 8, 'νεκρῶν', {'abrev_morf': ('Adj-GMP', 'Adj-GM/NP'), 'morfologia': ('Adjetivo - Genitivo Neutro Plural', 'Adjetivo - Genitivo Masculino/Neutro Plural')}),
 ('3860', 11, 'παραδίδοται', {'morfologia': ('Verbo - Presente Indicativo Média ou Passiva - 3ª Pessoa Singular', 'Verbo - Presente Indicativo Passiva - 3ª Pessoa Singular')}),
 ('4863', 22, 'συνηγάγετέ', {'abrev_morf': ('V-AI/MA-2P', 'V-AIA-2P')}),
 ('5100', 5, 'τινες', {'abrev_morf': ('IPro-NMP', 'IPro-NM/FP'), 'morfologia': ('Pronome Interrogativo/Indefinido - Nominativo Neutro Plural', 'Pronome Interrogativo/Indefinido - Nominativo Masculino/Feminino Plural')}),
]


def sha(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()


def items():
    return [{'strong': strong, 'flexao': flexao, 'forma': form,
             'alteracoes': {field: {'antes': before, 'depois': after} for field, (before, after) in changes.items()}}
            for strong, flexao, form, changes in CHANGES]


def state(text, rows):
    data = json.loads(text); values = []
    for row in rows:
        actual = data[row['strong']]['flexoes'][row['flexao']]
        if actual['grego'] != row['forma']: raise ValueError(f'Forma deslocada: {row["strong"]}/{row["flexao"]}.')
        for field, change in row['alteracoes'].items():
            values.append(actual[field] == change['depois'])
            if actual[field] not in {change['antes'], change['depois']}:
                raise ValueError(f'Campo desatualizado: {row["strong"]}/{row["flexao"]}/{field}.')
    if all(values): return 'aplicado'
    if not any(values): return 'pendente'
    raise ValueError('Lote parcialmente aplicado.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True); mode.add_argument('--apply', action='store_true'); mode.add_argument('--check', action='store_true')
    args = parser.parse_args(); path = ROOT / SOURCE; text = path.read_text(encoding='utf-8'); rows = items(); current = state(text, rows)
    if args.check and current != 'aplicado': raise ValueError('Correções ainda não aplicadas.')
    result = text if current == 'aplicado' else replacements(text, rows)
    if current == 'pendente' and replacements(result, rows, after=False) != text: raise ValueError('Alteração fora dos campos autorizados.')
    report = {'estado': 'APLICADO', 'fonte': SOURCE, 'antes_sha256': sha(text) if current == 'pendente' else None,
              'depois_sha256': sha(result), 'registros_corrigidos': len(rows),
              'campos_tecnicos_corrigidos': sum(len(r['alteracoes']) for r in rows), 'itens': rows,
              'pendencia_preservada': {'strong': '1510', 'flexao': 49, 'forma': 'ὧν\\u200b',
                  'motivo': 'Registro contaminado com marcador invisível e metadados incompatíveis; preservado para revisão humana conforme AGENTS.md.'}}
    if args.apply and current == 'pendente': write(path, result)
    target = ROOT / OUTPUT; target.parent.mkdir(parents=True, exist_ok=True); write(target, json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(rows)} registros e {report["campos_tecnicos_corrigidos"]} campos técnicos corrigidos; G1510/49 preservado.')


if __name__ == '__main__': main()
