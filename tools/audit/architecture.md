# Auditoria lexical e morfológica — etapa 1

## Execução

A partir da raiz, com Python 3.9+ e Node (este apenas nos testes):

```sh
python3 -B tools/audit/audit_tm.py
python3 -B -m unittest tools.audit.test_audit_tm -v
python3 -B tools/audit/audit_tm.py --books JO --output reports/audit/joao
python3 -B tools/audit/audit_tm.py --no-cache
```

O comando não chama gerador, build, migração, atualização do estado linguístico
nem rotinas de preenchimento. Não altera nenhuma fonte. Relatórios anteriores
no mesmo diretório de saída são atualizados apenas quando o conteúdo muda.
Para conservar execuções com fontes diferentes, escolha outro `--output`.
`reports/` é ignorado pelo Git no projeto; os relatórios permanecem disponíveis
localmente. Código, instruções e testes ficam em `tools/audit/`.

## Fontes inspecionadas

- `src/interlinear/nt/*.json`: 27 livros; a forma textual está em `tokens[].lemma`,
  apesar do nome do campo. Guardar cada grafia e referência, incluindo espaços.
- `src/_data/nt/dict_lex_nt-lxx_greek-pt.json`: fonte completa atual, organizada
  por Strong literal, com lema e flexões. O caminho sem `/nt` mencionado no
  AGENTS.md geral já não existe. Não recriá-lo nem migrar dados nesta etapa.
- `tools/dictionary/core.js` e `generate.js`: `flatten` conserva apenas a primeira
  análise por forma literal; `buildFormIndex` conserva todos os pares Strong/flexão.
  O auditor verifica a projeção e o índice existentes sem executar o gerador.
- `src/_data/nt/dict_flex_nt-lxx_greek-pt.json`: projeção usada pela consulta.
- `src/_data/nt/dict_form_index_nt-lxx_greek-pt.json`: índice multianálise, a
  preservar na substituição futura da consulta.
- `src/_data/nt/index.js`: lista `NORMALIZATION_EXCEPTIONS`, casos especiais,
  normalização e seleção da primeira chave. O auditor lê a lista diretamente;
  não mantém uma cópia manual divergente. Os testes exercitam a consulta real.
- `src/assets/js/strong-drawer.js`: filtra flexões por NFD sem marcas e caixa.
  Essa operação também reúne flexões distintas dentro de um mesmo Strong.
- `tools/tmnt/with-parsing/*.csv`: Strong e parsing Robinson por versículo,
  com grafia sem diacríticos. São evidências locais auxiliares, não a autoridade
  da grafia do TM. Só comparar tokens após validar o versículo inteiro.
- `tools/tmnt/no-variants/*.csv`: outra coleção local, sem o parsing entre
  chaves da coleção anterior; não misturar automaticamente essas testemunhas.
- `tools/preenche_abrev_morf_tm.py`: indexa por forma sem marcas/sigma e escolhe
  parsing agregado, um risco adicional de colapso se reutilizado. Não executado.
- `tools/preenche_strongs.py`: referencia `src/_data/strongs_greek_pt_defs.json`,
  ausente no checkout inspecionado.
- `tools/dictionary/migrate.js`: referencia `src/_data/archive/strongsg.js`,
  também ausente. Os lemas já importados permanecem no léxico atual; não se
  deve simular verificação com a fonte histórica indisponível.
- `tools/lxx/fontes/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt`:
  fonte lexical disponível para a etapa 2, sem autoridade para atribuir parsing
  contextual às flexões do NT. Preservar atribuição/licença da fonte.
- `tools/dictionary/compare-tm.js`: comparação anterior ignora caixa na chave
  chamada exata. A auditoria nova separa literal, NFC e candidatos por caixa.

## Contratos e artefatos

`inventario.json` contém versão de esquema, escopo, hashes SHA256, fontes
referenciadas ausentes, critérios, exceções atuais, coerência dos derivados,
alinhamento de todos os versículos e todas as formas, com referências de token
baseadas em 1. `strong` conserva os caracteres do identificador; `flexao` usa
índice baseado em 0. O par é estável apenas junto ao hash do léxico.

