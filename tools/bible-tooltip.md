# Tooltips globais do Novo Testamento

## Fluxo principal — uma fonte para o NT inteiro

O build aplica a busca lexical a todos os capítulos do NT, sem exigir revisão
ou aprovação de cada capítulo. Não é necessário executar `bible:propose` nem
preencher os CSVs por versículo para ter os tooltips. Esses recursos antigos
ficam disponíveis apenas para exceções opcionais.

As relações globais são compostas pelo dicionário definitivo e pelas regras de
`src/tooltip-relations.json`. O CSV `reports/bible-global.csv` oferece uma visão
única e completa dessa fonte, com uma linha por termo ou expressão portuguesa.
O arquivo inicial tem 20.438 linhas de termos. Suas alterações em uma linha
valem para todas as ocorrências correspondentes no NT.

### Para apenas usar o site

```bash
npm run dev -- --port=8091
# ou
npm run build
```

O build busca palavras e expressões na fonte global e filtra as formas gregas
pelo Texto Majoritário de cada versículo. Expressões maiores têm preferência
sobre fragmentos menores que se sobreponham. Formas repetidas iguais aparecem
uma vez no tooltip; formas diferentes possíveis aparecem como alternativas,
conforme a preferência do usuário. Isso é uma correspondência lexical, não uma
certificação de que cada alternativa seja a leitura contextual daquela palavra.

O processamento funciona sobre o HTML gerado, preservando as marcações e o
texto visível. Citações e palavras em cores continuam funcionando. Notas e
controles que já têm tooltip não recebem outro tooltip aninhado. A ausência
de uma relação global não bloqueia a página; você pode acrescentar essa relação
uma única vez na fonte global e reutilizá-la em todo o NT.

### Para revisar a fonte global

O CSV inicial já está em `reports/bible-global.csv`. Para exportar outra rodada:

```bash
npm run bible:global:export -- --file reports/revisao-global-2.csv
```

Mantenha o CSV e o `.global.json` de mesmo nome juntos. O segundo arquivo
registra a base da revisão; não deve ser editado. O exportador preserva arquivos
que já tenham conteúdo diferente, para não apagar uma revisão em andamento.

Edite somente as relações que quiser corrigir. Não há uma coluna para aprovar
cada linha e não é necessário confirmar os termos que já vêm do dicionário.

- `termo_pt`: palavra ou expressão portuguesa. A busca não remove acentos.
- `formas_gregas`: formas alternativas, separadas por ` | `.
- `grupos_gregos`: formas que, juntas, traduzem uma expressão, separadas por
  ` + `. Use ` || ` entre grupos alternativos.
- `ativo`: `sim` ou `não`. Desativar uma linha suprime a relação no NT inteiro.
- `observacao`: sua justificativa global, guardada na fonte de regras.
- `origem` e `id`: referências; não altere essas colunas nas linhas existentes.

Exemplo: se você ajustar as formas associadas a “palavra”, a seleção valerá em
todos os capítulos, sempre limitada às formas presentes no respectivo versículo.
Para incluir um termo novo, acrescente uma linha com `id` e `origem` vazios.
Para retirar uma relação, use `ativo = não`; apagar ou filtrar uma linha do CSV
não exclui a relação silenciosamente. Renomear um termo desativa o nome antigo
e cria o novo na fonte global, sem alterar o dicionário ou a tradução.

Salve como CSV UTF-8, preservando os diacríticos. Primeiro confira sem gravar:

```bash
npm run bible:global:import -- --file reports/bible-global.csv
```

Depois aplique suas alterações:

```bash
npm run bible:global:import -- --file reports/bible-global.csv --apply
npm run build
```

Só a aplicação escreve em `src/tooltip-relations.json`. Não escreve no
dicionário, nos capítulos ou em arquivos de alinhamento por capítulo. Uma
mudança de observação não muda o texto bíblico nem os metadados gregos.
Formas gregas desconhecidas do dicionário e do Texto Majoritário são rejeitadas.
Mudança na fonte global ou no dicionário durante a revisão exige nova exportação.
Após importar uma rodada, exporte outra para alterações posteriores.

