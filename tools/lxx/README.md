# Conversão da LXX para o interlinear

Baixe os JSONs finais de livros do diretório
<https://github.com/OpenScriptorium/lxx-morph/tree/master/db/seeds/lxx_morph>.
Mantenha os nomes originais (por exemplo, `genesis.json`) em uma pasta local
fora de `src`. Não inclua arquivos intermediários de processamento nessa pasta.
O conversor trabalha offline e não baixa nem executa conteúdo da fonte.

```sh
python3 tools/lxx/convert_lxx_morph.py /caminho/fontes/genesis.json
python3 tools/lxx/convert_lxx_morph.py /caminho/fontes
```

A saída padrão é `src/interlinear/at/gn.json`, um arquivo por livro.
Para nomes ainda não mapeados, use um arquivo individual com `--book SIGLA`.
`--output-dir PASTA` permite conferir resultados em outro local.
Saídas existentes só são substituídas com `--overwrite`.
Colisões de siglas e entradas inválidas interrompem a validação do lote antes
de qualquer gravação.

Cada arquivo contém uma lista de capítulos, como os JSONs do NT. Cada capítulo
registra `source_file` (nome original) e `source_url` (URL original no GitHub).
Cada capítulo começa com uma perícope de título vazio; os IDs são sequenciais
no livro. Os limites correspondem ao primeiro e ao último versículo recebido.
As perícopes e seus títulos poderão ser editados posteriormente.

`words[].surface` é copiado literalmente para `tokens[].lemma`, preservando
maiúsculas, diacríticos, espaços e pontuação. A ordem dos registros e palavras
é preservada. Referências com sufixo (como `1a`) são mantidas como texto e
versículos zero não são descartados. O consumidor futuro da LXX precisará
aceitar essas referências; este script não adapta a geração das páginas.

Os campos lexicais e morfológicos da fonte não são incorporados ao JSON
enxuto. Preserve os arquivos originais para consulta desses dados e auditoria.
O conversor não altera o dicionário, os JSONs do NT nem os HTMLs atuais do AT.
A conversão não equivale à revisão do texto ou das análises da fonte.
As condições de uso e atribuição da fonte continuam aplicáveis.