As classes primárias são mutuamente exclusivas: `exata`, `somente_nfc`,
`ausente`. Candidatos por caixa ou remoção de marcas ficam explicitamente em
campos separados (`situacao_normalizacao`), inclusive quando há vários. Eles
não contam como cobertura. `ambiguidades` identifica múltiplas análises
literais/NFC; não identifica automaticamente erro linguístico ou pendência de
revisão do dicionário. As regras de ignorar ambiguidades no fluxo de revisão
continuam válidas; esta auditoria estrutural não cria CSV de revisão.

`inconsistencias.json` recorta formas com divergência de Strong ou morfologia
entre evidências alinhadas e entradas exatas/NFC ou resultado da consulta atual.
Divergências são sinais para revisão humana. Não são correções comprovadas.
O adaptador nominal compara N-DSF com S-DFS, por exemplo. Códigos idênticos
são registrados, mas isso não verifica a descrição textual `morfologia` nem
comprova a correção do parsing. Códigos verbais/compostos de convenções diferentes
ficam `nao_comparavel`; ampliar adaptadores exige testes próprios.

`caso-arche.json` reúne grafias relacionadas presentes no TM, referências,
resultado atual, evidências e o grupo 746 completo. `resumo.md` apresenta
contagens, limites e a proposta de correção, sem tabelas.

O cache em `.cache/` guarda inventários e parsing por livro, com chave derivada
do conteúdo dos dois arquivos, do script e da versão. O resultado integral é
recalculado, incluindo o dicionário e a consulta atuais. Cache frio, quente e
`--no-cache` produzem relatórios byte a byte iguais. Não há data, caminho absoluto
ou estado do cache no relatório. `--books` gera relatório parcial explícito,
nunca o apresenta como auditoria integral. O cache é descartável.

## Proposta antes de alterar dados

1. Revisar formas sem cobertura por referência, distinguindo caixa, variantes
   de acento, espaços e flexões ausentes. Não converter candidatos em aliases.
2. Para ἀρχῇ, criar proposta de flexão própria no Strong 746, com dativo e
   tradução humana; manter ἀρχή como nominativo. A grafia ἀρχῇ está no TM em
   AT 11:15, FP 4:15, JO 1:1, JO 1:2 e LC 20:20. AT 11:15 não passou pelo
   alinhamento auxiliar e não recebe parsing inferido das demais ocorrências.
3. Preparar consulta literal/NFC com todas as análises. Aplicar filtros de
   Strong/parsing apenas quando houver evidência contextual validada; sem essa
   evidência, mostrar a ambiguidade. Remoção de diacríticos só sugere candidatos.
4. Validar cobertura e regressões da consulta e painel antes de substituir
   fallback e exceções. Mesmo uma forma já existente pode hoje ser sombreada
   pela primeira chave normalizada. Conservar homógrafos em toda a cadeia.

## Interface planejada para a etapa 2

Produzir propostas separadas de auditoria: nível `lema` (Strong literal, lema,
verbetes) e nível `flexao` (Strong literal, índice, forma, análises). Cada proposta
terá hash da fonte, valores anteriores integrais, evidências por referência,
categoria (`erro_objetivo`, `alternativa_aceitavel`, `preferencia_estilistica`,
`dependente_de_contexto`, `informacao_insuficiente`) e estado da decisão humana.

Identidade por lema ou Strong não implica identidade de flexão. Consolidação,
renomeação, exclusão e tradução exigem decisão específica; nenhuma é feita aqui.
Uma futura aplicação deve validar hashes e detectar conflitos antes de escrever,
preservar ordem e formatação, atualizar o estado linguístico conforme AGENTS.md
e regenerar produtos somente na etapa autorizada. Não alterar baseline nem
relatório histórico para acomodar a auditoria.

## Triagem e consulta em paralelo

```sh
python3 -B -m tools.audit.triage_tm
python3 -B -m unittest tools.audit.test_audit_tm tools.audit.test_triage_tm -v
npm test > reports/audit/tm/npm-test.log 2>&1
node tools/audit/diagnose_tests.js
```

`triage_tm.py` consome o inventário da etapa 1 e recusa hashes desatualizados.
Gera em `reports/audit/triagem/` propostas estruturais, comparação das consultas,
piloto e resumo em JSON/Markdown. Todas as propostas ficam pendentes; não há
aplicador nem escrita nos dados originais. As categorias gráficas têm prioridade:
espaços marginais, caixa, agudo/grave na mesma posição, outros acentos, outras
marcas e ausência de candidatos. Cada candidato também conserva sua própria
categoria. Isso impede apresentar todo um grupo como equivalência morfológica.

