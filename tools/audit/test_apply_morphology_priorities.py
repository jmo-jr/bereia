import copy
import json
import unittest

from tools.audit.apply_morphology_priorities import MANIFEST, ROOT, plan, replacements, sha
from tools.audit.audit_morphology import description_differences


class MorphologyPriorityApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/MANIFEST).read_text())
        current=(ROOT/cls.manifest['fonte']).read_text()
        if sha(current) not in {cls.manifest['antes_sha256'],cls.manifest['depois_sha256']}:
            # Histórico do lote é um fixture, não uma proibição de revisões
            # posteriores do léxico. Hashes reais do manifesto não são alterados.
            fixture=json.loads(current)
            for item in cls.manifest['itens']:
                fixture[item['strong']]['flexoes'][item['flexao']]=copy.deepcopy(item['campos_antes'])
            current=json.dumps(fixture,ensure_ascii=False,indent=2)+'\n'
            cls.manifest['antes_sha256']=sha(current)
            cls.manifest['depois_sha256']=sha(replacements(current,cls.manifest['itens']))
        cls.before=(replacements(current,cls.manifest['itens'],after=False)
                    if sha(current)==cls.manifest['depois_sha256'] else current)
        assert sha(cls.before)==cls.manifest['antes_sha256']
        cls.after,_=plan(cls.before,cls.manifest)

    def test_only_seven_technical_fields_change_without_reordering_or_data_loss(self):
        old,new=json.loads(self.before),json.loads(self.after)
        self.assertEqual(list(old),list(new))
        expected={(i['strong'],i['flexao'],k) for i in self.manifest['itens'] for k in i['alteracoes']}
        actual=set()
        for strong,g in old.items():
            self.assertEqual(list(g),list(new[strong]))
            self.assertEqual(len(g['flexoes']),len(new[strong]['flexoes']))
            for i,flex in enumerate(g['flexoes']):
                newflex=new[strong]['flexoes'][i]
                self.assertEqual(list(flex),list(newflex))
                for field,value in flex.items():
                    if value!=newflex[field]:actual.add((strong,i,field))
        self.assertEqual(actual,expected)
        self.assertEqual(len(actual),7)
        restored=json.loads(self.after)
        for i in self.manifest['itens']:
            for field,c in i['alteracoes'].items():restored[i['strong']]['flexoes'][i['flexao']][field]=c['antes']
        self.assertEqual(restored,old)
        self.assertEqual(replacements(self.after,self.manifest['itens'],after=False),self.before)

    def test_corrected_fields_agree_without_choosing_neuter_for_occurrence(self):
        lex=json.loads(self.after)
        for i in self.manifest['itens']:
            f=lex[i['strong']]['flexoes'][i['flexao']]
            self.assertEqual(description_differences(f['abrev_morf'],f['morfologia']),[])
        self.assertEqual(lex['4687']['flexoes'][20]['abrev_morf'],'V-PPA-GM/NS')
        self.assertEqual(lex['4687']['flexoes'][20]['morfologia'],
            'Verbo - Presente Particípio Ativa - Genitivo Masculino/Neutro Singular')

    def test_preserves_invisible_marker_duplicate_and_lxx_metadata(self):
        old,new=json.loads(self.before),json.loads(self.after)
        self.assertEqual(new['1510']['flexoes'][49],old['1510']['flexoes'][49])
        self.assertEqual(new['1510']['flexoes'][49]['grego'],'ὧν\u200b')
        for i in [46,47,48]:
            self.assertEqual(new['1510']['flexoes'][i]['ocorrencias_lxx'],old['1510']['flexoes'][i]['ocorrencias_lxx'])
        self.assertEqual(new['1510']['flexoes'][48]['abrev_morf'],new['1510']['flexoes'][46]['abrev_morf'])
        self.assertEqual(new['3739'],old['3739'])
        self.assertEqual(new['746'],old['746'])

    def test_idempotence_and_stale_or_invalid_sources_are_rejected(self):
        self.assertEqual(plan(self.after,self.manifest),(self.after,'aplicado'))
        with self.assertRaisesRegex(ValueError,'Fonte desatualizada'):
            plan(self.before+' ',self.manifest)
        with self.assertRaises(json.JSONDecodeError):plan('{"a":1,}',self.manifest)

    def test_forbids_greek_translation_and_duplicate_record_mutations(self):
        for field in ['grego','traducao','pt','ocorrencias_lxx']:
            manifest=copy.deepcopy(self.manifest)
            i=manifest['itens'][0]
            i['alteracoes']={field:{'antes':i['campos_antes'][field],'depois':'não autorizado'}}
            with self.assertRaisesRegex(ValueError,'fora dos campos técnicos'):
                plan(self.before,manifest)
        manifest=copy.deepcopy(self.manifest);manifest['itens'].append(copy.deepcopy(manifest['itens'][0]))
        with self.assertRaisesRegex(ValueError,'duplicado'):plan(self.before,manifest)

    def test_rejects_tampered_decision_and_obsolete_review(self):
        manifest=copy.deepcopy(self.manifest)
        manifest['itens'][0]['campos_antes']['pt']='não revisado'
        with self.assertRaisesRegex(ValueError,'Registro revisado desatualizado'):plan(self.before,manifest)
        manifest=copy.deepcopy(self.manifest)
        manifest['itens'][0]['alteracoes']['morfologia']['depois']='Adjetivo - Genitivo Feminino Singular'
        with self.assertRaisesRegex(ValueError,'Resultado diverge'):plan(self.before,manifest)


if __name__=='__main__':unittest.main()
