# Original grego no texto da Bíblia

A feature gera painéis por palavra ou expressão durante o build do Eleventy.
A tradução, o Texto Majoritário, o dicionário e os alinhamentos aprovados não
são regravados pelo build. A cobertura inicial é **João 1:1–5**. A infraestrutura
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

## Decisões do alinhamento inicial para revisão humana

- João 1:1: as três ocorrências de “Palavra” apontam para os tokens 5, 8 e 17;
  “Deus” após “com” agrupa os tokens 11–12.
- João 1:2: “Deus” agrupa os tokens 6–7.
- João 1:3: “Todas as coisas” aponta para Πάντα; “vieram a ser” e as duas
  ocorrências de “veio a ser” têm vínculos próprios. “do que” aponta para ὃ.
- João 1:4: “Nela” agrupa Ἐν e αὐτῷ. O primeiro artigo português de “a vida”
  fica sem vínculo direto: não há artigo correspondente antes de ζωὴ.
  “das pessoas” agrupa τῶν e ἀνθρώπων.
- João 1:5: “na” agrupa ἐν e τῇ; “não a” preserva separadamente οὐ e αὐτὸ.

## Integração

Branch de trabalho: `feat/biblia-original-tooltip`. Não há merge ou commit
feito automaticamente. Antes de integrar, inclua os arquivos novos junto das
alterações em `.eleventy.js`, `package.json`, layout e CSS. Não inclua o log
`nt-missing-lemmas.log` ou o relatório gerado como parte da feature.

Ao resolver conflitos, preserve a chamada ao renderizador no shortcode `verse`,
os hooks de build e a inclusão de `bible-original.js` no layout. As alterações
de layout e CSS são aditivas: preserve os ajustes que já existem na develop.
A mudança de formato dos dados de alinhamento deve ser acompanhada dos testes.