Na primeira triagem integral, os 2.774 casos se distribuem em 4 espaços, 1.422
diferenças de caixa, 636 de agudo/grave, 539 de outros acentos e 173 de outras
marcas. O inventário inicial conta 1.423 casos de caixa: um deles (`Ὦ `) também
tem espaço marginal e recebe prioridade de espaço na triagem. Não houve alteração
nas contagens do inventário ou nos dados. As três grafias sem candidatos são
um subconjunto dos quatro casos com espaços.

`strict_lookup.py` é um protótipo Python isolado da aplicação. Aceita somente
literal/NFC, preserva caixa, espaços e marcas e retorna todas as análises
canonicamente equivalentes, inclusive quando uma grafia literal existe. Não
filtra homógrafos por preferência nem usa o Strong para inventar cobertura.
Uma futura integração JavaScript deve preservar esse contrato com regressões
próprias; importar o protótipo não muda a consulta em produção.

A comparação em paralelo identifica sete formas cobertas mas encobertas pela
normalização da consulta atual, além das lacunas de cobertura. Isso não equivale
a sete erros lexicais: há variação de acento com a mesma análise e há mudanças
de caso/Strong. Conferir cada referência em `comparacao-consultas.json`.

O piloto `piloto-arche.json` inclui as ocorrências gregas e traduções existentes,
com hashes adicionais dos capítulos consultados. A proposta de glosas foi
preparada para revisão humana. O usuário definiu `traducao` como
“no princípio, ao principado” e `pt` como “no princípio”. A decisão está em
`tools/audit/decisions.json` e é reaplicada aos relatórios em cada execução,
preservando a proposta anterior como histórico.
As glosas foram aplicadas à nova flexão, sem atribuição contextual automática. O dativo S-DFS
é mantido separado dessa decisão lexical. A tradução existente de LC 20:20
fundamenta a necessidade de examinar a acepção de poder, sem alterar o capítulo.

`diagnose_tests.js` analisa o log completo de `npm test`, reproduz apenas as
comparações históricas e o título, em leitura, e registra as cinco causas.
Não repete builds com consumo de memória alto, não executa o gerador nem muda
testes históricos. A ausência de Strong histórico e as divergências de contrato
ficam explícitas; não se cria baseline substituto para obter uma suíte verde.

## Aplicação do piloto ἀρχῇ

Após a definição das glosas e a solicitação do usuário para avançar, a flexão
foi acrescentada ao final do Strong literal 746 (índice 6), sem alterar os seis
registros anteriores, sua ordem ou a grafia ἀρχή. Campos da nova flexão:

- `grego`: `ἀρχῇ`; transliteração `archē`, conforme a rotina local.
- `traducao`: `no princípio, ao principado`; `pt`: `no princípio`.
- `abrev_morf`: `S-DFS`; `morfologia`: `Substantivo - Dativo Feminino Singular`.
- `ocorrencias`: `"5"` (NT); `ocorrencias_lxx`: `22`, verificadas por literal/NFC
  nos JSONs atuais, sem agregar formas que apenas compartilham letras.
- `lxx`: lista vazia, conforme a estrutura das flexões do grupo; referências
  documentadas separadamente no relatório da aplicação, sem inferir links.

Os derivados foram regenerados e o estado linguístico atualizado por
`npm run dict:review-state`. Baseline, backups e relatório histórico de migração
permaneceram intactos. A decisão em `decisions.json` passou a aplicada; o caso
deixa de integrar propostas pendentes, mas continua no relatório do piloto.

O loader em produção agora consulta a chave literal e depois NFC antes do
fallback existente. O fallback ainda é necessário enquanto 2.773 grafias não
têm cobertura literal/NFC; ele continua sendo um risco explícito da migração,
nunca comprovação de identidade morfológica. Nenhuma exceção foi removida ou
acrescentada. A prioridade também impede que formas exatas já cobertas sejam
encobertas pela primeira chave sem marcas, preservando o índice multianálise.

O painel Strong seleciona somente flexões literais/NFC, incluindo todas as
análises canonicamente equivalentes. Quando não encontra uma flexão, usa a
apresentação de dados da ocorrência já existente, sem apresentar a análise de
um candidato sem marcas como se fosse da forma selecionada.

Regressões do piloto e do painel real com DOM mínimo:

```sh
node --test tools/audit/arche.test.js
```

