# Tarefa: revisão assistida do dicionário grego-português

## Arquivo-alvo

`src/_data/dict_lex_nt-lxx_greek-pt.json`

Esta é a fonte editável. `dict_flex_nt-lxx_greek-pt.json` e
`dict_form_index_nt-lxx_greek-pt.json` são derivados: não os edite
diretamente. Siga `docs/arquitetura-dicionario.md` para geração e validação.

## Unidade, sequência e retomada

- Cada registro no array `flexoes` conta como uma entrada. Um lote de 100
  significa 100 flexões, não 100 grupos Strong, lemas ou formas distintas.
- Siga a ordem textual dos grupos na fonte e, dentro de cada grupo, a ordem
  do array `flexoes`. Não reordene grupos nem flexões. Não use apenas
  `Object.keys` de um JSON comum para recuperar a ordem textual: JavaScript
  enumera chaves inteiras antes de identificadores com espaços.
- Preserve o Strong literal, incluindo espaços, sem aparar, consolidar ou
  mover registros automaticamente entre grupos.
- Identifique cada registro por Strong literal, índice em `flexoes`
  (base zero), `grego` e análise morfológica. A linha é apenas referência
  auxiliar; confirme a identidade antes de retomar.
- A retomada após a migração começa depois de `κατασκευάζεται`, no Strong
  `2680`, `flexoes[0]` (linha 123071 à época da indicação). Não recomece do
  topo automaticamente. Registros que migraram para antes desse ponto
  poderão ser abrangidos por uma segunda passagem solicitada pelo usuário.
- Preserve a multiplicidade de homógrafos e análises. Consulte o léxico e
  o índice, não apenas a primeira análise projetada no derivado.

## Escopo

A revisão de tradução concentra-se nos campos:

- `traducao`
- `pt`

Use o campo `morfologia` como contexto morfológico. Corrija também erros
técnicos objetivos comprovados, especialmente em `abrev_morf` e
`morfologia`, incluindo indicações de voz ausentes.

Consulte `lema` e a `transliteracao` do grupo como referência lexical, mas
não os altere nesta revisão. A `transliteracao` de cada flexão é um campo
distinto e pode receber correções objetivas comprovadas.

O `verbete` do grupo é compartilhado. Não o altere sem verificar o alcance
em todas as flexões afetadas. Para correções restritas ao lote, edite o
`verbete` específico da flexão ou acrescente essa substituição quando o
grupo usar verbete comum, preservando a sequência dos campos fixos. Nos
grupos com `verbetes`, mantenha a variante também nesse array, sem apagar
variantes antigas ou alterar outras flexões automaticamente.

## Regras da revisão

- Corrija erros objetivos de português brasileiro:
  ortografia, acentuação, concordância, regência e pontuação.
- Verifique se a tradução é compatível com a morfologia informada.
- Preserve o caráter interlinear e literal.
- Não altere a forma grega ou campos técnicos sem erro objetivo comprovado.
- Mantenha código, descrição morfológica e tradução coerentes. Não renomeie,
  funda ou exclua entradas automaticamente.
- Não faça escolha lexical exegética.
- Preserve diacríticos gregos, UTF-8, indentação e ordem das chaves.

### Suspeitas de correção gráfica

Sempre que houver suspeita de erro gráfico na forma grega, especialmente
em acentos, espíritos ou iota subscrito, consulte obrigatoriamente os
JSONs do Texto Majoritário em `src/interlinear/nt` antes de propor ou
aplicar a correção. Confira a grafia nas ocorrências pertinentes e
registre as referências bíblicas e os arquivos consultados na análise.

Não conclua que há erro apenas porque uma fonte externa usa outra grafia.
Se a forma não for localizada ou a comparação não resolver a dúvida,
classifique como `INCERTO` e preserve o original. A consulta não autoriza
renomear, fundir ou excluir chaves automaticamente.

## Classificação obrigatória

| Classificação | Significado |
|---|---|
| `CORRIGIR` | Erro objetivo de português ou incongruência morfológica clara |
| `SUGERIR` | Melhoria de naturalidade, sem erro evidente |
| `INCERTO` | Depende de contexto bíblico, referente ou decisão exegética |
| `OK` | Não alterar |

## Procedimento

1. Processe somente o intervalo de entradas informado no chat.
2. Apresente uma lista, nunca tabela, com:
   `id_item | chave_json | campo | valor atual | valor sugerido | motivo | classificação`
3. Aplique automaticamente `CORRIGIR`, correções técnicas comprovadas e as
   combinações de análises autorizadas na seção abaixo. Essas alterações
   já estão aprovadas; não solicite confirmação a cada lote.
