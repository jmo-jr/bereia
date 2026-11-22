import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.audit.audit_morphology import (ROOT, LEXICON, load_lexicon, parse_code,
    description_differences, compare, audit, summarize_evidence, source_candidate, check_products)


def lex(form='ὢν', code='V-PPA-NMS', description='Verbo - Presente Particípio Ativa - Nominativo Masculino Singular', strong='1510'):
    return {strong:{'lema':'εἰμί','verbete':f'G{strong}: ser, estar, existir',
        'flexoes':[{'grego':form,'abrev_morf':code,'morfologia':description,
                    'traducao':'o que é','pt':'aquele que é','ocorrencias':'2'}]}}


def evidence(form='ὢν',strong='1510',code='V-PAP-NSM',ref='JO 1:1#1'):
    return {form:[{'referencia':ref,'forma_tm':form,'alinhamento':'alinhado',
                   'strong_fonte':strong,'morfologia_fonte':code}]}


class MorphologyAuditTests(unittest.TestCase):
    def test_strict_json_and_read_only_trailing_comma_tolerance(self):
        text='{"grego":"ὧν,}","outro":[1,],}'
        original=text[:]
        with self.assertRaises(json.JSONDecodeError):load_lexicon(text)
        data,issues=load_lexicon(text,True)
        self.assertEqual(data,{'grego':'ὧν,}','outro':[1]})
        self.assertEqual(len(issues),2)
        self.assertEqual(original,text)

    def test_other_json_errors_remain_fatal(self):
        with self.assertRaises(json.JSONDecodeError):load_lexicon('{"a": xyz,}',True)
        with self.assertRaisesRegex(ValueError,'duplicada'):load_lexicon('{"a":1,"a":2}')

    def test_participle_adapters_keep_voice_and_order(self):
        self.assertEqual(parse_code('V-PPA-NMS'),parse_code('V-PAP-NSM',True))
        self.assertEqual(compare('V-PPA-NMS','V-PAP-NSM'),'compativel')
        self.assertEqual(compare('V-PPA-NMS','V-PPP-NSM'),'divergente')
        self.assertEqual(compare('Ppro-GFS','P-GSF'),'compativel')
        self.assertEqual(compare('IPro-NMP','X-NPM'),'compativel')

    def test_combined_voices_moods_persons_and_nominal_features(self):
        self.assertEqual({r['voz'] for r in parse_code('V-PIM/P-3S')},{'M','P'})
        self.assertEqual({r['modo'] for r in parse_code('V-PI/MA-2P')},{'I','M'})
        self.assertEqual({r['pessoa'] for r in parse_code('V-IIA-1S/3P')},{'1','3'})
        self.assertEqual({r['caso'] for r in parse_code('S-A/NNP')},{'A','N'})
        self.assertEqual({r['genero'] for r in parse_code('Adj-NM/FS')},{'M','F'})
        self.assertEqual(len(parse_code('V-PPA-DMP/PIA-3P')),2)
        self.assertTrue(all(r['voz']=='A' for r in parse_code('V-FI/ASA-1S')))
        self.assertEqual(len(parse_code('V-PIA/PMA-2P')),2)

    def test_unknown_and_deponent_conventions_not_guessed(self):
        self.assertIsNone(parse_code('V-???'))
        self.assertIsNone(parse_code('V-PNI',True))
        self.assertEqual(compare('V-PPA-NMS','V-PNP-NSM'),'nao_comparavel')

    def test_missing_voice_is_partial_not_full_validation(self):
        self.assertNotIn('voz',parse_code('V-PP-NMS')[0])
        self.assertEqual(compare('V-PP-NMS','V-PAP-NSM'),'compativel_parcial')

    def test_pluperfect_synonyms_and_abbreviated_descriptions(self):
        self.assertEqual(description_differences('V-LIA-3S','Verbo - PluPerfeito Indicativo Ativa - 3ª Pessoa Singular'),[])
        self.assertEqual(description_differences('Inj','Inj'),[])
        self.assertEqual(description_differences('R-AMS','R - Acusativo Masculino Singular'),[])
        self.assertEqual(description_differences('PRT','Particula'),[])

    def test_combined_first_third_person_and_possessors_not_false_errors(self):
        self.assertEqual(description_differences('V-IIA-1S/3P',
             'Verbo - Imperfeito Indicativo Ativa - 1ª Singular/3ª Pessoa Plural'),[])
        self.assertEqual(description_differences('PPro-AF1P',
             'Pronome Pessoal/Possessivo - Acusativo Feminino Singular - 1ª Pessoa Plural'),[])
        self.assertEqual(description_differences('Ppro-GFS',
             'Pronome Pessoal/Possessivo - Genitivo Feminino Singular'),[])

    def test_neuter_syncretism_ignored_but_other_conflicts_detected(self):
        self.assertEqual(compare('S-ANS','N-NSN'),'compativel')
        self.assertEqual(description_differences('S-ANS','Substantivo - Nominativo/Acusativo Neutro Singular'),[])
        self.assertTrue(description_differences('Adj-GFS','Adjetivo - Genitivo Neutro Singular'))

    def test_no_accent_stripping_or_hidden_character_association(self):
        a=lex('ὧν\u200b'); before=copy.deepcopy(a)
        report=audit(a,evidence('ὧν','3739','R-GPN'),{})
        self.assertEqual(a,before)
        finding=next(r for r in report['achados'] if r['tipo']=='grafia_com_invisiveis_ou_espacos')
        self.assertEqual(finding['evidencias'],[])
        self.assertEqual(finding['candidato_evidencias'][0]['comparacao'],'strong_divergente')
        self.assertEqual(finding['estado'],'REVISAO_MANUAL')
        self.assertEqual(audit(lex('ἀρχῇ','S-DFS','Substantivo - Dativo Feminino Singular','746'),
            evidence('ἀρχή','746','N-NSF'),{})['achados'],[])

    def test_cross_strong_reference_and_class_mismatch_are_manual(self):
        a=lex(strong='3739');a['3739']['verbete']='G5607: ser, estar, existir'
        report=audit(a,evidence(),{'3739':[{'classes':['RelPro'],'linha':1}]})
        findings=[r for r in report['achados'] if r['tipo'] in {'classe_flexao_lema','strong_verbete_lema'}]
        self.assertEqual(len(findings),2)
        self.assertTrue(all(r['estado']=='REVISAO_MANUAL' for r in findings))

    def test_substantival_translation_does_not_change_participle(self):
        a=lex();report=audit(a,evidence(),{'1510':[{'classes':['V'],'linha':1}]})
        self.assertEqual(report['achados'],[])
        self.assertEqual(a['1510']['flexoes'][0]['abrev_morf'],'V-PPA-NMS')

    def test_single_nominal_ambiguity_ignored_without_hiding_independent_error(self):
        a=lex('λόγου','S-GMS','Substantivo - Genitivo Feminino Singular','3056')
        a['3056']['flexoes'][0]['ocorrencias']='1'
        r=audit(a,evidence('λόγου','3056','N-NSM'),{})
        self.assertIn('codigo_descricao',[x['tipo'] for x in r['achados']])
        self.assertNotIn('parsing_auxiliar_divergente',[x['tipo'] for x in r['achados']])
        a['3056']['flexoes'][0]['ocorrencias']=None
        r=audit(a,evidence('λόγου','3056','N-NSM'),{})
        self.assertIn('parsing_auxiliar_divergente',[x['tipo'] for x in r['achados']])

    def test_unaligned_evidence_never_supports_correction(self):
        entries=[{'referencia':'JO 1:1#1','alinhamento':'sequencia_divergente',
                  'strong_fonte':'1510','morfologia_fonte':'V-PAP-NSM'}]
        summaries=summarize_evidence(entries,'1510','V-PP-NMS')
        self.assertIsNone(source_candidate(summaries))
        self.assertIsNotNone(source_candidate(summarize_evidence(evidence()['ὢν'],'1510','V-PP-NMS')))

    def test_foreign_or_conflicting_evidence_blocks_single_candidate(self):
        rows=evidence()['ὢν']+evidence(strong='3739',ref='JO 1:2#1')['ὢν']
        self.assertIsNone(source_candidate(summarize_evidence(rows,'1510','V-PP-NMS')))
        rows=evidence()['ὢν']+evidence(code='V-PPP-NSM',ref='JO 1:2#1')['ὢν']
        self.assertIsNone(source_candidate(summarize_evidence(rows,'1510','V-PP-NMS')))

    def test_duplicates_and_legitimate_homographs_preserve_records(self):
        a=lex();a['1510']['flexoes'].append(copy.deepcopy(a['1510']['flexoes'][0]))
        before=copy.deepcopy(a);r=audit(a,evidence(),{})
        self.assertEqual(r['formas_repetidas'][0]['tipo'],'duplicata_integral')
        self.assertEqual(a,before)
        a={'2564':{'lema':'καλέω','flexoes':[{'grego':'καλῶν','abrev_morf':'V-PPA-NMS','morfologia':'Verbo - Presente Particípio Ativa - Nominativo Masculino Singular'}]},
           '2570':{'lema':'καλός','flexoes':[{'grego':'καλῶν','abrev_morf':'Adj-GMP','morfologia':'Adjetivo - Genitivo Masculino Plural'}]}}
        e=evidence('καλῶν','2564','V-PAP-NSM');e['καλῶν']+=evidence('καλῶν','2570','A-GPM',ref='JO 1:2#1')['καλῶν']
        r=audit(a,e,{})
        self.assertEqual(r['formas_repetidas'][0]['estado'],'AMBIGUIDADE_LEGITIMA')
        self.assertEqual(len(r['formas_repetidas'][0]['entradas']),2)

    def test_real_execution_is_reproducible_and_sources_remain_unchanged(self):
        report_root=ROOT/'reports/audit';report_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=report_root,prefix='test-morfologia-') as directory:
            output=Path(directory)
            command=['python3','-B','-m','tools.audit.audit_morphology','--tolerate-trailing-commas','--output',str(output)]
            subprocess.run(command,cwd=ROOT,check=True,capture_output=True)
            first={p.name:p.read_bytes() for p in output.iterdir()}
            report=json.loads(first['auditoria.json'])
            for p,expected in report['fontes_sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),expected)
            subprocess.run(command,cwd=ROOT,check=True,capture_output=True)
            self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()},first)
            for p,expected in report['fontes_sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),expected)

    def test_stale_products_and_shifted_aliases_are_reported_without_writes(self):
        a=lex();before=copy.deepcopy(a)
        alias={'aliases':[{'origem':'ὼν','destino':{'strongs':'1510','flexao':1,'grego':'ὢν'}}]}
        r=check_products(a,{}, {}, alias)
        self.assertEqual(r['formas_derivado_divergentes'],['ὢν'])
        self.assertEqual(r['formas_indice_divergentes'],['ὢν'])
        self.assertEqual(len(r['aliases_com_destino_deslocado']),1)
        self.assertEqual(a,before)


if __name__=='__main__':unittest.main()
