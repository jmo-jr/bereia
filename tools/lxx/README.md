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

## Auditoria TBESG (sem preenchimento automático)

```sh
node tools/lxx/audit_tbesg.js "tools/lxx/fontes/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt" /caminho/lxx_morph
node --test tests/test_lxx_tbesg.cjs
```

A auditoria lê somente os livros convertidos já presentes no AT. Para cada
versículo, exige o mesmo número de palavras e igualdade literal de todas as
formas com o original antes de aproveitar os lemas. Divergências ficam
registradas como falhas de alinhamento; não há tentativa de alinhamento por
aproximação. O relatório padrão fica em
`tools/relatorios/lxx-tbesg-cobertura.json` (o terceiro argumento permite outro
destino e substitui esse relatório quando executado novamente).

O relatório preserva os campos TBESG, IDs completos, números de linha,
referências de ocorrência e hashes SHA-256 das entradas. Registros com IDs
distintos não são fundidos. A busca sem diacríticos fica separada da busca com
diacríticos: ambas produzem candidatos, não decisões lexicais. A confiança da
análise original é registrada, sem se presumir que foi validada.

`Morph` da TBESG descreve a categoria lexical, não a flexão de cada ocorrência.
Tradução portuguesa e transliteração da forma precisam de preparação/revisão;
a transliteração TBESG pertence ao lema. Não há escrita no dicionário nem
integração ao build nesta etapa.

Dados TBESG: Tyndale House e STEPBible.org, CC BY 4.0.
Fonte: <https://github.com/STEPBible/STEPBible-Data/tree/master/Lexicons>.
O processamento seleciona verbetes e associa candidatos às formas da BEREIA;
os campos originais em inglês não são traduzidos ou corrigidos pelo script.

## Complemento com o léxico local

```sh
node tools/lxx/audit_local_supplement.js
node --test tests/test_lxx_local_supplement.cjs
```

Lê apenas os registros `not_found` da auditoria TBESG e cruza com
`src/_data/lxx/lexico_lxx_gr-pt-heb.json`. Não modifica a auditoria anterior.
Gera `tools/relatorios/lxx-lexico-complementar.json`, mantendo os campos do
verbete, referências, hashes e o caminho de cada evidência no léxico local.
Busca por lema tem prioridade; coincidências só pela forma flexionada são
marcadas como fracas, incluindo colisões de nomes próprios. Todos os candidatos
continuam INCERTO. O processamento não traduz nem altera os livros ou dicionários.

## Suplemento beta aplicado

Após a aprovação para a versão beta, `generate_beta.py` prepara traduções e
transliterações por ocorrência, usando a auditoria e os originais locais:

```sh
npm run dict:generate
node tools/lxx/audit_tbesg.js "tools/lxx/fontes/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt" /caminho/lxx_morph tools/relatorios/lxx-tbesg-cobertura-beta.json
python3 -B tools/lxx/generate_beta.py /caminho/lxx_morph --audit tools/relatorios/lxx-tbesg-cobertura-beta.json
npm run build
```

A saída `src/_data/lxx/supplement-beta.json` é consultada apenas nas páginas
da LXX, depois do dicionário existente. Não contém Strong, verbete ou links
para detalhes. As referências de TBESG/Strong ficam somente no relatório
de procedência `tools/relatorios/lxx-beta-aplicacao.json`.

Ordem das bases portuguesas: verbete BEREIA do mesmo lema/identificador;
glosses TBESG traduzidas em `beta_glosses.json`; definição local com o mesmo
lema e uma única base curta. Formas equivalentes por apóstrofo podem reaproveitar
o `pt` já existente. Ajustes editoriais do suplemento estão explícitos no
gerador. Definições locais encontradas apenas em listas de flexão não são usadas.

As formas portuguesas são produzidas pelas rotinas existentes de flexão do
projeto, sem escrever no dicionário principal. A análise do lxx-morph continua
provisória; alternativas de caso, gênero ou voz são mantidas quando reconhecidas.
O código mostrado é a classe gramatical; a descrição pode conter os detalhes
da fonte. Nomes sem equivalência portuguesa segura são transliterados; não se
atribui a eles o significado de palavras comuns homógrafas.

Quando falta uma base portuguesa adequada, a tradução permanece vazia e a
ocorrência recebe transliteração. Todas essas lacunas são registradas em
`tools/relatorios/lxx-beta-pendencias.csv`. Os relatórios e amostras anteriores
são retratos da auditoria inicial, preservados para histórico; o relatório e
CSV com prefixo `lxx-beta-` representam o estado atual da aplicação beta.

Os hashes dos livros são verificados no carregamento. Um JSON do AT alterado
suspende o suplemento daquele livro até que a auditoria e o suplemento sejam
regenerados, evitando deslocamento de traduções por posição. Os originais e o
dicionário derivado também são verificados durante a geração.

As páginas atribuem os dados a Tyndale House/STEPBible.org (CC BY 4.0),
Septuaginta Online e BEREIA, identificando as adaptações da versão beta.
O léxico original, os livros gregos e os relatórios históricos são preservados.
