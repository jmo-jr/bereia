# Bases portuguesas TBESG — etapa 1

Esta etapa prepara bases lexicais. Não regenera flexões, suplemento ou páginas.

- Livros ativos: 39.
- Ocorrências ainda sem tradução na beta: 11,412.
- Identificadores completos dStrong com candidato único: 3,068.
- Bases lexicais provisórias: 3,055, associadas a 9,521 ocorrências pendentes.
- Identificadores INCERTO: 13, associados a 39 ocorrências.
- Sem candidato pelo lema informado: 1,806 ocorrências.
- Com múltiplos candidatos: 46 ocorrências.

As frequências indicam o alcance potencial das bases, não o número de traduções
já preenchidas nem uma promessa de que todas as flexões serão geradas. O passo 2
precisa verificar os modos, vozes e classes gramaticais antes de aplicar formas.
Os registros mantêm as definições originais, as referências e a procedência.
Os 13 casos incertos têm base_pt nula e não devem ser consumidos automaticamente.

## Exemplos

- G4876 — συναντάω: encontrar-se.
- G5339 — φείδομαι: poupar.
- G6398 — ἀπαντή: encontro.
- G9778 — χωνευτός: fundido.
- G8308 — μετέωρος: elevado, apoiado na definição completa, não na glosa isolada “a meteorite”.
- G4162 — ποίησις: feitura, apoiado na definição nominal, não na glosa “he did”.

A grafia grega acima é uma apresentação dos exemplos; o cadastro conserva
literalmente a grafia original da TBESG em cada verbete. Nenhum JSON grego foi
corrigido. As observações registram traduções alternativas, incerteza contextual
ou insuficiência da fonte; elas não constituem correções automáticas do léxico.

## Arquivos

- tools/lxx/tbesg_base_translations.tsv: propostas editoriais por identificador.
- tools/lxx/tbesg_bases_pt.json: cadastro completo com fontes e referências.
- tools/relatorios/lxx-bases-pt-pendencias.csv: somente os 13 casos pendentes.
- tools/lxx/prepare_tbesg_bases.py: geração reproduzível e validação de hashes.

Atribuição dos dados TBESG: Tyndale House e STEPBible.org, CC BY 4.0.
As bases portuguesas são adaptações editoriais provisórias para a BEREIA.
