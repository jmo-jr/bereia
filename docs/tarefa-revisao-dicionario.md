# Tarefa: revisão assistida do dicionário grego-português

## Arquivo-alvo

`src/_data/dict_flex_nt-lxx_greek-pt.json`

## Escopo

Revise apenas os campos:

- `traducao`
- `pt`

Use o campo `morfologia` como contexto morfológico.

## Regras da revisão

- Corrija erros objetivos de português brasileiro:
  ortografia, acentuação, concordância, regência e pontuação.
- Verifique se a tradução é compatível com a morfologia informada.
- Preserve o caráter interlinear e literal.
- Não altere o grego nem campos técnicos.
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
3. Apresente uma lista com:
   `id_item | chave_json | campo | valor atual | valor sugerido | motivo | classificação`
4. Não aplique nenhuma alteração antes da aprovação explícita.
5. Após aprovação, aplique somente as alterações aprovadas.
6. Gere ou atualize:
   `tools/relatorio_revisao_codex.csv`
   com as colunas:
   `chave_json, campo, abrev_morf, valor_atual, valor_sugerido, categoria, motivo, classificacao, aprovado`
7. Não processe o arquivo inteiro em uma única execução.