O build lê as alterações globais automaticamente. O navegador recebe apenas os
dados de seus tooltips, não o índice inteiro. Os metadados são buscados no
dicionário atual; se a flexão não estiver disponível, isso é informado em vez
de exibir a análise de uma flexão diferente.

### Relatórios e páginas em TXT

`reports/bible-global-tooltips.json` resume cobertura, alternativas, uso por
termo e problemas de referências. Ele serve para priorizar revisões globais,
não constitui uma lista de capítulos que precisam ser aprovados.

Os 19 capítulos de Mateus disponíveis apenas em TXT passam a ter páginas
renderizadas durante o build, usando o conversor já existente. Nenhum TXT ou
Liquid de capítulo é regravado. Esse adaptador requer Python 3, sem pacotes
adicionais; `BEREIA_PYTHON` pode indicar outro executável Python.
`reports/bible-generated-pages.json` registra avisos de marcação. O fechamento
malformado `/rl>` em Mateus 16:18 é tratado como `</rl>` no HTML e registrado;
o TXT permanece intacto. Outros erros de marcação são exibidos literalmente e
sinalizados, sem adivinhar uma tradução ou apagar o conteúdo.

### Exceções por ocorrência são opcionais

Por padrão, a fonte global governa todas as páginas, inclusive João 1. Os
alinhamentos anteriores são preservados em disco, mas não são exigidos pelo
fluxo principal. Para ativar exceções locais deliberadamente, use
`useVerseOverrides: true` na fonte JSON ou `BEREIA_VERSE_OVERRIDES=1` no ambiente.
Nessa modalidade, os vínculos locais têm prioridade nos trechos correspondentes.

Os capítulos e comandos documentados abaixo descrevem esse fluxo opcional e
os estágios de desenvolvimento anteriores. Eles **não são pré-requisitos**
para os tooltips globais.

## Fluxo opcional de alinhamento por ocorrência

## Uso cotidiano

- `npm run dev -- --port=8091`: página `/biblia/joao/1/`.
- `npm run build`: renderiza os vínculos seguros e informa pendências.
- `npm run bible:align`: recalcula e gera `reports/bible-alignment.json` sem
  precisar gerar todo o site.
- `npm run bible:align:check`: mesma auditoria, com saída 1 se houver pendências;
  apropriado para um gate opcional de integração. O build normal não trava a
  revisão linguística por pendências.
- `npm run test:bible`: testes de alinhamento, interação e geração pelo Eleventy.

A origem da página é o template `.liquid`. Se a revisão for feita no TXT,
primeiro gere o Liquid pelo fluxo já existente no projeto; o recurso não
sincroniza nem reescreve as duas versões.

## O que acontece quando o texto muda

O build compara as palavras atuais com o texto aprovado. Preserva somente
correspondências que aparecem em **todos** os alinhamentos ótimos que mantêm a
ordem. Não escolhe arbitrariamente uma ocorrência repetida. Alterações de
pontuação, espaços e caixa permitem recalcular posições. Não ignora diferenças
de acentuação lexical.

Uma expressão é preservada somente se todas as suas palavras permanecem
consecutivas. Trocas ou inserções dentro dela suspendem o vínculo inteiro;
outros trechos seguros continuam funcionando. Palavras novas sem vínculo
aparecem normalmente na leitura e são relacionadas no relatório.

Mudanças na sequência grega suspendem os painéis do versículo inteiro. HTML
interno e entidades HTML também são mantidos intactos, com o alinhamento do
versículo pendente. Configuração aprovada inválida (índices fora de limites,
sobreposição, etc.) é um erro técnico e interrompe o build com referência.

O resultado é recalculado do zero em cada build, incluindo em modo incremental,
e não promove automaticamente um alinhamento novo a aprovado. O relatório é
uma fotografia determinística da situação atual; não é histórico linguístico.
Inclui referência, segmentos resolvidos, posições, tokens e razões das pendências.
Templates aprovados removidos ou com formato não reconhecido também são sinalizados.
O relatório fica fora de `src` e da publicação. Para CI/testes, o destino pode
ser escolhido com `BEREIA_BIBLE_ALIGNMENT_REPORT`.

## Equivalências aprovadas

