#!/usr/bin/env python3
"""Auditoria estrutural/morfológica, somente leitura nos dados originais.

python3 -B -m tools.audit.audit_morphology
--tolerate-trailing-commas permite análise provisória, com remoções somente em
memória e registro das posições; nunca regrava ou normaliza o léxico.
"""
import argparse
import csv
import hashlib
import io
import itertools
import json
import re
import unicodedata as ud
from collections import Counter, defaultdict
from pathlib import Path

from tools.audit.audit_tm import ROOT, BOOKS, inventory, parsing, align, nfc, digest
from tools.audit.audit_accents import morphology as simple_morphology

VERSION = 1
LEXICON = 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json'
FIELDS = ('classe', 'tempo', 'modo', 'voz', 'caso', 'genero', 'numero', 'pessoa')
CLASSES = {'S': 'S', 'Adj': 'Adj', 'Adv': 'Adv', 'V': 'V', 'Art': 'Art',
           'RelPro': 'RelPro', 'DPro': 'DPro', 'PPro': 'PPro', 'Ppro': 'PPro',
           'IPro': 'IPro', 'RefPro': 'RefPro', 'PRec': 'PRec', 'Prep': 'Prep',
           'Conj': 'Conj', 'Prtcl': 'Prtcl', 'Prtcl ': 'Prtcl', 'Inj': 'Inj',
           'INJ': 'Inj', 'COND': 'Cond', 'PRT': 'Prtcl', 'R': 'RelPro'}
SOURCE_CLASSES = {'N': 'S', 'A': 'Adj', 'V': 'V', 'ADV': 'Adv', 'T': 'Art',
                  'R': 'RelPro', 'D': 'DPro', 'P': 'PPro', 'I': 'IPro',
                  'F': 'RefPro', 'S': 'PRec', 'PREP': 'Prep', 'CONJ': 'Conj',
                  'PRT': 'Prtcl', 'INJ': 'Inj', 'COND': 'Cond', 'Q': 'IPro',
                  'K': 'RelPro', 'X': 'IPro'}
TERMS = {
 'caso': {'nominativo':'N', 'genitivo':'G', 'dativo':'D', 'acusativo':'A', 'vocativo':'V'},
 'genero': {'masculino':'M', 'feminino':'F', 'neutro':'N', 'comum':'C'},
 'numero': {'singular':'S', 'plural':'P'},
 'tempo': {'presente':'P', 'imperfeito':'I', 'futuro':'F', 'aoristo':'A', 'perfeito':'R',
           'mais-que-perfeito':'L', 'mais que perfeito':'L', 'pluperfeito':'L'},
 'modo': {'indicativo':'I', 'subjuntivo':'S', 'optativo':'O', 'imperativo':'M',
          'infinitivo':'N', 'particípio':'P'},
 'voz': {'ativa':'A','ativo':'A','média':'M','médio':'M','passiva':'P','passivo':'P'},
}


def load_lexicon(text, tolerate=False):
    """Somente vírgulas terminais fora de strings; nenhuma outra reparação."""
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError(f'Chave JSON duplicada: {key}')
            result[key]=value
        return result
    try:
        return json.loads(text,object_pairs_hook=unique), []
    except json.JSONDecodeError:
        if not tolerate:
            raise
    quoted = escaped = False
    positions = []
    for i, char in enumerate(text):
        if quoted:
            if escaped: escaped = False
            elif char == '\\': escaped = True
            elif char == '"': quoted = False
        elif char == '"': quoted = True
        elif char == ',':
            j = i + 1
            while j < len(text) and text[j].isspace(): j += 1
            if text[j:j+1] in {'}', ']'}: positions.append(i)
    repaired = text
    for i in reversed(positions): repaired = repaired[:i] + repaired[i+1:]
    result = json.loads(repaired,object_pairs_hook=unique)  # Outros problemas continuam fatais.
    return result, [{'offset_caracter': i, 'linha': text.count('\n', 0, i) + 1,
                     'coluna': i - text.rfind('\n', 0, i), 'tipo': 'virgula_terminal',
                     'tratamento': 'desconsiderada_em_memoria_sem_regravar'} for i in positions]


def nominal_ending(ending, source=False):
    order = ('caso','numero','genero') if source else ('caso','genero','numero')
    slots = re.fullmatch(r'([NGDAV](?:/[NGDAV])*)([SP](?:/[SP])*)([MFNC](?:/[MFNC])*)' if source
                         else r'([NGDAV](?:/[NGDAV])*)([MFNC](?:/[MFNC])*)([SP](?:/[SP])*)', ending)
    if not slots: return None
    return [dict(zip(order, values)) for values in itertools.product(*(s.split('/') for s in slots.groups()))]


