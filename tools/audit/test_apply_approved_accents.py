import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.audit.apply_approved_accents import LEXICON, check_applied, plan_append, selected, sha


def fixture():
    flex = {'grego': 'ἀρχή', 'transliteracao': 'archē', 'ocorrencias': '1',
            'traducao': 'princípio', 'pt': 'princípio', 'abrev_morf': 'S-NFS',
            'morfologia': 'Substantivo - Nominativo Feminino Singular',
            'lxx': [], 'ocorrencias_lxx': 0}
    lexicon = {'746': {'lema': 'ἀρχή', 'verbete': 'Texto com "flexoes": [] e } dentro da string', 'flexoes': [flex]},
               '746 ': {'lema': None, 'verbete': 'Preservar Strong literal', 'flexoes': [copy.deepcopy(flex)]}}
    draft = {**flex, 'grego': 'ἀρχὴ', 'ocorrencias': '2'}
    item = {'id': 'test:1', 'estado': 'SUGERIR', 'sinais': [], 'aplicado': False,
            'forma_tm': 'ἀρχὴ', 'referencias_sem_parsing_alinhado': [],
            'candidatos': [{'strong': '746', 'flexao': 0, 'campos_atuais': flex}],
            'minuta_inclusao': draft, 'referencias_tm': ['TESTE 1:1#1', 'TESTE 1:2#1'],
            'referencias_lxx_literal_nfc': []}
    return json.dumps(lexicon, ensure_ascii=False, indent=2) + '\n', item


class ApplyApprovedTests(unittest.TestCase):
    def test_preserves_raw_prefixes_order_and_literal_strong(self):
        text, item = fixture()
        after, applications = plan_append(text, [item])
        before, result = json.loads(text), json.loads(after)
        self.assertEqual(result['746']['flexoes'][:-1], before['746']['flexoes'])
        self.assertEqual(result['746 '], before['746 '])
        self.assertEqual(applications[0]['flexao'], 1)
        block = ',\n' + '\n'.join('      ' + line for line in json.dumps(item['minuta_inclusao'], ensure_ascii=False, indent=2).splitlines())
        self.assertEqual(after.replace(block, '', 1), text)

    def test_appends_multiple_entries_without_shifting_old_indices(self):
        text, first = fixture()
        second = copy.deepcopy(first)
        second['id'], second['forma_tm'], second['minuta_inclusao']['grego'] = 'test:2', 'Ἀρχὴ', 'Ἀρχὴ'
        after, applications = plan_append(text, [first, second])
        self.assertEqual([a['flexao'] for a in applications], [1, 2])
        self.assertEqual([f['grego'] for f in json.loads(after)['746']['flexoes']], ['ἀρχή', 'ἀρχὴ', 'Ἀρχὴ'])

    def test_uncertain_stale_duplicate_and_canonically_covered_forms_are_rejected(self):
        text, item = fixture()
        bad = copy.deepcopy(item); bad['estado'] = 'INCERTO'
        with self.assertRaises(ValueError): plan_append(text, [bad])
        bad = copy.deepcopy(item); bad['candidatos'][0]['campos_atuais']['pt'] = 'alterado'
        with self.assertRaisesRegex(ValueError, 'desatualizado'): plan_append(text, [bad])
        with self.assertRaises(ValueError): plan_append(text, [item, item])
        bad = copy.deepcopy(item); bad['forma_tm'] = bad['minuta_inclusao']['grego'] = 'α\u0313ρχη\u0301'
        with self.assertRaisesRegex(ValueError, 'NFC'): plan_append(text, [bad])

    def test_unknown_fields_or_reordered_fields_are_rejected(self):
        text, item = fixture()
        item['minuta_inclusao']['novo'] = 'não descartar'
        with self.assertRaisesRegex(ValueError, 'ordem'): plan_append(text, [item])

    def test_report_scope_and_application_are_checked(self):
        text, item = fixture()
        after, applications = plan_append(text, [item])
        approval = {'estado': 'APROVADO', 'tipo': 'agudo_grave', 'quantidade': 1,
                    'itens_ids': ['test:1'], 'aplicacoes': applications}
        self.assertEqual(selected({'itens': [item]}, approval), [item])
        check_applied(after, approval)
        with self.assertRaises(ValueError): check_applied(text, approval)
        approval['itens_ids'] = ['outro']
        with self.assertRaises(ValueError): selected({'itens': [item]}, approval)

    def test_cli_application_is_idempotent_and_rejects_modified_approval_report(self):
        text, item = fixture()
        after, applications = plan_append(text, [item])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / LEXICON; source.parent.mkdir(parents=True)
            source.write_text(text, encoding='utf-8')
            report_text = json.dumps({'itens': [item], 'fontes_sha256': {LEXICON: sha(text)}}, ensure_ascii=False)
            (root / 'report.json').write_text(report_text, encoding='utf-8')
            approval = {'estado': 'APROVADO', 'tipo': 'agudo_grave', 'quantidade': 1,
                'itens_ids': ['test:1'], 'aplicacoes': applications,
                'relatorio': 'report.json', 'relatorio_sha256': sha(report_text),
                'fonte_antes_sha256': sha(text), 'fonte_depois_sha256': sha(after)}
            (root / 'approval.json').write_text(json.dumps(approval), encoding='utf-8')
            code = 'from pathlib import Path; import sys; from tools.audit import apply_approved_accents as a; a.ROOT=Path(sys.argv[1]); sys.argv=["apply", "--approval", "approval.json"]; a.main()'
            command = [sys.executable, '-B', '-c', code, str(root)]
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(source.read_text(encoding='utf-8'), after)
            modified = source.stat().st_mtime_ns
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(source.stat().st_mtime_ns, modified)
            (root / 'report.json').write_text(report_text + ' ', encoding='utf-8')
            result = subprocess.run(command, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(source.read_text(encoding='utf-8'), after)


if __name__ == '__main__':
    unittest.main()