4. Para `SUGERIR` e demais `INCERTO`, aguarde aprovação explícita.
5. Antes de sobrescrever arquivos, crie backup. Preserve UTF-8, formatação,
   ordem das chaves e alterações manuais; valide o JSON e o diff.
6. Gere ou atualize:
   `tools/relatorio_revisao_codex.csv`
   com as colunas:
   `chave_json, campo, abrev_morf, valor_atual, valor_sugerido, categoria, motivo, classificacao, aprovado`, 
   Preserve essas colunas; use `grego` em `chave_json` e registre no motivo
   o Strong literal e o índice `flexoes[n]`, pois a forma pode ter múltiplos
   registros. Inclua apenas itens não aplicados que continuam pendentes. Não
   acrescente casos ignorados pelas regras abaixo. Preserve o histórico;
   não faça limpeza retroativa sem solicitação.
7. Não processe o arquivo inteiro em uma única execução.
8. Após editar a fonte, execute `npm run dict:generate`,
   `npm run dict:check` e `npm test`. Confira também o diff dos derivados.
   Preserve backups e hashes históricos. Documente separadamente as
   alterações linguísticas autorizadas; não atualize referências de
   migração apenas para fazer testes passarem. Informe falhas de auditoria,
   distinguindo as preexistentes das introduzidas pelo lote.
9. Não faça commit. Informe a última forma, Strong literal, índice em
   `flexoes` e a linha alcançada na fonte lexical.

## Aplicação automática nos casos antes classificados como INCERTO

### Primeira pessoa singular e terceira pessoa plural

Quando a mesma forma admitir `1S/3P`, combine automaticamente as duas
análises, mesmo que haja apenas uma ocorrência. Siga os padrões de
`ἔφερον` e `ἔφαγον`, preservando flexão e alternativas lexicais:

- `pt`: forma compacta, como `trazia(m)` ou `comi(eram)`;
- `traducao`: explicite ambas, como
  `eu trazia, carregava; eles(as) traziam, carregavam`;
- `abrev_morf`: combine as pessoas, como `V-IIA-1S/3P`;
- `morfologia`: descreva primeira pessoa singular e terceira pessoa plural.

Use o padrão combinado dos exemplos, não uma inconsistência acidental:
`ele(a)` não representa primeira pessoa singular nem terceira plural.
Não substitua a combinação por uma escolha contextual exclusiva.

### Mais de um modo

- Com `ocorrencias` igual a 1, ignore somente a ambiguidade de modo.
- Com `ocorrencias` maior que 1, combine automaticamente os modos nos
  quatro campos, seguindo `εὐχαριστῶ`:
  `pt: agradeço(a)`;
  `traducao: eu dou graças, agradeço; que eu agradeça`;
  `abrev_morf: V-PI/SA-1S`;
  `morfologia: Verbo - Presente Indicativo/Subjuntivo Ativa - 1ª Pessoa Singular`.
- Adapte a forma compacta e o código aos modos efetivamente possíveis;
  não aplique uma substituição textual genérica a outros paradigmas.

### Ambiguidades nominais

- Ignore diferenças de caso que não mudem significativamente o português,
  como nominativo/acusativo com a mesma tradução, independentemente da
  contagem de ocorrências.
- Ignore outras ambiguidades nominais de caso, gênero ou número quando
  `ocorrencias` for igual a 1. Isso não revoga a regra verbal `1S/3P`.
- Para outros casos com mais de uma ocorrência e impacto real na tradução,
  mantenha `INCERTO` e encaminhe para revisão humana.

### Contagem e significado de ignorar

Use `ocorrencias`, a contagem do NT. Não some `ocorrencias_lxx`. Valores
ausentes, vazios ou inválidos não devem ser presumidos como 1; se a decisão
depender da contagem, registre a informação insuficiente para revisão.

Ignorar uma ambiguidade significa preservar os valores atuais e não criar
item na lista nem linha no CSV apenas por essa possibilidade. Continue
corrigindo erros objetivos independentes, mesmo nas entradas com uma só
ocorrência. Não remova pendências históricas sem solicitação.

### Campos técnicos

Corrija automaticamente erros técnicos quando a forma e a evidência
permitirem uma conclusão objetiva. Por exemplo, `εὐχαριστεῖ` é presente
indicativo ativo, terceira pessoa singular, não infinitivo. Acrescente
indicações de voz ausentes em código e descrição quando identificáveis.

Siga as abreviações já usadas no arquivo, inclusive as combinações de
análises. Não confunda voz grega com a voz necessária na tradução
portuguesa de verbos depoentes. Se a correção não for demonstrável, mantenha
`INCERTO`; escolhas lexicais e exegéticas continuam sem autorização automática.