def parse_code(code, source=False):
    """Adaptador conservador de convenções; None significa não comparável.

    Não infere voz, pessoa, gênero ou análise a partir da tradução portuguesa.
    Alternativas compactadas reconhecidas são expandidas, não escolhidas.
    """
    if not isinstance(code, str): return None
    simple = simple_morphology(code, source)
    if simple: return [simple]
    if source:
        # O/D/N denotam convenções de deponência, não são convertidas em voz ativa.
        m = re.fullmatch(r'(N|A|T|R|D|I|F|S|X|P)-([NGDAV])([SP])([MFN])(?:-[CS])?', code)
        if m:
            kind, case, number, gender = m.groups()
            return [{'classe': SOURCE_CLASSES[kind], 'caso':case, 'numero':number, 'genero':gender}]
        m = re.fullmatch(r'P-([123])([NGDAV])([SP])([MFN])?', code)
        if m:
            person, case, number, gender = m.groups()
            return [{'classe':'PPro','pessoa':person,'caso':case,'numero':number,
                     **({'genero':gender} if gender else {})}]
        kind = code.split('-')[0]
        return [{'classe':SOURCE_CLASSES[kind]}] if kind in SOURCE_CLASSES and '-' not in code else None
    head, _, rest = code.partition('-')
    kind = CLASSES.get(head)
    if not kind: return None
    if not rest: return [{'classe':kind}]
    if kind == 'V':
        parts = re.split(r'/(?=(?:V-)?[PIFARL][ISOMNP][AMPE])', rest)
        if len(parts)>1:
            rows=[]
            shared_ending=parts[-1].partition('-')[2]
            final_stem=parts[-1].removeprefix('V-').partition('-')[0]
            for part in parts:
                part=part.removeprefix('V-')
                if re.fullmatch(r'[PIFARL][ISOMNP]',part) and re.fullmatch(r'[PIFARL][ISOMNP][AMPE]',final_stem):
                    part+=final_stem[-1]  # Voz compartilhada em FI/ASA.
                if '-' not in part and shared_ending:part+='-'+shared_ending
                parsed=parse_code('V-'+part)
                if not parsed:return None
                rows.extend(parsed)
            return rows
        m = re.fullmatch(r'([PIFARL])([ISOMNP](?:/[ISOMNP])*)([AMPE](?:/[AMPE])*)(?:-(.+))?', rest)
        if m:
            tense, moods, voices, ending = m.groups()
            rows = []
            for mood, voice in itertools.product(moods.split('/'), voices.split('/')):
                base = {'classe':'V','tempo':tense,'modo':mood,'voz':voice}
                if mood == 'N' and ending is None: rows.append(base)
                elif mood == 'P' and ending:
                    ends = nominal_ending(ending)
                    if not ends: return None
                    rows.extend({**base, **end} for end in ends)
                elif mood not in {'N','P'} and ending and re.fullmatch(r'[123][SP](?:/[123][SP])*', ending):
                    rows.extend({**base,'pessoa':end[0],'numero':end[1]} for end in ending.split('/'))
                else: return None
            return rows
        # Voz ausente: representação parcial explícita, nunca completada aqui.
        m = re.fullmatch(r'([PIFARL])([ISOMNP])(?:-(.+))?', rest)
        if m:
            tense, mood, ending = m.groups()
            base = {'classe':'V','tempo':tense,'modo':mood}
            if mood == 'N' and ending is None: return [base]
            if mood == 'P' and ending:
                ends = nominal_ending(ending)
                if ends: return [{**base,**end} for end in ends]
            if ending and re.fullmatch('[123][SP]',ending):
                return [{**base,'pessoa':ending[0],'numero':ending[1]}]
        return None
    # Graus de adjetivos/advérbios não mudam os traços de caso/pessoa comparados.
    if kind == 'Adv' and rest in {'C','S'}: return [{'classe':kind}]
    rest = re.sub(r'-(C|S)$', '', rest)
    if kind in {'S','Adj','Art','RelPro','DPro','IPro','RefPro','PPro','PRec'}:
        m = re.fullmatch(r'([NGDAV])([MFNC])([123])([SP])', rest)
        if m:
            case,gender,person,number=m.groups()
            return [{'classe':kind,'caso':case,'genero':gender,'pessoa':person,'numero':number}]
        ends=nominal_ending(rest)
        if ends: return [{'classe':kind,**end} for end in ends]
        if '/' in rest:
            parts=rest.split('/')
            if all(nominal_ending(p) for p in parts):
                return [{'classe':kind,**end} for p in parts for end in nominal_ending(p)]
    return None


