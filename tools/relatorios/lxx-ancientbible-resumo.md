# Concordância AncientBible — cobertura das pendências da LXX

Fonte consultada: `../bibliaaberta/sources/ancientbible-corcordance.json`.
Consulta somente de leitura, sem alteração da fonte, dos livros, do dicionário
ou do suplemento. A lista atual contém 563 lemas e 1.046 ocorrências pendentes.

## Resultado

- 12 lemas com correspondência exata: 37 ocorrências pendentes.
- 3 lemas candidatos após retirar os diacríticos: 15 ocorrências pendentes.
- Total com lema grego identificado: 15 lemas / 52 ocorrências.
- Outros 26 lemas possuem candidatos por transliteração ou identificador TBESG,
  envolvendo 59 ocorrências. São pistas adicionais, não confirmação lexical.
- 522 lemas / 935 ocorrências não tiveram correspondência nem nessas buscas
  auxiliares nos registros aproveitáveis. A ausência não é conclusiva porque
  o arquivo apresenta corrupção sintática e campos ausentes ou misturados.

## Correspondências exatas

- μίτρα: 10 ocorrências. Glosa original: G8333: 'uma mitra'.
- ἄκρα: 9 ocorrências. Glosa original: G6202: 'Akra'.
- ἄπειμι: 4 ocorrências. Glosa original: G0549: 'para go'; G0548: 'afastar-se'.
- ἀποσυνάγω: 4 ocorrências. Glosa original: G6494: 'para cura'.
- καλέω: 2 ocorrências. Glosa original: G2564: 'para chamada: chamada'.
- καταβαρύνω: 2 ocorrências. Glosa original: G6046: 'para fardo'.
- ἀνακράζω: 1 ocorrências. Glosa original: G0349: 'para gritar'.
- ἀξιόπιστος: 1 ocorrências. Glosa original: G6381: 'digno de trust'.
- ἄπληστος: 1 ocorrências. Glosa original: G6414: 'insaciável'.
- διορίζω: 1 ocorrências. Glosa original: G6938: 'para determinar'.
- τρυφή: 1 ocorrências. Glosa original: G5172: 'auto-indulgência'.
- κραταιός: 1 ocorrências. Glosa original: G2900: 'poderoso'.

## Candidatos sem diacríticos

- ἱερόδουλος: 7 ocorrências; forma da fonte: ιεροδουλος.
- μονόκερως: 7 ocorrências; forma da fonte: μόνόκερως.
- μονοκέρως: 1 ocorrências; forma da fonte: μόνόκερως.

A normalização foi utilizada apenas na busca. Nenhuma grafia grega foi
corrigida, nem foram fundidos os lemas μονόκερως e μονοκέρως.

## Limitações da fonte

O JSON completo não pode ser decodificado: o primeiro erro ocorre na linha 1,
coluna 488. Foram detectados 17.009 inícios de registro com identificadores G/H;
15.981 registros puderam ser lidos individualmente e 1.028 não puderam ser
decodificados como registros completos. Há também registros com campos em
número diferente do padrão, cabeçalhos sem grego e mistura de alfabetos.

A auditoria identifica lemas gregos nos campos iniciais legíveis e marca
expressamente eventuais registros parciais. Não repara a fonte nem utiliza
suas contagens. Candidatos por transliteração e identificador ficam separados
das correspondências em grego. Identificadores não são acrescentados à BEREIA.

As glosas não são traduções portuguesas prontas: há textos como “para go”,
“para cura”, “digno de trust” e “a unicórnio”. A entrada ἄκρα, por exemplo,
traz “Akra”, o que exige verificar se cabe nome próprio ou substantivo comum
em cada contexto. A presença do lema não resolve uma análise morfológica
incompleta nem os casos semânticos INCERTO já conhecidos.

Nenhuma tradução foi aplicada. Os dados detalhados, inclusive candidatos,
referências bíblicas, hashes e registros problemáticos, estão em
`lxx-ancientbible-cobertura.json`.

## Reprodução

```sh
python3 -B tools/lxx/audit_ancientbible.py ../bibliaaberta/sources/ancientbible-corcordance.json
```
