# Tooltips do Novo Testamento

## Fluxo principal

O build cria os tooltips no NT inteiro. Não é necessário aprovar capítulos,
gerar propostas por versículo ou manter outro dicionário completo.

```bash
npm run dev -- --port=8091
# ou
npm run build
```

As fontes são:

1. `src/_data/nt/dict_flex_nt-lxx_greek-pt.json`: correspondências lexicais e
   metadados definitivos. O índice reverso é construído apenas em memória.
2. `src/tooltip-relations.json`: complemento global pequeno, para aliases,
   expressões compostas e ajustes reutilizáveis no NT inteiro.
3. `src/tooltip-exceptions.json`: exceções contextuais opcionais, com âncoras
   persistentes. O arquivo começa vazio; não é uma revisão obrigatória do NT.

O dicionário e as traduções não são modificados durante o build. Os resultados
são reconstruídos dessas fontes e do Texto Majoritário. Nenhuma escolha de
sentido contextual é feita por posição aproximada ou preferência lexical.

## Busca lexical e apresentação

A unidade é **palavra ou expressão**. A busca considera primeiro as expressões
maiores e limita os candidatos às formas presentes no versículo grego.
Uma expressão pode apontar para um token, ou para vários conjuntamente.

Diferentes grupos gregos representam alternativas. Dentro de um grupo, os
termos contribuem conjuntamente. No CSV global:

- `λόγος | ῥῆμα` são formas alternativas para a expressão portuguesa.
- `ἐν + αὐτῷ` é um grupo de duas formas.
- ` || ` separa grupos alternativos.

A mesma forma repetida com a mesma identidade lexical e morfológica é mostrada
uma vez, sem escolher uma posição grega arbitrariamente. Homógrafos com Strong
ou análise morfológica diferentes continuam sendo alternativas reais.

Um candidato único é uma **correspondência lexical automática**, não uma
confirmação contextual. As alternativas aparecem identificadas no tooltip,
conforme a preferência do usuário. Só uma exceção explícita, válida e com uma
única análise é contada como confirmação contextual.

O tooltip mostra forma grega, transliteração, morfologia e verbete com Strong.
Os dados vêm do dicionário, sem cópia nos arquivos de relações. Se uma flexão
não estiver disponível, isso é informado em vez de usar os dados de outra.

O HTML mantém o texto e a formatação. Expressões podem atravessar tags: os
fragmentos compartilham a mesma associação, com controles acessíveis distintos.
Referências em sobrescrito não entram na tokenização; controles interativos e
notas que já têm tooltip não recebem tooltips aninhados.

Mouse, teclado e toque são suportados. O botão × tem alvo de 44 × 44 px.
Escape, toque fora e rolagem da página fecham o painel. O conteúdo lexical é
escapado e excluído do Pagefind. O navegador não baixa o dicionário inteiro.

## Revisão global por CSV

O CSV é uma visão editável da fonte global, com uma linha por termo/expressão.
Não é um segundo dicionário nem exige confirmação de todas as linhas.

```bash
npm run bible:global:export
# Para outra rodada, preservando uma revisão existente:
npm run bible:global:export -- --file reports/revisao-global-2.csv
```

Mantenha o CSV e o `.global.json` de mesmo nome juntos. O segundo arquivo
registra a base da revisão, não deve ser editado e não é um backup.
O exportador não sobrescreve uma revisão diferente já existente.

Colunas editáveis:

- `termo_pt`: palavra ou expressão, preservando os acentos portugueses.
- `formas_gregas`: formas alternativas separadas por ` | `.
- `grupos_gregos`: formas conjuntas separadas por ` + `; grupos alternativos
  separados por ` || `.
- `ativo`: `sim` ou `não`; desativações valem globalmente.
- `observacao`: justificativa global.

`id` e `origem` são referências: não altere nas linhas existentes. Para incluir
um termo novo, adicione uma linha com ambos vazios. Para desativar uma relação,
use `ativo = não`: filtrar ou omitir uma linha não a exclui silenciosamente.

Salve como CSV UTF-8. Primeiro confira, depois aplique:

```bash
npm run bible:global:import -- --file reports/bible-global.csv
npm run bible:global:import -- --file reports/bible-global.csv --apply
npm run build
```

A importação escreve apenas no complemento global, preservando a formatação
não afetada. Não acrescenta sinônimos ao dicionário nem altera o interlinear.
Formas desconhecidas do dicionário e do TM são rejeitadas. Mudança na fonte ou
no dicionário exige nova exportação antes de importar. Após aplicar uma rodada,
exporte outra para alterações posteriores.

Sinônimo lexical de uso geral pode ser incluído manualmente no dicionário pelo
fluxo linguístico do projeto. Alias específico da tradução pode ficar no
complemento global; decisão exclusiva de uma ocorrência fica nas exceções.
Não altere automaticamente `pt` para satisfazer uma correspondência, pois esse
campo também participa do interlinear.