O arquivo `src/alinhamentos/<abreviação>/<capítulo>.json` tem este formato:

```json
{
  "sourceBook": "JO",
  "verses": {
    "3": {
      "text": "Eles vieram a ser livres.",
      "greek": ["FORMA GREGA DO TOKEN 1"],
      "segments": [
        {
          "start": 5,
          "text": "vieram a ser",
          "tokens": [1],
          "alternatives": ["passaram a existir"]
        }
      ]
    }
  }
}
```

Esse exemplo é estrutural e não é uma tradução de João 1:3.
`start` é uma posição UTF-16 de string JavaScript, começando em zero. `tokens`
são posições gregas começando em 1. `greek` preserva todas as formas originais,
na ordem exata do versículo. O texto aprovado continua sendo a âncora.

`alternatives` só deve conter expressões explicitamente aprovadas para **aquele
segmento e ocorrência**. Não é uma tabela global de sinônimos. Cada alternativa
é testada no contexto do texto aprovado, com a mesma exigência de correspondência
inequívoca. Se duas propostas disputarem o mesmo trecho, ambas ficam pendentes.
Não usamos similaridade aproximada ou o dicionário para decidir exegese.

Para aprovar uma revisão mais ampla, confira o relatório e as ocorrências no
Texto Majoritário, atualize `text` e os `segments` da entrada correspondente e
rode `npm run bible:align:check`. Os segmentos resolvidos do relatório ajudam a
reconstruir as posições; complete os pendentes antes de considerá-los aprovados.
Não substitua a entrada inteira por um relatório parcial sem revisão.

Para expandir a cobertura, crie o arquivo de alinhamento do capítulo, usando a
abreviação do shortcode `verse`, e registre os versículos revisados. Versículos
sem entrada aprovada continuam sendo texto comum. As contagens do relatório
se referem somente à cobertura cadastrada, não a todo o NT.

## Dados e apresentação

Primeira linha: forma grega da ocorrência, seguida da transliteração entre
parênteses. Segunda linha: morfologia. Terceira linha: verbete com Strong.
Vários tokens produzem blocos separados. O dicionário é lido apenas no build;
o navegador não baixa o dicionário completo para abrir o painel.

A busca dá prioridade à forma exata, aceitando caixa, equivalência Unicode e
alternância gráfica de acento grave/agudo. O enriquecedor do interlinear só é
usado como fallback lexical. Quando a forma exata não é confirmada, o painel
omite a transliteração e exibe “Morfologia não confirmada para esta forma”.
Isso evita apresentar, por exemplo, a análise nominativa de `ἀρχή` como se
fosse a análise de `ἀρχῇ`. O relatório lista esses casos em `lexicalWarnings`.
O verbete lexical pode continuar vindo do fallback; sua revisão continua
humana. Os avisos lexicais são separados das pendências de alinhamento e não
alteram a saída de `bible:align:check`. Não alteramos o dicionário.

## Interação e acessibilidade

Mouse: abre após breve intervalo e permite chegar até o painel. Teclado: Tab
focaliza o trecho e permite chegar ao botão; Escape fecha. Celular: toque abre,
botão × com alvo de 44 × 44 px ou toque fora fecha. O botão devolve o foco ao
trecho sem reabrir o painel. Rolagem da página e redimensionamento fecham;
rolagem dentro de um painel longo continua disponível.

O painel tem semântica de diálogo não modal porque contém um botão. Os estados
`aria-expanded` e os identificadores são gerados por ocorrência. O conteúdo
lexical é escapado, excluído do Pagefind e independente do jQuery externo.
As quebras de linha são codificadas para não interferirem nos parágrafos do
shortcode `pericope`. Os tooltips existentes permanecem separados.

## Decisões do alinhamento de João 1 para revisão humana

- João 1:1: as três ocorrências de “Palavra” apontam para os tokens 5, 8 e 17;
  “Deus” após “com” agrupa os tokens 11–12.
- João 1:2: “Deus” agrupa os tokens 6–7.
- João 1:3: “Todas as coisas” aponta para Πάντα; “vieram a ser” e as duas
  ocorrências de “veio a ser” têm vínculos próprios. “do que” aponta para ὃ.
