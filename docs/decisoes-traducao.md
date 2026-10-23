# BEREIA — Registro de decisões de tradução

**Versão inicial:** 23/10/2026  
**Referência:** `docs/protocolo-traducao.md`.

## 1. Finalidade e estados

Este documento registra decisões que possam afetar a tradução de outras passagens. Não é um dicionário paralelo nem substitui `src/_data/dict_flex_nt-lxx_greek-pt.json`.

**Estados:**
- **Consolidada:** escolha explicitamente confirmada pelo responsável pelo projeto.
- **Preferência observada:** escolha identificada em capítulos existentes, ainda não formalizada como regra geral.
- **Contextual:** solução adequada a determinado contexto, sem pretensão de uniformidade absoluta.
- **Em avaliação:** opção que merece revisão antes de se tornar padrão.

A aprovação geral da redação de Mateus 8 **não transforma automaticamente cada escolha lexical em regra definitiva**.

## 2. Decisões e preferências iniciais

| Termo / construção grega | Tradução ou orientação | Estado | Referência / observação |
|---|---|---|---|
| βαπτίζω | **imergir** | Preferência observada | Mt 3; alternativa semântica à transliteração “batizar”. Conferir uso figurado conforme contexto. |
| διάβολος | **acusador** | Preferência observada | Mt 4; conferir a função do termo em cada ocorrência. |
| πειράζω | **testar** | Contextual | Mt 4:1; “tentar” pode ser necessário em outros contextos. |
| προσκυνέω | **prostrar-se / reverenciar** | Contextual | Mt 2 e Mt 8:2; avaliar gesto físico e sentido de reverência. |
| παῖς | **servo / criança** | Contextual | Mt 8:6, 8, 13; depende da relação indicada pelo contexto. |
| δοῦλος | **escravo** | Preferência observada | Mt 8:9; distinguir de παῖς quando possível. |
| σκότος | **escuridão** | Preferência observada | Mt 8:12; conferir construções como “escuridão exterior”. |
| σεισμός | **agitação** | Contextual | Mt 8:24, no mar; em outros contextos, “terremoto” pode ser mais apropriado. |
| ἐπιούσιος | **necessário** | Em avaliação | Mt 6:11; vocábulo de interpretação discutida, requer nota lexical. |
| γεργεσηνῶν | **gergesenos** | Contextual / textual | Mt 8:28, conforme a forma do TM consultado; preservar a leitura adotada, sem harmonizar com outros testemunhos. |
| τί ἡμῖν καὶ σοί | **O que há entre nós e você?** | Contextual | Mt 8:29; tradução relativamente literal de expressão idiomática. |

## 3. Convenções editoriais observadas

| Convenção | Orientação | Estado |
|---|---|---|
| Particípios | Preservar, quando adequado, com “tendo...” ou gerúndio. | Consolidada no protocolo |
| Pronomes de tratamento | Preferir “você/vocês” quando coerente com o contexto e o estilo existente. | Preferência observada |
| Palavras explicativas | Usar `[colchetes]` quando não houver equivalente explícito no grego e a inserção for relevante. | Consolidada no protocolo |
| Repetição lexical | Evitar sinônimos puramente estilísticos para o mesmo lema. | Consolidada no protocolo |
| Polissemia | Admitir equivalências diferentes quando exigidas pelo contexto. | Consolidada no protocolo |
| Topônimos e nomes | Seguir a leitura do Texto Majoritário adotado no projeto. | Consolidada no protocolo |
| Tradução de expressões idiomáticas | Preservar o literal quando inteligível; adaptar minimamente quando necessário. | Consolidada no protocolo |

## 4. Registro de novas decisões

Para cada decisão relevante, acrescentar uma entrada neste modelo:

```markdown
### [Lema grego] — [tradução preferencial]
- **Estado:** consolidada / preferência observada / contextual / em avaliação
- **Referências:** livro capítulo:versículo
- **Forma(s) e morfologia:** ...
- **Equivalência principal no dicionário:** ...
- **Tradução adotada:** ...
- **Motivo:** ...
- **Exceções ou outras acepções:** ...
- **Aprovação editorial:** pendente / confirmada em AAAA-MM-DD
```

Registrar apenas decisões com potencial de reaproveitamento ou relevância interpretativa. Correções simples de pontuação e preferência estilística local não exigem nova entrada.

## 5. Pendências para revisão futura

1. Conferir as escolhas iniciais com os respectivos registros do dicionário definitivo antes de classificá-las como equivalências lexicais consolidadas.
2. Definir, quando necessário, o tratamento de vocábulos teológicos recorrentes e de traduções tradicionais por transliteração.
3. Registrar mudanças editoriais futuras que afetem múltiplos capítulos.

**Nota sobre Mateus 8:** a tradução experimental foi aprovada como padrão geral de estilo, com liberdade para ajustes pontuais posteriores. O arquivo `8.liquid` preexistente não integra a fonte dessa aprovação.