## Exceções opcionais com âncoras persistentes

O JSON usa `version: 1` e um objeto `verses`, cuja chave é a referência canônica,
por exemplo `jo 1:1`. Cada registro guarda:

- `portuguese`: texto português completo usado como âncora, sem tags e sem as
  notas em sobrescrito. É uma fonte persistente, não um relatório regenerável.
- `greek`: todas as formas do versículo, na ordem exata do TM.
- `associations`: somente os trechos que precisam de decisão contextual.

Cada associação usa `position` (token português começando em 1), `text` e
`groups`. Um grupo possui `tokens` (posições gregas começando em 1) e pode
informar `dictionaryKeys` para escolher uma análise homógrafa explicitamente.
Os índices de caracteres usados nos relatórios são UTF-16 e começam em zero.

A tokenização reconhece sequências de letras/números com seus diacríticos.
Pontuação não conta como palavra. Apóstrofos e hífens separam componentes:
`deu-lhes` tem dois tokens portugueses; pode continuar sendo uma expressão
única. Tags não contam. O texto de uma expressão cobre todos os seus componentes.

Exemplo estrutural de uma associação (não há motivo para cadastrar esse caso
se a busca lexical já o resolver):

```json
{
  "position": 5,
  "text": "Palavra",
  "groups": [{ "tokens": [5], "dictionaryKeys": ["λόγος"] }]
}
```

Uma associação com `suppress: true`, sem grupos, registra um trecho que não deve
receber tooltip. `ignoreGreek` no registro do versículo pode excluir tokens
conhecidos como representados por pontuação. Essas decisões não são inferidas
apenas pela ausência de candidato.

A posição é validada contra a âncora guardada. Se as palavras portuguesas ou a
sequência grega mudarem, a exceção é suspensa e relatada; não basta a posição
ainda existir ou conter a mesma palavra. Alterações apenas de caixa, espaços
ou pontuação podem ser revalidadas em memória. A fonte não é regravada.

Uma exceção suspensa não bloqueia a página: a busca global continua disponível,
sem apresentar a decisão antiga como confirmada. Não crie exceções para casos
que já sejam resolvidos pelo dicionário ou por um ajuste global reutilizável.

## Auditorias geradas no build

- `reports/bible-lexical-coverage.json`: palavras sem correspondência efetiva,
  agrupadas por termo/classificação, com referências e contextos individuais.
- `reports/bible-lexical-ambiguities.json`: grupos candidatos, lemas quando
  disponíveis, Strong, morfologia e estado da associação.
- `reports/bible-tooltip-summary.json`: estatísticas, definições das contagens,
  uso por termo e problemas de fontes/exceções.

As pendências de cobertura não são erros confirmados de tradução nem sinônimos
que devam ser acrescentados automaticamente. Podem envolver auxiliares,
contrações, expressões compostas, suprimentos ou dados insuficientes.
Somente colchetes explícitos e decisões manuais são classificados como
suprimentos/ausência confirmada de vínculo. Grego sem correspondente português
não gera automaticamente uma correção.

O percentual de cobertura é a razão entre tokens portugueses com tooltip e
tokens analisados. Não mede acerto contextual. `unambiguousLexicalTokens` não
é equivalente a `contextConfirmedTokens`; as definições ficam no resumo.
Os relatórios não são fontes de aprovação e não precisam ser editados.

## Páginas em TXT e limitações das fontes

Os capítulos disponíveis apenas em TXT são renderizados no build reutilizando
o conversor existente, sem regravar fontes Liquid ou TXT. É necessário Python 3
sem pacotes adicionais; `BEREIA_PYTHON` pode apontar outro executável.

`reports/bible-generated-pages.json` registra problemas de marcação. O fechamento
`/rl>` de Mateus 16:18 é tratado como `</rl>` apenas no HTML, com aviso, sem
alterar o TXT. Outros problemas não resolvidos são exibidos literalmente e
sinalizados. Referências sem texto grego ou com ids duplicados não são alinhadas
por adivinhação; permanecem no relatório.

## Testes e manutenção

```bash
npm run test:bible
```

A suíte cobre busca global, CSV, preservação de UTF-8 e JSON, grupos conjuntos,
homógrafos, formas repetidas, expressões através de HTML e exceções com âncoras.
O piloto Eleventy em Mateus 8 confere os 34 versículos, o texto visível e as
marcações, além das três auditorias.

Foram retirados os fluxos antigos de revisão por capítulo, os índices reversos
persistidos, o mapa completo de João 1 que não era usado no build padrão e seus
relatórios de propostas. As expressões reutilizáveis continuam no complemento
global; o histórico anterior permanece no Git. Backups, baselines e relatórios
históricos do dicionário não fazem parte dessa limpeza. Não há commit automático.