Esse teste também confronta a emulação Python com o loader JavaScript para
todas as grafias do TM. Relatórios em `reports/audit/aplicacao-arche/` registram
referências, hashes, verificações de preservação e diferenças antes/depois da
consulta. A auditoria e a triagem continuam sendo operações somente leitura.

## Lote de agudo/grave

```sh
python3 -B -m tools.audit.audit_accents
python3 -B -m unittest tools.audit.test_audit_accents -v
```

O lote seleciona somente formas ainda ausentes, com candidato que difere por
agudo/grave na mesma posição, conforme a triagem. A comparação gráfica conserva
espíritos, trema, circunflexo e iota subscrito; caixa é documentada como diferença
adicional. Candidatos de outras categorias não são descartados: bloqueiam uma
minuta de inclusão automática.

Em `reports/audit/agudo-grave/`, `revisao.json` registra cada candidato, seus
campos originais, Strong literal, índice de flexão, códigos e referências por
evidência. `sugestoes.md` apresenta minutas completas para revisão de glosas;
`incertos.md` e `divergencias.md` apresentam as pendências em listas, sem tabelas.
O script não aplica nada nem atualiza o estado linguístico. Aprovação do piloto
ἀρχῇ não se estende a esse lote.

Uma minuta SUGERIR exige candidato único, parsing alinhado em todas as ocorrências,
compatibilidade em todas as análises comparáveis, descrição coerente e ausência
de outros candidatos por marcas. Mesmo assim, as glosas são apenas propostas
copiadas do candidato para aprovação; identidade lexical não é inferida de acento.
As contagens NT e LXX da minuta são recalculadas para a grafia original; vínculos
LXX do candidato não são copiados. A contagem LXX não atribui Strong aos tokens.

Os adaptadores cobrem substantivos/adjetivos simples, classes invariáveis
explicitamente relacionadas e verbos simples com voz explícita. A ordem dos
campos difere entre BEREIA e Robinson; a fonte é mantida integralmente, incluindo
prefixos de segundo paradigma. Vozes deponentes, códigos incompletos, códigos
combinados e análises que exigem interpretação permanecem não comparáveis.
Sincretismo neutro nominativo/acusativo não cria uma pendência própria.

Na execução inicial, 636 formas (26.554 tokens do TM) produziram 255 minutas
SUGERIR (672 tokens) e 381 casos INCERTO. Os grupos principais são exclusivos;
os sinais secundários podem se sobrepor. Os oito casos com divergência de Strong
e os 41 com análises morfológicas diferentes não são declarados erros objetivos.
Por exemplo, δωρεὰν apresenta G1432/ADV e G1431/N-ASF nas evidências: um candidato
gráfico único não basta para escolher uma análise ou tradução para toda a forma.

O relatório inclui hashes dos JSONs consultados da LXX, além das fontes do
inventário e da implementação. A execução recusa inventário desatualizado e
confere os hashes ao final. O teste de integração recria o inventário em área
temporária, compara duas execuções byte a byte e verifica fontes intactas.

## Aplicação aprovada das 255 minutas

O usuário aprovou as 255 minutas SUGERIR do relatório original de agudo/grave.
A aprovação, vinculada ao SHA256 desse relatório e aos hashes do léxico antes e
depois, está em `tools/audit/approvals/agudo-grave-255.json`. O manifesto registra
todos os valores aprovados, Strong literais, novos índices e referências.
`decisions.json` aponta para o manifesto, sem ampliar a aprovação aos INCERTO.

A aplicação em `apply_approved_accents.py` é separada da auditoria. Ela verifica
o manifesto, o relatório e as fontes, acrescenta somente as minutas ao final de
cada grupo e recusa conflitos, formas já cobertas literalmente/NFC e alterações
nos candidatos originais. Não usa remoção de marcas para criar associações.
O posicionamento textual é obtido pelo parser JSON, sem reformatar o arquivo.
Uma reversão em memória comprova a preservação de todos os bytes anteriores.
Repetir a aplicação com a mesma fonte final é uma operação sem escrita.

```sh
python3 -B -m tools.audit.apply_approved_accents --approval tools/audit/approvals/agudo-grave-255.json --check
python3 -B -m unittest tools.audit.test_apply_approved_accents -v
node --test tools/audit/approved_accents.test.js
```

