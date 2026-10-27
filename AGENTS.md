# Instruções do projeto BEREIA

## Finalidade

Este repositório contém recursos do projeto BEREIA, incluindo um dicionário grego (koiné)-português usado para a construção de um Novo Testamento interlinear.

## Regras permanentes

- Preserve os valores originais e não faça alterações silenciosas.
- Preserve a codificação UTF-8, os diacríticos gregos, a ordem das chaves
  e a formatação do JSON.
- Corrija automaticamente erros objetivos comprovados em campos técnicos,
  especialmente `abrev_morf` e `morfologia`, incluindo indicações de voz
  ausentes. Preserve a consistência entre código, descrição e forma grega.
- Não faça mudanças técnicas por preferência, nem renomeie, funda ou exclua
  entradas automaticamente. Preserve campos sem erro comprovado.
- Não reordene chaves nem reformate arquivos inteiros.
- Não sobrescreva arquivos originais sem criar backup.
- Diferencie sempre:
  - erro objetivo;
  - alternativa de tradução aceitável;
  - preferência estilística;
  - caso dependente de contexto;
  - informação insuficiente.
- Não trate uma tradução possível como erro apenas porque difere de outra.
- Não invente contexto bíblico nem atribua sentido contextual sem indicar
  que a conclusão depende da ocorrência.
- Quando houver dúvida, marque o item para revisão manual.

## Revisão do dicionário

A revisão assistida deve concentrar-se nos campos `traducao` e `pt`.

Use `morfologia` como contexto para avaliar:

- concordância nominal e verbal;
- voz verbal, especialmente média/passiva;
- tempo, modo, pessoa, número, gênero e caso;
- ortografia, acentuação, regência e pontuação em português brasileiro;
- naturalidade, sem perder o caráter interlinear e literal.

Não automatize escolhas lexicais ou exegéticas dependentes de contexto.
Esses casos devem ser marcados como `INCERTO` e deixados para decisão humana.

### Tratamento autorizado de ambiguidades

- Formas que admitem primeira pessoa singular e terceira pessoa plural
  (`1S/3P`): registre automaticamente ambas em `pt`, `traducao`,
  `abrev_morf` e `morfologia`, seguindo os padrões do projeto, como
  `ἔφερον` e `ἔφαγον`. Essa regra independe do número de ocorrências.
  Não reproduza eventuais inconsistências de pessoa dos exemplos.
- Mais de um modo possível: com apenas uma ocorrência, ignore a
  ambiguidade, preservando a análise atual; com mais de uma ocorrência,
  combine automaticamente as análises como em `εὐχαριστῶ`, sem escolher
  uma delas nem atribuir uma leitura a uma ocorrência específica.
- Ambiguidades de caso sem diferença relevante em português, como
  nominativo/acusativo com a mesma tradução: ignore.
- Outras ambiguidades nominais de caso, gênero ou número com apenas uma
  ocorrência: ignore. A exceção verbal `1S/3P` continua válida.
- Para esses limites, use o campo `ocorrencias` (NT), sem somar
  `ocorrencias_lxx`. Contagem ausente ou inválida não equivale a uma
  ocorrência: mantenha a questão pendente se depender dessa contagem.
- Ignorar significa não alterar nem listar ou gravar no CSV somente por
  essa ambiguidade; não significa deixar de corrigir um erro objetivo
  independente de tradução ou de campo técnico.

## Fluxo de trabalho — revisão do dicionário

1. Leia apenas o intervalo de entradas solicitado.
2. Apresente sugestões e alterações em lista, nunca em tabela.
3. Aplique automaticamente os itens `CORRIGIR`, os erros técnicos
   comprovados e as combinações de análises autorizadas acima, sem pedir
   nova aprovação. Preserve backup e informe o que foi alterado.
4. Aguarde aprovação para `SUGERIR` e para os demais `INCERTO`.
5. Gere ou atualize o CSV somente com pendências não aplicadas; não
   acrescente casos ignorados. Preserve o histórico sem limpeza retroativa
   não solicitada. Não faça commit.

## Tradução do Novo Testamento

Esta atividade é distinta da revisão do dicionário.

Para tarefas de tradução bíblica:

1. Leia e siga `docs/protocolo-traducao.md`.
2. Consulte `docs/decisoes-traducao.md`.
3. Utilize o Texto Majoritário do projeto BEREIA.
4. Utilize `src/_data/dict_flex_nt-lxx_greek-pt.json`
   como dicionário definitivo.
5. Preserve a consistência lexical e o estilo dos
   capítulos anteriormente aprovados.
6. Produza os capítulos em formato TXT, conforme o protocolo.
7. Não modifique o dicionário nem outros capítulos.
8. Não solicite aprovação a cada versículo.
9. Entregue o capítulo completo para revisão humana.
10. Registre separadamente as decisões lexicais relevantes.

As regras do fluxo de revisão do dicionário não se aplicam
à produção de capítulos bíblicos.
