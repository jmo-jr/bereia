# Comparação de formas do TM e do léxico

Execute `npm run dict:compare-tm`. O relatório completo fica em
`reports/dictionary/tm-lexico.json`. Para outra saída, use
`npm run dict:compare-tm -- --output reports/dictionary/tm-lexico-2.json`.
O script recusa sobrescrever arquivos existentes; para atualizar, remova
explicitamente o relatório anterior antes de executar novamente.

- `formas_tm_ausentes`: formas literais de `tokens[].lemma` não encontradas
  em `flexoes[].grego`, com todas as ocorrências (arquivo, capítulo,
  versículo e posição do token).
- `candidatos`: formas do léxico com as mesmas letras após remover marcas
  Unicode e ignorar maiúsculas. A diferença é classificada como diacríticos,
  representação Unicode canonicamente equivalente ou maiúsculas e/ou
  diacríticos. Todas as entradas homógrafas são preservadas, com Strong e
  índice da flexão (a partir de zero).
- `presente_exatamente_no_tm`: informa se o próprio candidato também ocorre
  literalmente no TM; isso impede confundir uma variante textual existente
  com uma forma que precisaria ser substituída.
- `formas_lexico_sem_ocorrencia_exata_tm`: inventário inverso, para avaliar
  quais formas não pertencem ao conjunto exato do TM.

A igualdade exata não aplica normalização Unicode, conversão de caixa,
remoção de pontuação nem espaços. Candidatos não são confirmação de
identidade lexical: remover diacríticos também remove o iota subscrito e
pode reunir palavras diferentes. Alterações de letras (inclusive sigma
final) não entram como diferenças de diacríticos.

Somente JSONs da pasta do TM são lidos, em ordem de nome. Os dados são
validados e entradas inválidas interrompem a execução. O script escreve
apenas o relatório, sem modificar o TM, o léxico ou o estado de revisão.
O léxico contém também material da LXX: ausência no TM, isoladamente,
não autoriza excluir uma flexão nem um verbete inteiro.

Verificação específica: `node --test tests/dictionary/compare-tm.test.js`.