Foram acrescentadas 255 flexões em 188 grupos, cobrindo literalmente 672 tokens
do TM. Nenhuma entrada ou índice anterior foi alterado. Os derivados foram
regenerados e o estado linguístico atualizado explicitamente. A auditoria passou
de 2.773 para 2.518 grafias sem cobertura literal/NFC; o fallback legado continua
ativo para as lacunas restantes. A auditoria geral também passou a respeitar o
sincretismo neutro nominativo/acusativo já aceito na revisão do lote, evitando
classificar `δεσμά` como divergência apenas por esse caso.

O relatório original `reports/audit/agudo-grave/revisao.json` permanece intacto,
como evidência da aprovação. A execução atual foi gravada em `pendentes/`, sem
sobrescrevê-lo. Os 381 INCERTO originais permanecem em
`reports/audit/aplicacao-agudo-grave/pendencias.json` e `pendencias.csv`; o CSV
contém somente pendências não aplicadas. Desses casos, 26 agora são classificados
como diferenças apenas de caixa, pois a inclusão de outra grafia tornou visível
esse candidato mais próximo. Não foram aplicados nem excluídos do histórico.
Os outros 355 continuam no grupo agudo/grave da auditoria atual.

`reports/audit/aplicacao-agudo-grave/` contém o recibo, hashes, conferência de
preservação, comparação da consulta antes/depois, testes e resumo da aplicação.
Nenhum backup, baseline, relatório histórico de migração ou capítulo bíblico foi
alterado pela aplicação; nenhum commit foi criado.

## Consulta insensível a caixa

Por orientação do usuário, a chave de consulta ignora caixa com
`toLowerCase().normalize('NFC')`, conservando acentos, espíritos, trema, iota
subscrito e espaços. A grafia exibida continua sendo a do token do TM. Nenhuma
palavra foi convertida para minúsculas nos JSONs; a identificação de nomes
próprios não é inferida para reescrever o texto. Não se usa casefold que expanda
o iota subscrito. Essa equivalência dispensa duplicar entradas só pela caixa.

O loader usa literal, NFC, caixa e, durante a migração, o fallback legado.
NT e LXX recebem o índice completo de formas. Colisões entre formas canônicas
diferentes ou Strong diferentes não escolhem o primeiro registro nem recorrem
ao fallback. Uma só forma canônica e um só Strong mantêm a projeção de
compatibilidade já existente, expondo em `analises_dicionario` todos os pares
Strong/índice quando houver múltiplas análises. Isso não funde registros nem
resolve ambiguidades gramaticais por capitalização.

O painel aplica a mesma equivalência de caixa depois da tentativa literal/NFC e
conserva todas as análises da forma. A auditoria distingue `somente_caixa` de NFC
e conserva os candidatos completos. A comparação literal continua disponível
na biblioteca Python por `StrictLookup(lexicon, ignore_case=False)`.

A verificação atual encontrou 1.449 grafias sem correspondência literal/NFC
que correspondem por caixa, em 9.441 tokens. O número histórico de 1.448 excluía
um caso com espaço marginal já presente também na entrada correspondente;
nenhum espaço foi retirado. Com essa equivalência, restam 1.069 grafias sem
correspondência sem retirada de diacríticos. `Εὗρον` e `Οὐ` mantêm as múltiplas
análises do índice sem mudança nos registros. Relatórios em
`reports/audit/caixa/` foram gerados separadamente dos relatórios aprovados.

Regressões: `node --test tools/audit/case_lookup.test.js`. Nenhum dicionário,
texto do TM/LXX, tradução, baseline ou estado linguístico foi alterado por essa
mudança de consulta. As exceções legadas continuam preservadas.

## Lista positiva de equivalências agudo/grave

O usuário autorizou equivalências validadas sem duplicar ou consolidar entradas.
O registro separado está em `src/_data/nt/greek_accent_aliases.json`. Cada alias
preserva origem, destino Strong/índice, assinatura da identidade morfológica,
referências NT e parsing que fundamentam a associação. Não altera a entrada
canônica nem remove qualquer uma das 255 inclusões anteriores.

A regra aceita uma única troca agudo/grave na última vogal, conservando todos os
outros sinais. É conservadora para grafias que exigem análise adicional; exclui
interrogativos τίς/τί, elisão, espaços, hífens e mudanças de posição de acento.
O fundamento gramatical é Smyth, §154, registrado com URL no manifesto.