- João 1:4: “Nela” agrupa Ἐν e αὐτῷ. O primeiro artigo português de “a vida”
  fica sem vínculo direto: não há artigo correspondente antes de ζωὴ.
  “das pessoas” agrupa τῶν e ἀνθρώπων.
- João 1:5: “na” agrupa ἐν e τῇ; “não a” preserva separadamente οὐ e αὐτὸ.

A expansão do capítulo registra 758 segmentos. Cada token grego está ligado
uma vez a um trecho português ou identificado em `untranslatedTokens`. Cada
palavra portuguesa tem vínculo ou justificativa em `unlinkedPortuguese`.
Esses campos documentam escolhas linguísticas; não geram novos tooltips.

- João 1:6, 8, 18, 23, 30 e 39: ficam sem vínculo independente, respectivamente,
  a cópula “era”, “[veio]”, o objeto “o”, a cópula “sou”, “aquele” e o sujeito
  “Ele”. São suprimentos da tradução, não tokens gregos ausentes no cadastro.
- João 1:20 e 32: ὅτι introduz discurso direto e é representado pela pontuação;
  não se atribui seu painel a uma palavra portuguesa diferente.
- João 1:25: o único “lhe” português reúne αὐτόν e αὐτῷ, presentes no grego nas
  construções de perguntar e dizer.
- João 1:27: “de quem” reúne o relativo οὗ e a retomada possessiva αὐτοῦ.
- João 1:31, 33 e 34: “E eu” corresponde à crase Κἀγὼ.
- João 1:33: “você vir” agrupa a partícula modal ἂν e o verbo ἴδῃς.
- João 1:38: “que o seguiam” preserva a reformulação portuguesa de αὐτοὺς
  ἀκολουθοῦντας. Não se inventa um token grego independente para cada palavra.
- João 1:40: “que ouviram João” reúne artigo, particípio e παρὰ Ἰωάννου.
- João 1:43: “Siga-me” mantém unidos Ἀκολούθει e μοι.
- João 1:45: “aquele a respeito de quem” é a expansão do relativo Ὃν; não há
  περί independente nessa ocorrência.
- João 1:51: o alinhamento aceita “digo a vocês” e “lhes digo”, esta última já
  presente no texto revisado da develop. Ambos apontam para λέγω e ὑμῖν.

Os campos `notes` de cada versículo explicam esses agrupamentos. Os testes
conferem a cobertura dos 51 versículos contra o Texto Majoritário, preservação
do português e ausência de vínculos duplicados ou palavras sem justificativa.

## Índice reverso português → grego — passo 1

```bash
npm run bible:index
npm run bible:index:check
npm run bible:lookup -- palavra
npm run bible:lookup -- palavra --book jo --chapter 1 --verse 1
npm run bible:lookup -- "por meio de"
npm run test:bible:index
```

`bible:index` gera `reports/bible-reverse-index.json` a partir dos campos `pt`
e `traducao` do dicionário definitivo. O arquivo contém termos portugueses,
referências à chave grega e ao campo de origem, estatísticas e pendências de
indexação. Não copia os metadados morfológicos e lexicais: a consulta os lê da
entrada original referenciada, preservando seus valores.

Alternativas simples separadas por vírgula, ponto e vírgula ou barra entram
separadamente no índice. Expressões de várias palavras permanecem inteiras.
A busca uniformiza caixa, Unicode NFC e espaços, sem remover acentos
portugueses, lematizar ou escolher sinônimos. Notações como `eu/ele(a) era`,
complementos entre parênteses e trechos não reconhecidos ficam em `pending`,
com o valor original e a justificativa. Uma pendência significa limitação da
indexação, não um erro de tradução ou uma correção a aplicar no dicionário.

O índice inicial desta branch tem 20.342 termos/expressões, 43.365 referências
a campos e 4.774 pendências. Esses números mudam conforme o dicionário evolui.
O arquivo é regenerável e fica fora da publicação. Seu versionamento depende
do `.gitignore`; não deve ser usado como lugar definitivo para decisões de alinhamento.