def compatible(a, b):
    """Compatibilidade de traços explicitados; não prova identidade de forma."""
    shared = set(a) & set(b)
    for key in shared:
        x,y=a[key],b[key]
        if x==y: continue
        if key=='genero' and 'C' in {x,y}: continue
        if key=='voz' and (x=='E' and y in {'M','P'} or y=='E' and x in {'M','P'}): continue
        if key=='caso' and {x,y}=={'N','A'} and a.get('genero')==b.get('genero')=='N': continue
        return False
    return True


def source_analysis(code, strong=None):
    """D Robinson significa média deponente; adaptação restrita e documentada.

    Só os futuros copulares de G1510/G3918 foram revisados nesta rodada.
    A etiqueta original D permanece nas evidências; outras famílias e O/N
    continuam não comparáveis, sem inferência por tradução.
    """
    if strong in {'1510','3918'} and isinstance(code,str) and re.fullmatch(r'V-FD[INP](?:-[123][SP]|-[NGDAV][SP][MFN])?',code):
        return parse_code(code.replace('V-FD','V-FM',1),True)
    return parse_code(code,True)


def compare(local, external, strong=None):
    a,b=parse_code(local),source_analysis(external,strong)
    if a is None or b is None: return 'nao_comparavel'
    if not any(compatible(x,y) for x in a for y in b): return 'divergente'
    # Classe isolada e código sem voz não são validação da análise inteira.
    required=({'classe','tempo','modo','voz'} if a[0]['classe']=='V' else
              {'classe','caso','genero','numero'} if a[0]['classe'] in {'S','Adj','Art','RelPro','DPro','IPro','PPro','RefPro','PRec'} else {'classe'})
    if not all(required <= set(x) for x in a): return 'compativel_parcial'
    return 'compativel'


def description_differences(code, text):
    rows=parse_code(code)
    if rows is None: return None
    text=(text or '').lower()
    found={}
    for key,terms in TERMS.items():
        words=sorted(terms,key=len,reverse=True)
        pattern=r'(?<!\w)(?:'+'|'.join(re.escape(w) for w in words)+r')(?!\w)'
        found[key]={terms[w] for w in re.findall(pattern,text)}
    persons=set(re.findall(r'([123])(?:ª|º)?\s*(?:/\s*[123](?:ª|º)?\s*)?pessoa',text))
    persons.update(re.findall(r'([123])(?:ª|º)\s+(?:singular|plural)',text))
    # Descrições compactas como "1ª/3ª Pessoa" e "1ª Pessoa/3ª Pessoa".
    persons.update(re.findall(r'([123])(?:ª|º)\s*(?=/)',text))
    if persons: found['pessoa']=persons
    kinds={r['classe'] for r in rows}
    markers={'S':'substantivo','Adj':'adjetivo','V':'verbo','Adv':'advérbio',
             'Art':'artigo','RelPro':'pronome relativo','DPro':'pronome demonstrativo',
             'PPro':'pronome pessoal','IPro':'pronome indefinido',
             'RefPro':'pronome reflexivo','PRec':'pronome recíproco',
             'Prep':'preposição','Conj':'conjunção','Prtcl':'partícula','Inj':'interjeição'}
    # IPro reúne convenções locais interrogativas e indefinidas; não escolher uma.
    class_diff=[]
    for kind in kinds:
        expected=markers.get(kind)
        allowed=[expected] if expected else []
        if kind=='IPro':allowed=['pronome indefinido','pronome interrogativo']
        if kind=='Inj':allowed+=['inj']
        if kind=='Prtcl':allowed+=['particula']
        if kind=='RelPro' and text.startswith('r -'):allowed+=['r -']
        if allowed and not any(w in text for w in allowed):
            class_diff.append({'traco':'classe','codigo':[kind],'descricao':text})
    diffs=class_diff
    for key in FIELDS[1:]:
        expected={r[key] for r in rows if key in r}
        if not expected: continue
        observed=found.get(key,set())
        if key=='numero' and 'possessivo' in text and 'PPro' in kinds and any('pessoa' in r for r in rows):
            # O sufixo pessoal indica número do possuidor; não confundir com
            # número do objeto possuído, também explicitado na descrição.
            observed=set(re.findall(r'[123](?:ª|º)?\s+pessoa\s+(singular|plural)',text))
            observed={TERMS['numero'][w] for w in observed}
        if key=='genero' and 'C' in expected:
            if observed and observed <= {'M','F','N','C'}: continue
        if key=='voz' and 'E' in expected:expected=(expected-{'E'})|{'M','P'}
        if key=='caso' and expected<={'N','A'} and all(r.get('genero')=='N' for r in rows) and observed<={'N','A'} and observed:continue
        if expected != observed:
            diffs.append({'traco':key,'codigo':sorted(expected),'descricao':sorted(observed)})
    return diffs


