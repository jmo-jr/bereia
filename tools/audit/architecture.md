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