Como os 355 casos restantes têm provas parciais, o escopo é **por ocorrência**:
livro, capítulo, versículo e posição do token. A construção revalida diretamente
os JSONs/CSVs, exige alinhamento do versículo inteiro, Strong literal compatível,
código e descrição coerentes e destino único. Referências repetidas em perícopes
são verificadas em todas as cópias relevantes. Não se transfere parsing de uma
cópia alinhada para outra não alinhada.

Na primeira construção, 170 pares foram autorizados em 13.076 referências
distintas, correspondentes a 13.092 tokens na estrutura dos JSONs. Restaram
10.908 tokens pendentes; todas as 355 grafias ainda têm alguma ocorrência sem
prova. Destas, 185 não têm alias ativo. Referências únicas e tokens são contados
separadamente, sem editar ou deduplicar o TM.

A consulta tenta literal/NFC e caixa antes do alias. Nos casos controlados, sem
referência ou prova válida, o resultado é pendente e não atravessa o fallback
sem marcas. Outras famílias continuam sob o mecanismo legado enquanto a migração
prossegue. Os aliases não são usados na LXX, para a qual não foi validado parsing.

Hashes do TM e parsing validam cada livro. Se a evidência mudar, os aliases desse
livro ficam pendentes até reconstrução. Mudança de Strong, forma, código ou índice
do destino também bloqueia o alias; glosas e contagens aprovadas da entrada
canônica propagam-se sem duplicação. As contagens da grafia original ficam em
campo separado, e o painel identifica a forma de referência sem mudar a exibição
do token. Os totais gerais de cobertura literal/caixa continuam separados da
cobertura contextual parcial; não se declara a grafia inteira resolvida por
existirem algumas ocorrências comprovadas.

```sh
python3 -B tools/audit/audit_tm.py --output reports/audit/aliases/base
python3 -B -m tools.audit.build_accent_aliases
python3 -B tools/audit/audit_tm.py --output reports/audit/aliases/atual
python3 -B -m tools.audit.build_accent_aliases --inventory reports/audit/aliases/atual/inventario.json --check
python3 -B -m unittest tools.audit.test_accent_aliases -v
node --test tools/audit/accent_aliases.test.js
```

O registro é determinístico e não depende dos resultados do próprio resolvedor:
reconstruí-lo a partir de auditoria com aliases ativos produz o mesmo manifesto.
Os relatórios, CSV de pendências e provas de integração estão em
`reports/audit/aliases/`. O dicionário, índices, TM, LXX, traduções e estado
linguístico permanecem intactos. Não foram criados backups nem commit.

## Revisão editorial dos verbetes por lema

A rodada autorizada de promoção analisa 551 grupos com overrides de `verbete`:
546 possuem divergência textual e cinco apenas repetem o lema. O manifesto
`tools/audit/approvals/verbetes-lema.json` registra escolhas editoriais, valores
anteriores/posteriores, índices e textos flexionais, pendências e referências à
cópia local do TBESG. Não há regra automática de preferir o conjunto mais longo.
Foram selecionados 73 lemas; 16 grupos têm pendências (um deles também recebeu
uma melhoria parcial). Os demais grupos permanecem sem alteração, sem que isso
certifique cada sinônimo anterior ou autorize remover os overrides.

`promote_lemma_verbetes.py` é uma aplicação separada, limitada aos campos de lema
do manifesto. Verifica hashes e valores revisados, altera somente os intervalos
das strings JSON e recusa dados novos. A aplicação é idempotente. Não modifica
flexões nem o TM; os 4.784 verbetes flexionais continuam intactos.

```sh
python3 -B -m tools.audit.promote_lemma_verbetes --apply
npm run dict:generate
npm run dict:review-state
python3 -B -m tools.audit.promote_lemma_verbetes --check
python3 -B -m unittest tools.audit.test_promote_lemma_verbetes -v
```

Os relatórios JSON, Markdown e CSV de pendências ficam em
`reports/audit/verbetes-lema/`. São reproduzíveis a partir do manifesto versionável;
como os demais relatórios do projeto, o diretório está ignorado pelo Git. O comando
sem opções somente gera relatórios, sem aplicar dados. Após a geração do léxico,
auditoria e aliases devem ser reconstruídos pelo fluxo anterior para atualizar
o hash de referência; nesta rodada, as equivalências contextuais não mudaram.

O gerador ainda prioriza `flexao.verbete`. Apenas `αἰτοῦντί`, `ἀσπάσησθε` e
`ἔσχατον`, que não têm override, herdam imediatamente a mudança de lema. Uma
futura remoção dos campos exige resolver as pendências, avaliar cada override
e comparar os resultados antes/depois, preservando os identificadores Strong,
os homógrafos e a segmentação de locuções. Esse passo não foi executado.

