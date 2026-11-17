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

## Bases portuguesas por identificador TBESG — etapa 1

```sh
python3 -B tools/lxx/prepare_tbesg_bases.py
python3 -B -m unittest discover -s tests -p test_lxx_bases.py -v
```

As propostas editoriais estão em `tbesg_base_translations.tsv`, com uma base
por identificador completo dStrong. Não se usa a glosa inglesa como chave.
O preparador cruza somente as ocorrências ainda sem tradução nos livros
existentes e gera `tools/lxx/tbesg_bases_pt.json`, preservando lema, definição,
classe, identificadores e linha da TBESG, além da frequência e referências.

`BASE_BETA` é uma escolha lexical provisória, ainda não flexionada ou aplicada.
Os casos `INCERTO` possuem proposta, justificativa e `base_pt: null`, para impedir
uso automático; também aparecem em `tools/relatorios/lxx-bases-pt-pendencias.csv`.
Eventuais discordâncias de classe da fonte são registradas separadamente,
sem corrigir os campos originais. Os hashes dos artefatos de entrada e dos
livros ativos são conferidos para evitar preparar bases a partir de dados
desatualizados. O gerador da beta não consome este cadastro nesta etapa.

## Flexões das bases por identificador — etapa 2

```sh
node tools/lxx/audit_tbesg.js "tools/lxx/fontes/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt" /caminho/lxx_morph tools/relatorios/lxx-tbesg-cobertura-etapa2.json
python3 -B tools/lxx/generate_beta.py /caminho/lxx_morph --audit tools/relatorios/lxx-tbesg-cobertura-etapa2.json --bases tools/lxx/tbesg_bases_pt.json
npm run build
```

`--bases` habilita o cadastro da etapa 1. O identificador completo dStrong e a
grafia do lema devem coincidir com a mesma versão da TBESG. Entradas INCERTO
continuam bloqueadas. As traduções da beta anterior são preservadas; apenas as
lacunas são preenchidas. A etapa 2 pode ser repetida para refinar suas próprias
flexões, sem retraduzir os preenchimentos anteriores à etapa.

O gerador reconhece `ptc`, mantém alternativas de voz e distingue particípios
ativos e passivos. O particípio em composto com `ter` fica invariável, enquanto
a passiva concorda em gênero/número quando a análise traz essas informações.
A tradução portuguesa usa voz ativa para os verbos intransitivos explicitamente
listados em `inflect_beta.py`, mesmo quando a análise grega é passiva; o parsing
original permanece no relatório. Análises não reconhecidas e verbos sem dados
suficientes ficam pendentes em vez de receber uma flexão presumida.

`lxx-beta-etapa2.json` registra os preenchimentos desta etapa e sua procedência;
`lxx-beta-pendencias.csv` contém apenas lacunas não aplicadas. Nomes próprios não
recebem automaticamente a base de um substantivo comum com o mesmo identificador.
Nenhum identificador é exposto como Strong no suplemento de apresentação.

Uma auditoria já referenciada pelo relatório de aplicação deve ser preservada.
Se as fontes mudarem, gere a nova auditoria com outro nome e passe-a em `--audit`.
Isso permite comparar a geração atual com a anterior sem criar backups dos livros.

## Correspondências explícitas — etapa 3

```sh
python3 -B tools/lxx/generate_beta.py /caminho/lxx_morph --audit tools/relatorios/lxx-tbesg-cobertura-etapa2.json --bases tools/lxx/tbesg_bases_pt.json --aliases tools/lxx/tbesg_aliases_pt.json --stage 3
```

`tbesg_aliases_pt.json` registra 11 correspondências editoriais, suas bases
portuguesas, classes admitidas e evidência integral da TBESG. A fonte e cada
verbete são conferidos antes da aplicação. Não há busca aproximada automática
nem alteração dos lemas gregos. Nomes próprios não são elegíveis. Todas as
traduções das etapas anteriores são preservadas; só as lacunas são preenchidas.
O relatório `lxx-beta-etapa3.json` registra as formas e referências aplicadas.
Não execute novamente uma etapa anterior para atualizar o suplemento atual.

## Revisão editorial por forma e contexto — etapa 4

```sh
python3 -B tools/lxx/generate_beta.py /caminho/lxx_morph --audit tools/relatorios/lxx-tbesg-cobertura-etapa4.json --bases tools/lxx/tbesg_bases_pt.json --aliases tools/lxx/tbesg_aliases_pt.json --stage 4 --reviewed tools/lxx/reviewed_step4.json
```

`reviewed_step4.json` contém decisões editoriais explícitas para gentílicos e
φοβέομαι. As traduções portuguesas foram registradas por forma/análise, sem
reescrever os lemas gregos ou a morfologia. A aplicação exige o hash da auditoria,
as referências e contagens revisadas; contextos novos exigem nova revisão.
Nomes próprios e verbetes bloqueados INCERTO não podem ser liberados por esse
cadastro. Grupos que misturam sentidos ficam pendentes, com justificativa no
CSV. As 394 novas ocorrências e suas fontes são registradas em
`lxx-beta-etapa4.json` e `lxx-beta-etapa4-resumo.md`.

A reprodução da etapa 4 mantém todas as traduções anteriores à etapa e refaz
somente os preenchimentos da própria etapa. A revisão registrada é provisória
para a beta; as 1.046 lacunas restantes continuam disponíveis no CSV de pendências.

## AncientBible aprovado — etapa 5

A aprovação explícita do arquivo `lxx-ancientbible-en-revisao.json` permite
aplicar as 44 propostas (41 lemas / 112 ocorrências) ao suplemento beta.
`prepare_ancientbible_application.py` prepara as decisões por forma/análise;
`reviewed_step5.json` registra a aprovação, o hash das propostas e as evidências.
O gerador aceita `--stage 5 --reviewed tools/lxx/reviewed_step5.json`, mantendo
os demais argumentos da etapa 4. As alternativas são conservadas em vez de
selecionadas. Três ocorrências incompatíveis/incompletas exibem só a glosa base.

Casos INCERTO só são liberados quando a decisão traz candidatos aprovados
para aquele lema e o hash do arquivo aprovado confere. O cadastro original
e seu bloqueio geral são preservados. O relatório `lxx-beta-etapa5-resumo.md`
detalha as adaptações gramaticais, os fallbacks e as ressalvas semânticas.