Sem referência bíblica, `bible:lookup` lista as entradas gregas que contêm o
termo consultado. Com `--book`, `--chapter` e `--verse`, filtra essas entradas
pelas formas presentes no Texto Majoritário daquele versículo. Preserva todas
as ocorrências repetidas, sem atribuir uma delas a uma palavra portuguesa.
Por exemplo, “palavra” em João 1:1 retorna λόγος nas posições 5, 8 e 17.
A comparação grega aceita caixa, NFC e alternância grave/agudo, mas não ignora
outros diacríticos nem confunde flexões como ἀρχή e ἀρχῇ. A ausência de uma
forma exata pode resultar em nenhum candidato; isso não autoriza corrigi-la.

O SHA-256 do dicionário de origem fica registrado no índice. Se o dicionário
mudar, a consulta exige executar `npm run bible:index` novamente.
`bible:index:check` verifica sem escrever e retorna saída 1 quando o índice
está ausente ou desatualizado. A geração não modifica fontes, capítulos,
dicionário ou relações aprovadas e não cria backups.

O índice persistente é usado pelo gerador de relações do passo 2, descrito
abaixo. Ele não é lido pelo navegador. Não é necessário gerá-lo em cada build:
regenere após mudanças no dicionário. O gerador exige um índice atual e não o
reconstrói silenciosamente.

## Relações por ocorrência — passo 2

O comando do gerador agora consulta o índice reverso persistido: primeiro
localiza palavras e expressões portuguesas e depois filtra suas entradas pelos
tokens gregos daquele versículo. Não usa fallback sem diacríticos nesse
caminho. Expressões de vários tokens previamente cadastradas continuam sendo
fontes de sugestões quando os tokens gregos são contíguos.

```bash
npm run bible:index
npm run bible:propose

# Um livro ou capítulo
npm run bible:propose -- --book jo
npm run bible:propose -- --book jo --chapter 2

# Incluir os vínculos já aprovados na visão de revisão
npm run bible:propose -- --book jo --chapter 1 --include-approved --out reports/revisao-jo1

# Avaliação sem usar o próprio versículo como exemplo ou exportar sua aprovação
npm run bible:propose -- --book jo --chapter 1 --evaluate --out reports/bible-occurrence-relations-evaluation

npm run test:bible:proposals
```

A saída padrão da versão 2 fica em `reports/bible-occurrence-relations/`,
separada dos relatórios antigos em `reports/bible-alignment-proposals/`.
Nenhum relatório antigo é apagado ou promovido automaticamente. A pasta fica
fora de `src` e da publicação; seu versionamento depende da configuração do Git.

O `summary.json` lista os capítulos da execução, as fontes e seus hashes,
contagens, diagnósticos e o hash de cada arquivo gerado. O campo `fileHashes`
preserva o histórico de hashes gerados em outros filtros da mesma pasta.
Arquivos não listados em `chapters` podem ser de execuções anteriores: confira
o resumo e o `inputDigest`. Use pastas diferentes para avaliação e revisão.

Cada arquivo `<livro>/<capítulo>.json` tem `version: 2` e
`type: RELACOES_POR_OCORRENCIA`. Cada versículo preserva o texto português, a
sequência grega e duas listas:

- `relations`: vínculos entre um trecho português e um ou vários tokens gregos.
- `notes`: palavras ou tokens sem candidato, além de justificativas já aprovadas
  para termos supridos ou elementos representados pela pontuação.

Cada registro identifica referência, tipo, posição UTF-16 do trecho, texto,
tokens gregos e estado. Os vínculos incluem evidências, prioridade, justificativa
e ids de registros concorrentes. O id é estável enquanto referência, tipo,
trecho, posição e tokens forem iguais. Assim, a revisão pode identificar a
mesma relação em execuções posteriores sem depender da ordem dos candidatos.

Os estados significam:

- `PROPOSTA`: candidato sem concorrente detectado, ainda não conferido.
- `PENDENTE`: concorrência, ausência de correspondência, conflito com decisão
  aprovada ou geração incompleta. A razão é registrada.
- `APROVADA`: decisão já cadastrada em `src/alinhamentos` e confirmada contra
  o mesmo texto e a mesma sequência grega. O gerador não concede essa aprovação
  por similaridade ou por haver apenas um candidato.