## Auditoria de agrupamentos e consistência morfológica

`audit_morphology.py` examina toda a fonte lexical atual, sem reaplicar as
escolhas anteriores e sem escrever em dicionários, TM, índices ou traduções.
Compara classe lexical do TBESG, referência Strong do verbete, código local,
descrição, parsing auxiliar e registros repetidos por forma literal/NFC.
Divergências de classe ou entre fontes permanecem revisão manual: substantivação
não transforma automaticamente um particípio em substantivo. As hipóteses de
código candidato usam apenas parsing de versículos integralmente alinhados e não
comprovam exclusividade morfológica.

O adaptador distingue tempo/modo/voz na convenção BEREIA da ordem Robinson;
reconhece alternativas compactadas e mantém as análises. Descrições abreviadas,
possuidor versus objeto possuído, sincretismo neutro e pluperfeito não geram
contradições artificiais. Deponência e códigos não reconhecidos não são
convertidos por adivinhação. Uma ausência de voz no código é relatada como lacuna
técnica, sem preencher automaticamente o campo. As 80 ocorrências de códigos
fora do adaptador na primeira execução estão discriminadas, com Strong e índice,
no relatório completo; não são automaticamente erros.

```sh
python3 -B -m tools.audit.audit_morphology
python3 -B -m unittest tools.audit.test_audit_morphology -v
```

A leitura padrão é JSON estrito e recusa chaves duplicadas. Se a edição manual
tiver apenas vírgulas terminais, o modo explícito abaixo permite análise
provisória: desconsidera essas vírgulas somente em memória, registra linha,
coluna e offset de cada uma e não regrava nenhum byte do arquivo original.
Outros erros de sintaxe continuam fatais. Corrigir a sintaxe e executar novamente
é necessário antes de usar os relatórios como resultado de uma fonte válida.

```sh
python3 -B -m tools.audit.audit_morphology --tolerate-trailing-commas
```

Saídas em `reports/audit/morfologia/`: `auditoria.json`, `resumo.md`,
`erros-comprovados.json`, `pendencias.csv`, `formas-repetidas.json`,
`prioridades.json`, `caso-on.json` e `produtos.json`. A comparação dos produtos
informa derivados e índices desatualizados e aliases com índices deslocados,
sem reconstruí-los durante a auditoria. O CSV contém somente achados pendentes;
o inventário de homógrafos legítimos fica separado, sem sugerir sua eliminação.
Não são criadas pendências de parsing apenas por ambiguidade nominal com uma
ocorrência; erros internos independentes continuam sendo registrados.

Os relatórios usam hashes das fontes e do código, sem horários e sem cache, e
são determinísticos. As referências de perícopes repetidas são deduplicadas para
não contar a mesma ocorrência como provas independentes; cópias conflitantes
ficam sem atribuição de parsing. Caracteres invisíveis são inventariados como
possíveis marcadores históricos, nunca apagados ou tratados como identidade.
Esta auditoria não reconstrói todos os paradigmas gregos independentemente.
Correções e consolidações ficam para uma aplicação separada, com seus próprios
critérios e validação de índices.

## Aplicação separada dos casos morfológicos prioritários

A solicitação de tratar os casos prioritários autoriza o manifesto
`tools/audit/approvals/morfologia-prioritarios.json`. Ele fixa os bytes da fonte
antes/depois, os seis registros revisados, as sete mudanças de campo e as provas
no TM, parsing e TBESG. A aplicação não exclui registros nem altera formas,
traduções, verbetes ou contagens. Em σπείροντος, o código conserva os gêneros
masculino/neutro já presentes na descrição ao corrigir o caso; não atribui uma
leitura neutra à ocorrência. O registro incompleto de ὢν recebe voz ativa sem
fundir seus metadados com os do outro registro da mesma forma.

```sh
python3 -B -m tools.audit.apply_morphology_priorities --apply
npm run dict:generate
npm run dict:review-state
python3 -B -m tools.audit.audit_tm --output reports/audit/aliases/base
python3 -B -m tools.audit.build_accent_aliases
python3 -B -m tools.audit.audit_morphology
python3 -B -m tools.audit.apply_morphology_priorities --check
npm run dict:check
npm run dict:review-state:check
python3 -B -m tools.audit.build_accent_aliases --check
python3 -B -m unittest tools.audit.test_apply_morphology_priorities tools.audit.test_audit_morphology -v
```