def tbesg(path):
    result=defaultdict(list)
    for line_number,line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(),1):
        fields=line.split('\t')
        if len(fields)<8 or not re.fullmatch(r'G\d+',fields[0]):continue
        strong=str(int(fields[0][1:]))
        kinds=set()
        for code in re.findall(r'[GNAH]:([A-Z]+)', fields[5]):
            if code in SOURCE_CLASSES:kinds.add(SOURCE_CLASSES[code])
        result[strong].append({'linha':line_number,'lema':fields[3],
                              'classe_fonte':fields[5],'classes':sorted(kinds)})
    return result


def collect_evidence(root):
    occurrences=defaultdict(dict); alignment=Counter(); hashes={}
    for book,external in BOOKS.items():
        tm=root/f'src/interlinear/nt/{book}.json'
        aux=root/f'tools/tmnt/with-parsing/{external}.csv'
        hashes[str(tm.relative_to(root))]=digest(tm)
        if aux.exists():
            hashes[str(aux.relative_to(root))]=digest(aux); table=parsing(aux)
        else: table={}
        for verse in inventory(json.loads(tm.read_text(encoding='utf-8')),book):
            source=table.get((verse['chapter'],verse['verse']))
            status=align(verse,source); alignment[status]+=1
            for i,form in enumerate(verse['forms']):
                ref=f"{verse['ref']}#{i+1}"
                item={'referencia':ref,'forma_tm':form,'alinhamento':status}
                if status=='alinhado':
                    _,strong,code=source['tokens'][i]
                    item.update(strong_fonte=strong,morfologia_fonte=code)
                key=nfc(form)
                # Perícopes repetidas não contam como provas independentes.
                previous=occurrences[key].get(ref)
                if previous is None:occurrences[key][ref]=item
                elif previous!=item:
                    occurrences[key][ref]={'referencia':ref,'forma_tm':form,
                                           'alinhamento':'copias_divergentes_sem_atribuicao'}
    return {k:sorted(v.values(),key=lambda x:x['referencia']) for k,v in occurrences.items()}, dict(sorted(alignment.items())), hashes


def summarize_evidence(entries,strong,code):
    groups=defaultdict(list)
    for e in entries:
        if e.get('alinhamento')!='alinhado' or 'strong_fonte' not in e:
            k=(None,None,'sem_parsing_alinhado')
        else:
            status='strong_divergente' if e['strong_fonte']!=strong else compare(code,e['morfologia_fonte'],strong)
            k=(e['strong_fonte'],e['morfologia_fonte'],status)
        groups[k].append(e['referencia'])
    return [{'strong_fonte':s,'morfologia_fonte':c,'comparacao':status,'referencias':refs}
            for (s,c,status),refs in sorted(groups.items(),key=lambda kv:tuple(x or '' for x in kv[0]))]


def source_candidate(evidence, strong=None):
    """Hipótese explícita de correção, não comprovação de exclusividade."""
    observed=[]
    for e in evidence:
        if e['comparacao'] in {'strong_divergente','sem_parsing_alinhado'}:continue
        parsed=source_analysis(e['morfologia_fonte'],strong)
        if not parsed or len(parsed)!=1:return None
        if parsed[0] not in observed:observed.append(parsed[0])
    if len(observed)!=1 or any(e['comparacao']=='strong_divergente' for e in evidence):return None
    f=observed[0];kind=f['classe'];code=None
    if kind=='V' and {'tempo','modo','voz'}<=f.keys():
        code='V-'+f['tempo']+f['modo']+f['voz']
        if f['modo']=='P' and {'caso','genero','numero'}<=f.keys():
            code+='-'+f['caso']+f['genero']+f['numero']
        elif f['modo']!='N' and {'pessoa','numero'}<=f.keys():code+='-'+f['pessoa']+f['numero']
        elif f['modo']!='N':return None
    elif kind in {'S','Adj','Art','RelPro','DPro','IPro','RefPro','PRec'} and {'caso','genero','numero'}<=f.keys():
        code=kind+'-'+f['caso']+f['genero']+f['numero']
    if code is None:return None
    return {'estado':'SUGERIR_NAO_APLICADO','codigo_candidato':code,
            'tracos_fonte':f,'acao':'Conferir forma e decidir se o código ou a descrição precisa mudar; ajustar somente os campos comprovadamente incorretos.',
            'limite':'Consenso nas ocorrências alinhadas não exclui outras análises possíveis da forma; lacunas permanecem sem validação.'}