Ao usar `--include-approved`, vínculos aprovados que o índice não recupera
continuam na visão de revisão. As justificativas `unlinkedPortuguese` e
`untranslatedTokens` também são mantidas como notas aprovadas. Sugestões que
contradigam essas decisões ficam pendentes. Se a tradução ou o grego tiver
mudado, as aprovações anteriores não são transferidas para as propostas.
No modo de avaliação não se exportam aprovações do versículo avaliado.
As contagens por estado incluem vínculos e notas, identificados pelo campo
`type`; não devem ser interpretadas como quantidade de palavras traduzidas.

Prioridade é uma heurística de ordenação, não uma probabilidade de acerto.
Uma proposta sem concorrente pode estar linguisticamente errada. Não há
seleção automática de ocorrências repetidas ou aplicação de exegese.

Regeneração compara cada arquivo existente com o hash da última versão gerada.
Se alguém tiver alterado um arquivo de revisão, o comando para antes de escrever
os capítulos e o preserva. Use `--out` com outra pasta para obter uma nova
rodada, mantendo a revisão existente. Não edite o manifesto ou seus hashes
para contornar essa proteção.

Estes arquivos **não são lidos pelo build para publicar tooltips**. Alterar
`status` num relatório, inclusive para `APROVADA`, não modifica a página nem o
arquivo aprovado. A importação das decisões usa o CSV do passo 3, descrito abaixo. O build
continua usando somente os arquivos em
`src/alinhamentos/<livro>/<capítulo>.json` e o fluxo de revisão já documentado.
O gerador não escreve em capítulos, dicionário, aprovados ou `.git`.

### Fontes e limitações de formato

O gerador prefere o Liquid atual quando existe e usa TXT quando não há template.
A identificação por metadados também resolve pastas com grafias diferentes do
slug, sem renomeá-las. HTML legado com spans `verse` é lido no formato original.
Erros de ids, versículos duplicados ou capítulos ausentes entram no resumo;
não se usa outra tradução silenciosamente para contornar um problema.

HTML e entidades dentro do versículo são preservados e sinalizados; não se
inventam offsets após remover marcações. Continuação TXT não numerada é
preservada e exige conferir os limites do versículo. Termos entre colchetes
permanecem identificados como supridos. Ausência de candidato não comprova
que uma palavra seja suprida ou que um original tenha sido omitido.

Resultados parciais e limites de candidatos ficam explícitos. Fontes e índice
são identificados por hashes para que revisões possam detectar dados antigos.
A versão 2 não tem campo `segments`, evitando confusão com o esquema aprovado.

### Avaliação da versão 2

Na rodada atual, foram gerados 154.247 candidatos para 258 capítulos (7.883
versículos), com os 51 versículos já cadastrados de João 1 ignorados por padrão.
Mateus 2 continua no diagnóstico de id duplicado; 309 versículos precisam de
revisão de formato.

Na avaliação de João 1 sem usar o próprio versículo como exemplo, 551 dos 758
vínculos de referência apareceram entre 1.114 candidatos (72,7%). Dos 314 sem
concorrente, 266 coincidiram exatamente com a referência (84,7%). Não se deve
aprovar automaticamente os restantes por unicidade; o arquivo preserva o
estado de proposta ou pendência.

### Histórico da versão anterior

Na versão anterior, que consultava diretamente o dicionário, foram geradas 157.540 propostas em 258 capítulos
(7.883 versículos), além de 51 versículos cadastrados que foram ignorados.
309 versículos exigem revisão de formato. Mateus 2 não foi processado porque
seu HTML repete o id `mt_2-2`, inclusive no trecho de 2:14. Esse problema já
existia no template e não foi corrigido como parte do gerador.

A avaliação dessa versão em João 1, excluindo os exemplos do próprio versículo, encontrou
557 dos 758 segmentos de referência entre 1.127 candidatos (cobertura de 73,5%).
Entre os 319 candidatos sem concorrente, 269 coincidiram exatamente com a
referência (84,3%). A comparação exige o mesmo trecho português e os mesmos
tokens na mesma ordem; reformulações equivalentes podem não ser contadas.
Esses números se referem a esse capítulo, não estimam a qualidade de todo o NT
e não justificam aprovação automática.