O aplicador é idempotente, recusa fonte ou evidências novas e substitui somente
as strings dos campos autorizados. A inversão em memória deve restaurar todos os
bytes anteriores, e nenhuma sequência de flexões é alterada. Os relatórios de
aplicação ficam em `reports/audit/morfologia-aplicacao/`; a auditoria atual e seu
CSV contêm apenas os achados que permanecem ativos. O sumário de prioridades é
derivado dos achados atuais, para não repetir como pendentes os casos resolvidos.

G1510/49 (`ὧν` + U+200B) permanece intocado. O backup histórico já misturava a
chave com marcador, `grego: ὢν` e análise genitiva verbal; os campos atuais não
permitem transportar contagens com segurança. O manifesto documenta a proposta
não aplicada de retirada isolada após decisão humana, conservando G1510/46–48,
o pronome G3739/18 e os demais marcadores históricos. O backup foi apenas lido.
Na execução após aplicação, o JSON é válido, os derivados e o índice coincidem
com a fonte, e os 170 aliases mantêm as mesmas referências contextuais.

## Revisão dos 48 alertas de voz remanescentes

O manifesto `approvals/vozes-48.json` documenta todos os 48 alertas da rodada
anterior. A aplicação em `apply_missing_voice.py` completa somente a voz em
`abrev_morf` e `morfologia` de 47 registros (94 campos): 38 ativos e nove futuros
médios de εἰμί/πάρειμι. Mantém integralmente os demais traços e todos os demais
campos. Reutiliza o aplicador de intervalos de strings, sem reserializar a fonte.

G1507/0 é um registro genérico com código `V`, descrição `Verbo`, contagem vazia
e sem ocorrência literal/NFC no TM. Não recebeu análise inventada: o auditor
passa a contá-lo separadamente como genérico, em lugar de tratá-lo como omissão
de voz numa análise flexional. O registro e sua limitação permanecem visíveis.

As fontes gramaticais consultadas estão no manifesto e no relatório, com URLs e
uso da evidência: Robinson PARSING.COD, Ancient Greek for Everyone e LSJ. Robinson
D é média deponente; o adaptador contextual só a compara como média nos futuros
de G1510/G3918. Não altera etiquetas originais, não estende a equivalência a
outros lemas nem a O/N, e não deduz voz pela tradução portuguesa. Sete registros
sem parsing alinhado usam o paradigma e a identidade lexical: suas ocorrências
continuam sem atribuição auxiliar. Contagens e grafias foram preservadas.

```sh
python3 -B -m tools.audit.apply_missing_voice --apply
npm run dict:generate
npm run dict:review-state
python3 -B -m tools.audit.audit_tm --output reports/audit/aliases/base
python3 -B -m tools.audit.build_accent_aliases
python3 -B -m tools.audit.audit_tm --output reports/audit/aliases/atual
python3 -B -m tools.audit.build_accent_aliases --inventory reports/audit/aliases/atual/inventario.json --check
python3 -B -m tools.audit.audit_morphology
python3 -B -m tools.audit.apply_missing_voice --check
npm run dict:check
npm run dict:review-state:check
python3 -B -m unittest tools.audit.test_apply_missing_voice tools.audit.test_apply_morphology_priorities tools.audit.test_audit_morphology -v
```

Os relatórios de aplicação ficam em `reports/audit/vozes-48/`. Não se reescrevem
manifestos históricos para corresponder ao léxico novo: cada aplicação aceita
somente seus hashes antes/depois. Os testes do lote prioritário usam snapshots
como fixtures quando há revisões posteriores, sem enfraquecer essas verificações
de execução nem alterar os hashes históricos.

Na revalidação desta rodada, todos os 170 aliases anteriores foram preservados
integralmente. A melhoria dos campos técnicos habilitou sete aliases com prova
contextual, somando 195 tokens validados: total de 177 aliases e 13.287 tokens.
A equivalência não foi estendida a ocorrências sem prova. O resultado da auditoria
morfológica tem zero alertas de código sem voz; permanecem 14 divergências entre
código e descrição e 856 alertas de revisão manual, incluindo problemas alheios
a esta aplicação. Não foram removidos os registros de homógrafos ou o marcador
G1510/49.
