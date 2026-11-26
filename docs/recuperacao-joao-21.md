# Recuperação do texto grego de João 21

Em 16/11/2026, preenchido o capítulo 21 de `src/interlinear/nt/JO.json`,
anteriormente com `pericopes: []`: 25 versículos, 552 tokens.
João 7:35 já continha 27 tokens; foi preservado, assim como João 1–20 inteiro.

## Fonte e conferência

- Fonte acentuada local: `tools/tmnt/no-variants/JOH.csv`.
- Origem confirmada pelo responsável: https://github.com/byztxt/byzantine-majority-text/blob/master/csv-unicode/ccat/no-variants/JOH.csv
- O arquivo local é idêntico em bytes ao arquivo remoto consultado nesta data.
- Revisão de `master` informada pelo GitHub na consulta: `cd06053d36d7add3761b0c8ee0bba3a33582666f`.
- SHA-256 da fonte acentuada: `06251d70a77f4d17e8dbde054e82ee947ef7834378348e5bcfa938803b42447b`.
- Conferência com `tools/tmnt/with-parsing/JOH.csv`, SHA-256 `c1c004f56e931630ac98cb973dea8b2da4d5220d707cd66fe980cb8c11e1fa9c`.

O README da origem identifica a edição Robinson–Pierpont 2018 e descreve
os arquivos CCAT como fonte com acentos e espíritos. A identificação
Família 35 do README do BEREIA não foi usada para atribuir essa edição à fonte.

Todas as palavras de 21:1–25 coincidem, na ordem e quantidade, com o CSV
com parsing após normalização para comparação (sem diacríticos, pontuação,
distinção de maiúsculas ou sigma final). Isso verifica a sequência de letras;
os diacríticos foram copiados da fonte CCAT, sem reconstrução pelo dicionário.

## Conversão

`python3 tools/recupera_joao21.py` valida; `--apply` preenche apenas se vazio.
O script também reconhece uma recuperação já aplicada e confere sua igualdade
com a fonte. Conteúdo existente divergente interrompe a execução.

- Removidos sinais de pontuação e o marcador de parágrafo `¶` dos tokens,
  conforme o formato sem pontuação do JSON; preservados apóstrofos de elisão.
- Mantidas as formas flexionadas no campo histórico `lemma`.
- Criado um único agrupamento estrutural `P091`, de 21:1–25, com título vazio.
  Não representa uma decisão sobre divisões editoriais.
- Preservado `Ἀμήν` em 21:25.
- Nenhum outro capítulo, dicionário ou tradução foi alterado por esta recuperação.

A nota anterior em `decisoes-traducao-joao-21.md` descreve as fontes disponíveis
na produção daquela tradução; seu registro histórico não foi reescrito.

Validação: equivalência das 552 palavras com o CSV com parsing, cobertura
exata de 21:1–25, preservação integral de João 1–20, segunda execução
sem alterações e `git diff --check`.