def audit(lexicon, occurrences, lexical):
    issues=[]; records=[]; forms=defaultdict(list); coverage=Counter(); codes=Counter()
    def issue(record,kind,state,reason,**extra):
        issues.append({'id':f"{record['strong']}:{record['flexao']}:{kind}",
                       'estado':state,'tipo':kind,**record,'motivo':reason,**extra})
    for strong,group in lexicon.items():
        expected={c for e in lexical.get(strong,[]) for c in e['classes']}
        for i,flex in enumerate(group['flexoes']):
            form=flex['grego'];code=flex.get('abrev_morf','')
            record={'strong':strong,'flexao':i,'lema':group.get('lema'),
                    'forma':form,'campos_atuais':flex}
            records.append(record);forms[nfc(form)].append(record)
            parsed=parse_code(code);codes[code]+=1
            coverage['codigo_comparavel' if parsed is not None else 'codigo_nao_comparavel']+=1
            if code=='V':coverage['registros_verbais_genericos_sem_analise_flexional']+=1
            evidence=summarize_evidence(occurrences.get(nfc(form),[]),strong,code)
            context={'evidencias':evidence}
            diffs=description_differences(code,flex.get('morfologia',''))
            if diffs:
                issue(record,'codigo_descricao','ERRO_COMPROVADO',
                      'Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise.',
                      divergencias=diffs,proposta=source_candidate(evidence,strong),**context)
            if parsed and parsed[0]['classe']=='V' and any('tempo' in x and 'modo' in x and 'voz' not in x for x in parsed):
                issue(record,'codigo_sem_voz','ERRO_COMPROVADO',
                      'O código verbal reconhecido não explicita voz; não completar por preferência ou apenas pela tradução.',
                      proposta=source_candidate(evidence,strong),**context)
            kind=CLASSES.get(code.split('-')[0])
            if expected and kind and kind not in expected:
                # Substantivação e classificação lexical divergente não comprovam erro.
                issue(record,'classe_flexao_lema','REVISAO_MANUAL',
                      'A classe do código difere das classes lexicais do TBESG; pode haver substantivação, convenção ou agrupamento incorreto.',
                      classes_lexicais=sorted(expected),fonte_lexical=lexical[strong],**context)
            for level,verbete in [('flexao',flex.get('verbete')),('lema',group.get('verbete'))]:
                if not verbete:continue
                m=re.match(r'^G(\d+):',verbete)
                if m and m[1]!=strong:
                    issue(record,'strong_verbete_'+level,'REVISAO_MANUAL',
                          'O Strong inicial do verbete difere do identificador literal do grupo; conferir agrupamento e referências históricas, sem fundir entradas.',
                          strong_verbete=m[1],verbete=verbete,**context)
            suspicious=[{'offset':j,'unicode':f'U+{ord(c):04X}','nome':ud.name(c,'SEM NOME')}
                        for j,c in enumerate(form) if ud.category(c) in {'Cf','Cc'}]
            if suspicious or form!=form.strip():
                candidate=''.join(c for c in form if ud.category(c) not in {'Cf','Cc'}).strip()
                issue(record,'grafia_com_invisiveis_ou_espacos','REVISAO_MANUAL',
                      'Pode ser marcador histórico de diferenciação. Conferir TM e agrupamento; não remover nem associar automaticamente.',
                      caracteres=suspicious,candidato_visual=candidate,
                      candidato_evidencias=summarize_evidence(occurrences.get(nfc(candidate),[]),strong,code),**context)
            divergences=[e for e in evidence if e['comparacao']=='divergente']
            # Regra geral do projeto: não criar pendência apenas por ambiguidade
            # nominal com uma ocorrência. Erros internos independentes continuam.
            count=flex.get('ocorrencias')
            one_occurrence=str(count).strip()=='1'
            nominal_only=bool(parsed) and all(p['classe'] in {'S','Adj','Art','RelPro','DPro','IPro','PPro','RefPro','PRec'} for p in parsed)
            if divergences and one_occurrence and nominal_only and all(
                    (external:=parse_code(e['morfologia_fonte'],True)) and
                    all(x['classe']==parsed[0]['classe'] for x in external)
                    for e in divergences):
                coverage['divergencias_nominais_uma_ocorrencia_ignoradas']+=1
                divergences=[]
            if divergences:
                issue(record,'parsing_auxiliar_divergente','REVISAO_MANUAL',
                      'Parsing auxiliar alinhado diverge em traços reconhecidos; divergência entre fontes não determina qual análise está correta.',**context)
            foreign=[e for e in evidence if e['comparacao']=='strong_divergente']
            if foreign:
                issue(record,'strong_auxiliar_divergente','REVISAO_MANUAL',
                      'Há ocorrência alinhada com outro Strong. Pode ser homografia legítima; não atribuir todas as ocorrências a esta entrada.',**context)
    repeated=[]
    for form,rows in sorted(forms.items()):
        if len(rows)<2:continue
        signatures=[parse_code(r['campos_atuais']['abrev_morf']) for r in rows]
        supports=[]
        for r in rows:
            ev=summarize_evidence(occurrences.get(form,[]),r['strong'],r['campos_atuais']['abrev_morf'])
            supports.append([e for e in ev if e['comparacao']=='compativel'])
        same_analysis=(len({r['strong'] for r in rows})==1 and all(signatures)
                       and all(s==signatures[0] for s in signatures))
        exact_duplicate=len({json.dumps(r['campos_atuais'],ensure_ascii=False,sort_keys=True) for r in rows})<len(rows)
        if exact_duplicate:
            kind,state='duplicata_integral','ERRO_COMPROVADO'
        elif same_analysis:
            kind,state='mesma_analise_metadados_distintos','REVISAO_MANUAL'
        elif all(supports) and all(signatures):
            kind,state='analises_distintas_atestadas','AMBIGUIDADE_LEGITIMA'
        else:kind,state='multiplicidade_a_validar','REVISAO_MANUAL'
        repeated.append({'forma':form,'tipo':kind,'estado':state,'entradas':rows,
                         'evidencias_por_entrada':supports,
                         'observacao':'Preservar todos os índices. Apoio contextual não certifica exclusividade nem autoriza fusão.'})
    # Classes suspeitas e duplicatas são inventariadas sem decidir por perda de marcas.
    return {'resumo':{'grupos_strong':len(lexicon),'flexoes':len(records),
                       'formas_nfc':len(forms),'cobertura_codigos':dict(coverage),
                       'achados':len(issues),
                       'flexoes_com_achados':len({(r['strong'],r['flexao']) for r in issues}),
                       'achados_por_tipo':dict(sorted(Counter(r['tipo'] for r in issues).items())),
                       'achados_por_estado':dict(sorted(Counter(r['estado'] for r in issues).items())),
                       'formas_repetidas':len(repeated),
                       'repeticoes_por_tipo':dict(sorted(Counter(r['tipo'] for r in repeated).items()))},
            'codigos_nao_comparaveis':[{'codigo':c,'registros':n,
                'entradas':[{'strong':r['strong'],'flexao':r['flexao'],'forma':r['forma'],
                             'morfologia':r['campos_atuais'].get('morfologia')}
                            for r in records if r['campos_atuais'].get('abrev_morf')==c]}
                for c,n in sorted(codes.items()) if parse_code(c) is None],
            'achados':issues,'formas_repetidas':repeated}


