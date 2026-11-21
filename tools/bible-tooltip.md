# Original grego no texto da Bíblia

A feature gera painéis por palavra ou expressão durante o build do Eleventy.
A tradução, o Texto Majoritário, o dicionário e os alinhamentos aprovados não
são regravados pelo build. A cobertura inicial é **João 1 completo (51 versículos)**. A infraestrutura
funciona para novos capítulos, mas não inventa seus primeiros alinhamentos.

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

## Gerador de propostas em lote

O gerador auxilia o primeiro alinhamento dos demais capítulos. É uma etapa
separada do build de publicação: seus resultados **não são aprovados nem
consumidos pelo renderizador**.

```bash
# Demais capítulos do NT; ignora versículos já cadastrados em src/alinhamentos
npm run bible:propose

# Um livro ou capítulo (abreviações jo, mt, 1co etc.)
npm run bible:propose -- --book jo
npm run bible:propose -- --book jo --chapter 2

# Inspecionar propostas também para versículos cadastrados
npm run bible:propose -- --book jo --chapter 1 --include-approved --out reports/propostas-jo1

# Avaliar contra João 1 sem usar o próprio versículo como exemplo
npm run bible:propose -- --book jo --chapter 1 --evaluate --out reports/bible-proposals-evaluation

npm run test:bible:proposals
```

A saída padrão fica em `reports/bible-alignment-proposals/`, fora da publicação
e do Git. `summary.json` lista os arquivos desta execução, contagens, origens,
hashes SHA-256 dos insumos e diagnósticos de capítulos não processados. Os
arquivos `<livro>/<capítulo>.json` guardam o texto português, todos os tokens
gregos e os candidatos. Execuções com filtro não apagam arquivos anteriores;
consulte somente os arquivos listados no resumo atual e confira `inputDigest`.
Use `--out` com pastas diferentes para avaliações e lotes parciais.

As fontes são o Texto Majoritário, os campos `pt` e `traducao` do dicionário
definitivo e os segmentos/equivalências já cadastrados em `src/alinhamentos`.
Expressões aprendidas só são reutilizadas quando seus tokens gregos formam uma
sequência contígua; agrupamentos contextuais cruzados não viram regras gerais.
A busca preserva acentos portugueses. Uma busca grega que dependa de ignorar
diacríticos é identificada como aproximada, com aviso e prioridade baixa.
Notações como `ele(a)` não são expandidas por adivinhação.

Cada candidato traz `start`, `text`, `tokens`, evidências, prioridade e
identificadores de candidatos conflitantes. A prioridade é uma heurística para
organizar a revisão, não uma probabilidade de acerto. `CANDIDATO_UNICO` significa
apenas que não há concorrente entre as propostas geradas. `AMBIGUO` preserva
alternativas que disputam palavras portuguesas ou tokens gregos. Não há seleção
automática de uma ocorrência repetida ou aplicação de uma tradução contextual.
Até candidatos únicos podem estar linguisticamente errados ou incompletos.

`unmatchedPortuguese` e `unmatchedGreek` indicam ausência de candidato, não
atestam palavras supridas ou originais omitidos. Termos entre colchetes são
mantidos como suprimentos explícitos. Resultados truncados são identificados e
nunca classificados como únicos. HTML/entidades ficam intactos e sinalizados,
sem propostas para o versículo; é necessário tratar o formato separadamente.

O gerador prefere o Liquid atual quando existe e usa TXT apenas quando não há
template correspondente. A identificação por metadados também resolve pastas
com grafias diferentes do slug cadastrado, sem renomear arquivos. Os templates
antigos com spans `verse` são lidos em seu formato original. Erros de ids,
versículos duplicados ou capítulos ausentes são registrados; não se usa outra
tradução silenciosamente para contornar um erro. Continuação TXT não numerada
é preservada e exige conferência dos limites do versículo.

Na rodada inicial desta branch, foram geradas 157.540 propostas em 258 capítulos
(7.883 versículos), além de 51 versículos cadastrados que foram ignorados.
309 versículos exigem revisão de formato. Mateus 2 não foi processado porque
seu HTML repete o id `mt_2-2`, inclusive no trecho de 2:14. Esse problema já
existia no template e não foi corrigido como parte do gerador.

A avaliação de João 1, excluindo os exemplos do próprio versículo, encontrou
557 dos 758 segmentos de referência entre 1.127 candidatos (cobertura de 73,5%).
Entre os 319 candidatos sem concorrente, 269 coincidiram exatamente com a
referência (84,3%). A comparação exige o mesmo trecho português e os mesmos
tokens na mesma ordem; reformulações equivalentes podem não ser contadas.
Esses números se referem a esse capítulo, não estimam a qualidade de todo o NT
e não justificam aprovação automática.

Para revisar um capítulo, confira cada candidato com a ocorrência grega,
selecione/ajuste os vínculos e registre somente os aprovados em
`src/alinhamentos/<livro>/<capítulo>.json`, no esquema `segments` já descrito.
Complete também os trechos sem candidato e as justificativas necessárias.
O gerador não oferece um comando de aprovação em massa. Os arquivos gerados
não têm campo `segments`, para evitar que sejam confundidos com aprovados.
Depois, rode `npm run bible:align:check` e confira a página. A próxima geração
passará a usar os novos exemplos cadastrados.

Não edite os relatórios como lugar definitivo de aprovação: são regeneráveis,
e a mesma execução pode sobrescrevê-los. Preserve decisões aprovadas nos
arquivos de alinhamento e justificativas do projeto. O gerador não escreve em
`src`, no dicionário, nos capítulos, nos aprovados ou em `.git`; também bloqueia
saídas por links simbólicos que apontem para essas fontes.

## Integração

Branch de trabalho: `feat/biblia-original-tooltip`. Não há merge ou commit
feito automaticamente. Antes de integrar, inclua os arquivos novos junto das
alterações em `.eleventy.js`, `package.json`, layout e CSS. Não inclua o log
`nt-missing-lemmas.log` ou o relatório gerado como parte da feature.

Ao resolver conflitos, preserve a chamada ao renderizador no shortcode `verse`,
os hooks de build e a inclusão de `bible-original.js` no layout. As alterações
de layout e CSS são aditivas: preserve os ajustes que já existem na develop.
A mudança de formato dos dados de alinhamento deve ser acompanhada dos testes.