## CSV e importação das decisões — passo 3

### Preparar e abrir a revisão

Com as relações do passo 2 geradas, exporte um capítulo:

```bash
npm run bible:review:export -- --book jo --chapter 2
```

Isso cria dois arquivos que devem permanecer juntos:

- `reports/bible-review/jo/2.csv`: a revisão que você abre na planilha.
- `reports/bible-review/jo/2.review.json`: os dados de referência usados pelo
  importador para detectar alterações no texto, grego, dicionário e aprovados.

Não edite o `.review.json`. Ao mover ou renomear o CSV, copie também esse arquivo
com o mesmo nome-base. Não é um backup; é parte do contrato de importação.
A exportação não substitui um CSV ou manifesto já diferente: escolha outra
pasta com `--out reports/revisao-rodada2`.

É possível exportar um livro inteiro com `--book jo` sem `--chapter`, ou todos
os capítulos listados no resumo sem filtros. Cada capítulo recebe seu próprio
par CSV/manifesto. Para usar outra rodada de relações, informe
`--source reports/pasta-da-rodada`. Capítulos já aprovados só aparecem se a
rodada de origem tiver sido gerada com `--include-approved`.

O CSV usa UTF-8 com BOM, separador ponto e vírgula, aspas escapadas e CRLF.
O importador também aceita vírgula como separador. No Excel/LibreOffice,
preserve os acentos gregos e salve como **CSV UTF-8**, mantendo as colunas de
ids, posições e tokens como texto. Não salve por cima como XLSX ou CSV ANSI.
Células que poderiam ser interpretadas como fórmulas recebem escape reversível.
Os testes verificam o round-trip dos dados; não foi feita validação visual em
uma sessão nativa do Excel.

### O que preencher

A coluna editável principal é `decisao`, que começa vazia:

- `APROVAR`: publicar este vínculo após importação com `--apply`.
- `REJEITAR`: registrar que a sugestão foi descartada. Se a linha representar
  um vínculo já aprovado, retirá-lo explicitamente do arquivo aprovado.
- `PENDENTE`: registrar a dúvida sem mudar um vínculo aprovado que já exista.
- Vazio: não tomar decisão nessa linha; não remove nem aprova nada.

Quando houver várias alternativas para o mesmo trecho/token, escolha apenas
as compatíveis entre si. A importação rejeita conflitos entre aprovações.
Não basta a situação original indicar proposta única: confira a ocorrência.

As outras colunas editáveis são `tipo`, `trecho_pt`, `inicio_pt`,
`tokens_gregos` e `observacao`. As demais são referências e devem ficar intactas.
`referencia` identifica o versículo, `situacao_original` mostra o estado da
rodada, e `id` mantém a identidade da linha mesmo após ordenar ou filtrar.
`texto_versiculo` e `grego_versiculo` permitem conferir o contexto completo.
`formas_gregas`, evidências e justificativa original descrevem a sugestão de
origem; não se atualizam dentro da planilha quando você edita os tokens.

Para corrigir um vínculo, edite o trecho e sua posição e/ou os tokens, e marque
`APROVAR`. `inicio_pt` conta posições de string JavaScript (UTF-16), começando
em zero. Tokens gregos começam em 1 e aceitam listas como `5,6`. Não escreva
Strong no lugar desses números. O trecho precisa corresponder exatamente ao
texto do versículo, sem cortar uma palavra. Expressões com vários tokens são
aceitas. Não invente ids nem duplique linhas.

Para criar uma relação que faltou, reaproveite uma linha de pendência, altere
`tipo` para `VINCULO` e preencha trecho, posição e tokens. Para confirmar que
não há equivalente direto, escolha `PORTUGUES_SEM_VINCULO_DIRETO` (trecho e
posição, sem tokens) ou `GREGO_SEM_VINCULO_DIRETO` (um token, trecho/posição
portugueses vazios). Esses dois tipos exigem justificativa em `observacao`.
Não se aprova uma linha `SEM_CANDIDATO` como se ela já fosse um vínculo.