def check_products(lexicon, flat, index, aliases):
    expected_flat={};expected_index=defaultdict(list)
    for strong,group in lexicon.items():
        for i,flex in enumerate(group['flexoes']):
            form=flex['grego']
            expected_index[form].append({'strongs':strong,'flexao':i})
            expected_flat.setdefault(form,{'strongs':strong,**flex,
                'verbete':flex.get('verbete',group.get('verbete'))})
    flat_diffs=sorted(k for k in set(flat)|set(expected_flat) if flat.get(k)!=expected_flat.get(k))
    index_diffs=sorted(k for k in set(index)|set(expected_index) if index.get(k)!=expected_index.get(k))
    stale=[]
    for alias in aliases.get('aliases',[]):
        target=alias['destino'];s=target['strongs'];i=target['flexao']
        actual=lexicon.get(s,{}).get('flexoes',[])
        if i>=len(actual) or actual[i]['grego']!=target['grego']:
            stale.append({'origem':alias['origem'],'destino_registrado':target,
                          'forma_atual_no_indice':actual[i]['grego'] if i<len(actual) else None})
    return {'derivado_coerente':not flat_diffs,'formas_derivado_divergentes':flat_diffs,
            'indice_coerente':not index_diffs,'formas_indice_divergentes':index_diffs,
            'aliases_com_destino_deslocado':stale,
            'limite':'Comparação somente; não regenera produtos. A validação completa dos aliases continua no verificador específico.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='reports/audit/morfologia')
    parser.add_argument('--tolerate-trailing-commas',action='store_true')
    args=parser.parse_args()
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to((ROOT/'reports/audit').resolve()):parser.error('Saída deve estar em reports/audit')
    source=ROOT/LEXICON;text=source.read_bytes().decode('utf-8');before=digest(source)
    try:lexicon,syntax=load_lexicon(text,args.tolerate_trailing_commas)
    except json.JSONDecodeError as exc:
        parser.exit(2,f'JSON inválido: linha {exc.lineno}, coluna {exc.colno}: {exc.msg}. Nenhum dado modificado.\n')
    evidence,alignment,hashes=collect_evidence(ROOT)
    lexical_path=next((ROOT/'tools/lxx/fontes').glob('TBESG*'))
    hashes.update({LEXICON:before,str(lexical_path.relative_to(ROOT)):digest(lexical_path)})
    for p in ['tools/audit/audit_morphology.py','tools/audit/audit_tm.py','tools/audit/audit_accents.py']:
        hashes[p]=digest(ROOT/p)
    result=audit(lexicon,evidence,tbesg(lexical_path))
    products={}
    for key,name in [('flat','dict_flex_nt-lxx_greek-pt.json'),('index','dict_form_index_nt-lxx_greek-pt.json'),('aliases','greek_accent_aliases.json')]:
        path=ROOT/'src/_data/nt'/name
        hashes[str(path.relative_to(ROOT))]=digest(path)
        products[key]=json.loads(path.read_text(encoding='utf-8'))
    result['produtos']=check_products(lexicon,**products)
    result.update(schema_version=VERSION,estado='PROVISORIO_JSON_INVALIDO' if syntax else 'AUDITORIA_CONCLUIDA',
                  problemas_sintaxe=syntax,fontes_sha256=dict(sorted(hashes.items())),alinhamento=alignment,
                  criterios={'identidade':'Somente forma literal/NFC; caixa e retirada de marcas não atribuem análise.',
                             'codigo_descricao':'Erro comprovado significa contradição interna, não decisão sobre qual campo alterar.',
                             'classes':'Divergência com TBESG é sinal de revisão, não prova de erro; particípios substantivados continuam verbais.',
                             'limites':'Não há reconstrução independente de todos os paradigmas gregos. Códigos fora do adaptador são não comparáveis. Ausência de parsing alinhado não valida nem refuta uma análise.',
                             'aplicacao':'Somente relatórios; nenhuma alteração em dados, índices, traduções ou mecanismos de homografia.',
                             'sincretismo':'Neutro nominativo/acusativo não gera conflito próprio. Inventário de múltiplas análises não propõe novas ambiguidades.',
                             'voz_copular':'Robinson D é interpretado como média somente nos futuros de G1510/G3918 já revisados; etiqueta original conservada nas evidências. Outras famílias e O/N permanecem não comparáveis.',
                             'registro_generico':'V isolado informa somente a classe verbal; é contado separadamente, sem preencher análise ou gerar omissão de voz.',
                             'reproducibilidade':'Hashes de conteúdo; sem relógio ou cache. Execução completa determinística; fontes verificadas novamente ao final.'})
    if any(digest(ROOT/p)!=h for p,h in hashes.items()):raise RuntimeError('Fonte mudou durante auditoria; repetir.')
    output.mkdir(parents=True,exist_ok=True)
    def write(name,value):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write('auditoria.json',result)
    write('erros-comprovados.json',[r for r in result['achados'] if r['estado']=='ERRO_COMPROVADO'])
    write('formas-repetidas.json',result['formas_repetidas'])
    write('produtos.json',result['produtos'])
    priority_keys={('4687','σπείροντι','codigo_descricao'),
                   ('4687','σπείροντος','codigo_descricao'),
                   ('4931','συνετέλεσεν','codigo_descricao'),
                   ('2608','κατεάξει','codigo_descricao'),
                   ('88','ἀδιάλειπτος','codigo_descricao'),
                   ('1510','ὧν\u200b','grafia_com_invisiveis_ou_espacos')}
    priorities=[r for r in result['achados'] if (r['strong'],r['forma'],r['tipo']) in priority_keys]
    write('prioridades.json',priorities)
    on_forms={'ὢν','ὤν','ὧν'}
    on_rows=[{'strong':s,'flexao':i,'lema':g.get('lema'),'campos_atuais':f}
             for s,g in lexicon.items() for i,f in enumerate(g['flexoes'])
             if ''.join(c for c in nfc(f['grego']) if ud.category(c)!='Cf') in on_forms]
    write('caso-on.json',{'entradas':on_rows,
                         'ocorrencias_tm':{k:evidence.get(k,[]) for k in sorted(on_forms)},
                         'limite':'A remoção do marcador invisível apenas seleciona registros para investigação; não equivale grafias nem atribui análise.'})
    lines=['# Auditoria de agrupamentos e morfologia','',f"Estado: **{result['estado']}**.",'',
           'Dados originais preservados. Os achados contam regras acionadas: uma flexão pode aparecer em mais de uma categoria.','']
    if syntax:lines += ['## Sintaxe do arquivo','',*[f"- Vírgula terminal na linha {r['linha']}, coluna {r['coluna']}; desconsiderada somente em memória." for r in syntax],'',
            'A sintaxe precisa ser corrigida antes de regenerar derivados. As conclusões abaixo são provisórias e vinculadas ao hash exato dos bytes atuais.','']
    lines += ['## Cobertura','',*[f'- {k}: {json.dumps(v,ensure_ascii=False)}.' for k,v in result['resumo'].items()],
              '', '## Produtos derivados','',
              f"- Formas divergentes no dicionário plano: {len(result['produtos']['formas_derivado_divergentes'])}.",
              f"- Formas com índice divergente: {len(result['produtos']['formas_indice_divergentes'])}.",
              f"- Aliases com destino deslocado: {len(result['produtos']['aliases_com_destino_deslocado'])}.",
              '- Detalhes em `produtos.json`. Nenhum produto foi regenerado durante a auditoria.',
              '', '## Casos prioritários','',
              *[f"- **G{r['strong']}/{r['flexao']} — {r['forma']}** ({r['tipo']}): {r['motivo']}" for r in priorities],
              *([] if priorities else ['- Nenhum dos achados prioritários anteriores permanece ativo.']),
              '- Valores e provas completas em `prioridades.json`; os registros atuais relacionados a ὢν/ὧν estão em `caso-on.json`.',
              '', '## Inconsistências internas comprovadas','',
              'O erro comprovado é a contradição ou ausência técnica indicada. Nenhuma análise foi escolhida automaticamente para resolver o conflito.','']
    for r in result['achados']:
        if r['estado']!='ERRO_COMPROVADO':continue
        refs=[ref for e in r['evidencias'] for ref in e['referencias']]
        candidate=(r.get('proposta') or {}).get('codigo_candidato')
        suggestion=f' Código candidato pela fonte alinhada: `{candidate}` (não aplicado; conferir limites no JSON).' if candidate else ' Sem candidato único pela fonte alinhada.'
        lines += [f"- **G{r['strong']} / flexão {r['flexao']} — {r['forma']}** ({r['tipo']}): `{r['campos_atuais']['abrev_morf']}`; {r['campos_atuais']['morfologia']}. {r['motivo']} Traços: {json.dumps(r.get('divergencias',[]),ensure_ascii=False)}. Referências: {', '.join(refs[:8]) or 'sem ocorrência literal/NFC no TM'}.{suggestion} Detalhamento completo no JSON.",'']
    lines += ['## Formas repetidas','']
    for r in result['formas_repetidas']:
        entries='; '.join(f"G{x['strong']}/{x['flexao']}: {x['campos_atuais']['abrev_morf']}" for x in r['entradas'])
        lines += [f"- **{r['forma']}** — {r['estado']}: {r['tipo']}. {entries}.",'']
    lines += ['## Próximos passos','',
              ('- Corrigir a sintaxe em aplicação separada e repetir a auditoria sobre JSON válido.' if syntax else '- JSON válido nesta execução; conferir os produtos derivados e o estado linguístico após qualquer aplicação.'),
              '- Priorizar contradições internas e registros verbais incompletos, validando a forma e o parsing alinhado antes de decidir qual campo corrigir.',
              '- Examinar os marcadores invisíveis sem apagá-los: podem participar da diferenciação histórica de homógrafos.',
              '- Manter divergências entre fontes e classes lexicais em revisão manual; não converter particípios ou infinitivos em substantivos por causa da tradução.',
              '- Não excluir duplicatas nem verbetes flexionais antes de revisar metadados e dependências de índices.',
              '- A lista de códigos não comparáveis é limite explícito da auditoria, não lista de códigos necessariamente errados.','',
              'Fonte lexical: TBESG, Tyndale House/STEPBible, baseado em Abbott-Smith, CC BY 4.0 ([origem](https://STEPBible.github.io/STEPBible-Data)). As classes são usadas apenas para triagem.','']
    (output/'resumo.md').write_text('\n'.join(lines),encoding='utf-8')
    # Somente pendências: não transformar o inventário de ambiguidades em sugestões de alteração.
    buffer=io.StringIO(newline='');writer=csv.writer(buffer)
    writer.writerow(['id','estado','tipo','strong','flexao','grego','abrev_morf','motivo'])
    for r in result['achados']:
        writer.writerow([r['id'],r['estado'],r['tipo'],r['strong'],r['flexao'],r['forma'],r['campos_atuais']['abrev_morf'],r['motivo']])
    (output/'pendencias.csv').write_bytes(buffer.getvalue().encode('utf-8'))
    print(json.dumps(result['resumo'],ensure_ascii=False,indent=2))
    print('Relatórios:',output)


if __name__=='__main__':main()
