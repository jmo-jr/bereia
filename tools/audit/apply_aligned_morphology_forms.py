#!/usr/bin/env python3
"""Acrescenta formas do TM com Strong e parsing auxiliar unívocos e conversíveis."""
import argparse, copy, hashlib, json
from collections import defaultdict
from tools.audit.apply_approved_accents import LEXICON, members
from tools.audit.audit_accents import collect_lxx, morphology
from tools.audit.audit_tm import ROOT, digest, nfc, read, write
from tools.update_interlinear_translit import transliterate

TENSE={'P':'Presente','I':'Imperfeito','F':'Futuro','A':'Aoristo','R':'Perfeito','L':'Mais-que-perfeito'}
MOOD={'I':'Indicativo','S':'Subjuntivo','O':'Optativo','M':'Imperativo','N':'Infinitivo','P':'Particípio'}
VOICE={'A':'Ativa','M':'Média','P':'Passiva','E':'Média ou Passiva'}
CASE={'N':'Nominativo','G':'Genitivo','D':'Dativo','A':'Acusativo','V':'Vocativo'}
GENDER={'M':'Masculino','F':'Feminino','N':'Neutro'}; NUMBER={'S':'Singular','P':'Plural'}
CLASS={'S':'Substantivo','Adj':'Adjetivo'}
def sha(x): return hashlib.sha256(x.encode()).hexdigest()
def render(source):
    f=morphology(source,source=True)
    if not f: return None
    if f['classe'] in CLASS:
        code=f"{f['classe']}-{f['caso']}{f['genero']}{f['numero']}"
        desc=f"{CLASS[f['classe']]} - {CASE[f['caso']]} {GENDER[f['genero']]} {NUMBER[f['numero']]}"
    elif f['classe']=='V':
        code=f"V-{f['tempo']}{f['modo']}{f['voz']}" + (f"-{f['caso']}{f['genero']}{f['numero']}" if f['modo']=='P' else (f"-{f['pessoa']}{f['numero']}" if 'pessoa' in f else ''))
        desc=f"Verbo - {TENSE[f['tempo']]} {MOOD[f['modo']]} {VOICE[f['voz']]}" + (f" - {CASE[f['caso']]} {GENDER[f['genero']]} {NUMBER[f['numero']]}" if f['modo']=='P' else (f" - {f['pessoa']}ª Pessoa {NUMBER[f['numero']]}" if 'pessoa' in f else ''))
    else: return None
    return code,desc
def select(report,source):
    known={nfc(f['grego']) for g in source.values() for f in g['flexoes']}; out=[]; pending=[]
    for r in report['propostas']:
        cs=r['candidatos']; ids={(c['strong'],c['forma'],c.get('abrev_morf')) for c in cs}; ev=r['evidencias']['analises_observadas']
        codes={e['parsing'] for e in ev}; strong={e['strong'] for e in ev}
        parsed=render(next(iter(codes))) if len(codes)==1 else None
        if len(ids)!=1 or not ev or strong!={cs[0]['strong']} or not parsed: pending.append(r['forma_tm']); continue
        c=cs[0]; current=source[c['strong']]['flexoes'][c['flexao']]
        if current['grego']!=c['forma'] or nfc(r['forma_tm']) in known: raise ValueError('Fonte ou cobertura desatualizada.')
        known.add(nfc(r['forma_tm'])); out.append({'forma_tm':r['forma_tm'],'strong':c['strong'],'flexao_origem':c['flexao'],'referencias_tm':r['referencias'],'campos_origem':current,'abrev_morf':parsed[0],'morfologia':parsed[1],'parsing_fonte':next(iter(codes))})
    return out,pending
def append(text,rows,lxx):
    before=json.loads(text); grouped=defaultdict(list); apps=[]
    for r in rows:
        d=copy.deepcopy(r['campos_origem']); d.update(grego=r['forma_tm'],transliteracao=transliterate(r['forma_tm']),ocorrencias=str(len(r['referencias_tm'])),lxx=[],ocorrencias_lxx=len(lxx[nfc(r['forma_tm'])]),abrev_morf=r['abrev_morf'],morfologia=r['morfologia'])
        i=len(before[r['strong']]['flexoes'])+len(grouped[r['strong']]); grouped[r['strong']].append(d); apps.append({k:v for k,v in r.items() if k!='campos_origem'}|{'flexao_nova':i,'campos':d})
    roots={k:a for k,a,_ in members(text)}; inserts=[]
    for s,adds in grouped.items():
        fields={k:(a,b) for k,a,b in members(text,roots[s])}; a,b=fields['flexoes']; pos=len(text[:b-1].rstrip())
        if text[a]!='[' or text[pos:b]!='\n    ]': raise ValueError('Formatação inesperada.')
        block=',\n'+',\n'.join('\n'.join('      '+x for x in json.dumps(d,ensure_ascii=False,indent=2).splitlines()) for d in adds); inserts.append((pos,block))
    result=text
    for pos,block in sorted(inserts,reverse=True): result=result[:pos]+block+result[pos:]
    after=json.loads(result)
    for s,g in before.items():
        if after[s]!={**g,'flexoes':g['flexoes']+grouped.get(s,[])}: raise ValueError('Alteração externa ao lote.')
    return result,apps
def main():
    p=argparse.ArgumentParser();p.add_argument('--report',required=True);p.add_argument('--output',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    rp=(ROOT/a.report).resolve(); op=(ROOT/a.output).resolve(); text=(ROOT/LEXICON).read_text()
    report=read(rp)
    if report['fontes_sha256'][LEXICON]!=sha(text): raise ValueError('Triagem desatualizada.')
    rows,pending=select(report,json.loads(text)); lxx,_=collect_lxx([r['forma_tm'] for r in rows]); result,apps=append(text,rows,lxx)
    data={'schema_version':1,'criterio':'Strong auxiliar unânime, parsing único conversível e grafia própria do TM.','relatorio_origem':str(rp.relative_to(ROOT)),'relatorio_sha256':digest(rp),'fonte':LEXICON,'fonte_antes_sha256':sha(text),'fonte_depois_sha256':sha(result),'quantidade':len(apps),'pendentes':pending,'aplicacoes':apps}
    if a.apply: write(ROOT/LEXICON,result)
    write(op,json.dumps(data,ensure_ascii=False,indent=2)+'\n'); print(f"{len(apps)} flexões aplicáveis; {len(pending)} pendências preservadas.")
if __name__=='__main__': main()
