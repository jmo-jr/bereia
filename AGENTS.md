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

## Fluxo de trabalho — revisão do dicionário

1. Leia apenas o intervalo de entradas solicitado.
2. Apresente sugestões em lista antes de editar.
3. Aguarde aprovação explícita.
4. Aplique somente as alterações aprovadas.
5. Gere relatório CSV das sugestões e decisões.

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