`observacao` acompanha a decisão e fica no recibo; em vínculos aprovados também
pode ser guardada como `reviewNote`. Uma observação isolada, sem decisão, não
é importada. Edições nos dados do vínculo sem uma decisão são rejeitadas.

### Conferir, aplicar e visualizar

Primeiro valide sem escrever arquivos aprovados:

```bash
npm run bible:review:import -- --file reports/bible-review/jo/2.csv
```

O resultado indica decisões, arquivo afetado, versículos, quantidade de vínculos
e pendências restantes. Qualquer referência inválida, fonte alterada, coluna de
referência editada, id duplicado ou aprovação incompatível aborta antes da gravação.
Você pode ordenar/filtrar linhas; omitir uma linha não exclui seu vínculo aprovado.

Para efetivar suas decisões explícitas:

```bash
npm run bible:review:import -- --file reports/bible-review/jo/2.csv --apply
npm run bible:align
npm run dev -- --port=8091
```

A importação atualiza somente o capítulo em `src/alinhamentos/jo/2.json`, nunca
os capítulos traduzidos, o dicionário ou outros capítulos aprovados. Não
reformata o arquivo inteiro: preserva chaves, espaçamento e entradas não afetadas.
Vínculos aprovados que não receberam decisão são preservados. Correções que
alterem o conteúdo de um vínculo não herdam automaticamente suas antigas
alternativas lexicais; os outros dados aprovados permanecem intactos.

O recibo `<capítulo>.import-<hash>.json`, ao lado do CSV, registra as decisões,
observações e hashes anterior/posterior. Não substitui o histórico Git nem gera
`.bak`. Com todas as decisões vazias, nada é aplicado.

Aprovações parciais são permitidas. O arquivo aprovado guarda `pendingReview`
para palavras e tokens ainda sem decisão. O build mostra os vínculos aprovados
e mantém as pendências no relatório. `bible:align:check` retorna saída 1 enquanto
elas existirem; o build normal continua funcionando. Capítulos parciais voltam
a entrar no gerador de relações, preservando os vínculos já cadastrados.

### Revisões posteriores e limites

Cada CSV é uma rodada baseada nas fontes e aprovados presentes na exportação.
Se a tradução, o grego, o dicionário, as relações de origem ou o capítulo aprovado
mudar, ele não pode ser aplicado silenciosamente. Uma importação que altere o
capítulo também torna antiga aquela rodada. Para continuar depois, gere novas
relações e exporte para outra pasta, preservando o CSV anterior e seu recibo.
Evite regenerar as relações na mesma pasta enquanto revisa um CSV; use `--out`
para manter a origem daquela rodada intacta.

Mudanças mecânicas anteriores à exportação podem ter seus vínculos seguros
reposicionados durante a importação. Os trechos que deixaram de ser seguros
ficam pendentes, sem escolher uma tradução nova. Mudança da sequência grega
aprovada requer revisão específica e não é reconciliada por posições presumidas.

Aprovar tooltips exige um template com shortcode `verse` e texto sem marcação
interna. TXT sem página, HTML legado e trechos com tags/entidades precisam ser
preparados e reexportados antes de aprovar vínculos publicáveis. Não se remove
marcação automaticamente para encaixar os offsets.

O passo 3 não aprova decisões linguísticas por você. Na entrega inicial, o CSV
de João 2 foi exportado com todas as decisões vazias e testado em modo de
conferência. Nenhum vínculo real novo foi aprovado pelo agente.

## Integração

Branch de trabalho: `feat/biblia-original-tooltip`. Não há merge ou commit
feito automaticamente. Antes de integrar, inclua os arquivos novos junto das
alterações em `.eleventy.js`, `package.json`, layout e CSS. Não inclua o log
`nt-missing-lemmas.log` ou o relatório gerado como parte da feature.

Ao resolver conflitos, preserve a chamada ao renderizador no shortcode `verse`,
os hooks de build e a inclusão de `bible-original.js` no layout. As alterações
de layout e CSS são aditivas: preserve os ajustes que já existem na develop.
A mudança de formato dos dados de alinhamento deve ser acompanhada dos testes.
