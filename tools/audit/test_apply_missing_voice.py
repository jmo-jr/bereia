import copy
import json
import unittest
from collections import Counter

from tools.audit.apply_missing_voice import ROOT,MANIFEST,validate_manifest
from tools.audit.apply_morphology_priorities import plan,replacements,sha
from tools.audit.audit_morphology import audit,compare,source_analysis,description_differences,parse_code


class MissingVoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/MANIFEST).read_text())
        current=(ROOT/cls.manifest['fonte']).read_text()
        if sha(current) not in {cls.manifest['antes_sha256'],cls.manifest['depois_sha256']}:
            fixture=json.loads(current)
            for item in cls.manifest['itens']:
                fixture[item['strong']]['flexoes'][item['flexao']]=copy.deepcopy(item['campos_antes'])
            current=json.dumps(fixture,ensure_ascii=False,indent=2)+'\n'
            cls.manifest['antes_sha256']=sha(current)
            cls.manifest['depois_sha256']=sha(replacements(current,cls.manifest['itens']))
        cls.before=(replacements(current,cls.manifest['itens'],after=False)
                    if sha(current)==cls.manifest['depois_sha256'] else current)
        cls.after,_=plan(cls.before,cls.manifest)

    def test_47_records_and_94_fields_preserve_every_other_byte(self):
        validate_manifest(self.manifest)
        old,new=json.loads(self.before),json.loads(self.after)
        self.assertEqual(list(old),list(new))
        changed=[]
        for s,g in old.items():
            self.assertEqual(list(g),list(new[s]))
            self.assertEqual(len(g['flexoes']),len(new[s]['flexoes']))
            for i,f in enumerate(g['flexoes']):
                nf=new[s]['flexoes'][i]
                self.assertEqual(list(f),list(nf))
                for k,v in f.items():
                    if v!=nf[k]:changed.append((s,i,k))
        expected={(r['strong'],r['flexao'],k) for r in self.manifest['itens'] for k in r['alteracoes']}
        self.assertEqual(set(changed),expected)
        self.assertEqual(len(changed),94)
        self.assertEqual(replacements(self.after,self.manifest['itens'],after=False),self.before)

    def test_voices_and_descriptions_agree_without_changing_other_features(self):
        self.assertEqual(Counter(r['voz_revisada'] for r in self.manifest['itens']),Counter({'A':38,'M':9}))
        for r in self.manifest['itens']:
            old=r['campos_antes'];new=r['alteracoes']
            self.assertEqual(description_differences(new['abrev_morf']['depois'],new['morfologia']['depois']),[])
            a=parse_code(old['abrev_morf']);b=parse_code(new['abrev_morf']['depois'])
            self.assertEqual(a,[{k:v for k,v in f.items() if k!='voz'} for f in b])
            self.assertEqual({f['voz'] for f in b},{r['voz_revisada']})

    def test_future_middle_deponent_mapping_is_strictly_scoped(self):
        for s in ['1510','3918']:
            self.assertEqual(compare('V-FIM-3S','V-FDI-3S',s),'compativel')
            self.assertEqual(compare('V-FIA-3S','V-FDI-3S',s),'divergente')
        self.assertEqual(compare('V-FIM-3S','V-FDI-3S'),'nao_comparavel')
        self.assertEqual(compare('V-FIM-3S','V-FDI-3S','1096'),'nao_comparavel')
        self.assertIsNone(source_analysis('V-FNI','1510'))
        self.assertIsNone(source_analysis('V-FOI-3S','1510'))
        self.assertEqual(source_analysis('V-FDN','1510')[0]['voz'],'M')
        self.assertEqual(source_analysis('V-FDP-ASN','1510')[0]['voz'],'M')

    def test_generic_class_is_visible_in_coverage_but_not_a_missing_voice_error(self):
        generic=self.manifest['nao_aplicavel'][0]
        l={'1507':{'lema':'εἱλίσσω','flexoes':[generic['campos_preservados']]}}
        r=audit(l,{}, {})
        self.assertEqual(r['achados'],[])
        self.assertEqual(r['resumo']['cobertura_codigos']['registros_verbais_genericos_sem_analise_flexional'],1)
        old,new=json.loads(self.before),json.loads(self.after)
        self.assertEqual(old['1507'],new['1507'])
        self.assertEqual(old['1510']['flexoes'][49],new['1510']['flexoes'][49])
        self.assertEqual(old['3739'],new['3739'])
        self.assertEqual(old['746'],new['746'])

    def test_voice_only_evidence_preserves_original_deponent_codes_and_alignment_limits(self):
        no_alignment=[r for r in self.manifest['itens'] if not r['evidencia_voz']]
        self.assertEqual(len(no_alignment),7)
        for r in self.manifest['itens']:
            for e in r['evidencia_voz']:
                self.assertEqual(source_analysis(e['codigo_original'],r['strong'])[0]['voz'],r['voz_revisada'])
                if r['voz_revisada']=='M':self.assertTrue(e['codigo_original'].startswith('V-FD'))
            self.assertTrue(all(e.get('alinhamento')=='alinhado' for e in r['ocorrencias_tm'] if 'strong_fonte' in e))

    def test_all_old_voice_alerts_are_resolved_without_new_internal_contradictions(self):
        old=audit(json.loads(self.before),{}, {})
        new=audit(json.loads(self.after),{}, {})
        self.assertEqual(sum(x['tipo']=='codigo_sem_voz' for x in old['achados']),47)
        self.assertEqual(sum(x['tipo']=='codigo_sem_voz' for x in new['achados']),0)
        self.assertEqual(sum(x['tipo']=='codigo_descricao' for x in old['achados']),
                         sum(x['tipo']=='codigo_descricao' for x in new['achados']))

    def test_idempotence_and_manifest_scope_guards(self):
        self.assertEqual(plan(self.after,self.manifest),(self.after,'aplicado'))
        with self.assertRaises(ValueError):plan(self.before+' ',self.manifest)
        m=copy.deepcopy(self.manifest);m['itens'][0]['alteracoes']['traducao']={'antes':'a','depois':'b'}
        with self.assertRaisesRegex(ValueError,'Somente código'):validate_manifest(m)
        m=copy.deepcopy(self.manifest);m['itens'][0]['alteracoes']['abrev_morf']['depois']='V-PIA-3P'
        with self.assertRaisesRegex(ValueError,'além da indicação'):validate_manifest(m)
        m=copy.deepcopy(self.manifest);m['itens'][0]['strong']='9999'
        with self.assertRaisesRegex(ValueError,'Grupo fora'):validate_manifest(m)


if __name__=='__main__':unittest.main()
