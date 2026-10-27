# Tarefa: revisão assistida do dicionário grego-português

## Arquivo-alvo

`src/_data/dict_flex_nt-lxx_greek-pt.json`

## Escopo

A revisão de tradução concentra-se nos campos:

- `traducao`
- `pt`

Use o campo `morfologia` como contexto morfológico. Corrija também erros
técnicos objetivos comprovados, especialmente em `abrev_morf` e
`morfologia`, incluindo indicações de voz ausentes.

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
   apenas dos itens que não foram aplicados e continuam pendentes. Não
   acrescente casos ignorados pelas regras abaixo. Preserve o histórico;
   não faça limpeza retroativa sem solicitação.
7. Não processe o arquivo inteiro em uma única execução.
8. Não faça commit. Informe a última entrada e a linha alcançada.

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
