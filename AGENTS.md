# Instruções do projeto BEREIA

## Finalidade

Este repositório contém recursos do projeto BEREIA, incluindo um dicionário grego (koiné)-português usado para a construção de um Novo Testamento interlinear.

## Regras permanentes

- Preserve os valores originais e não faça alterações silenciosas.
- Preserve a codificação UTF-8, os diacríticos gregos, a ordem das chaves
  e a formatação do JSON.
- Não altere campos técnicos, como `chave_json`, `grego`, `strongs`,
  `transliteracao`, `verbete`, `abrev_morf` e `morfologia`.
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

## Fluxo de trabalho

1. Leia apenas o intervalo de entradas solicitado.
2. Apresente sugestões em lista antes de editar.
3. Aguarde aprovação explícita.
4. Aplique somente as alterações aprovadas.
5. Gere relatório CSV das sugestões e decisões.