# BEREIA — Protocolo de tradução do Novo Testamento

**Versão:** 1.0 — 23/10/2026  
**Estado:** método aprovado em caráter operacional; sujeito a refinamentos editoriais.  
**Projeto:** Bíblia Aberta / BEREIA.

## 1. Objetivo

Produzir uma tradução brasileira do Novo Testamento predominantemente literal, legível e lexicalmente consistente, permitindo ao leitor reconhecer, tanto quanto possível, a recorrência dos mesmos termos gregos em diferentes passagens e livros.

A tradução não é uma transcrição palavra por palavra do interlinear: é um texto contínuo em português, construído a partir dele, com intervenções sintáticas tão limitadas quanto a compreensão exigir.

## 2. Fontes e precedência

1. **Texto grego:** Texto Majoritário (TM) adotado no interlinear BEREIA, preservando suas variantes e escolhas textuais. O material em `src/interlinear/nt/` e `tools/tm_with-parsing/` auxilia a conferência das formas e da análise morfológica.
2. **Dicionário definitivo:** `src/_data/dict_flex_nt-lxx_greek-pt.json`. Consultar a tradução associada a cada forma, o lema, a morfologia e as demais informações disponíveis.
3. **Referência editorial:** Mateus 1–8, com Mateus 8 como primeiro capítulo experimental aprovado. Os capítulos existentes servem como referência de estilo, não como autoridade superior ao texto grego.
4. **Decisões editoriais posteriores:** correções expressamente aprovadas pelo responsável pelo projeto têm precedência sobre preferências anteriores, sem alterar o texto grego.

**Nota:** o arquivo `src/biblia/nt/mateus/8.liquid` preexistente não foi utilizado como fonte para o primeiro teste de Mateus 8 e não deve ser tomado como versão aprovada desse teste.

## 3. Princípios de tradução

### 3.1. Correspondência lexical

- Adotar preferencialmente uma equivalência portuguesa estável para cada lema grego, respeitando a acepção efetivamente empregada.
- Evitar variações meramente estilísticas de tradução que escondam a repetição do mesmo termo.
- Preservar, quando viável, distinções entre lemas gregos diferentes; não forçar distinções artificiais se o português não as comportar.
- Não impor uma tradução única a termos polissêmicos: registrar as acepções contextuais justificadas.
- Usar o dicionário como referência principal, **não como substituto da análise sintática e semântica**.

### 3.2. Sintaxe e legibilidade

- Conservar a ordem e a estrutura do grego quando resultarem em português compreensível.
- Reorganizar constituintes, ajustar concordâncias e inserir elementos exigidos pela gramática portuguesa quando necessário.
- Evitar paráfrases, harmonizações, explicações doutrinárias e acréscimos interpretativos no texto principal.
- Manter o grau de explicitação do original sempre que possível: não resolver ambiguidades deliberadas sem necessidade.

### 3.3. Morfologia verbal

- Observar pessoa, número, tempo, modo, voz e aspecto, inclusive a distinção entre formas finitas e particípios.
- Preservar particípios por construções como “tendo feito”, gerúndios ou outras soluções adequadas quando isso favorecer a fidelidade.
- Não converter automaticamente aoristos em pretéritos perfeitos nem particípios em orações independentes sem avaliar o contexto.
- Manter o presente histórico quando compatível com a fluência e o estilo estabelecido.
- Não sacrificar o sentido temporal ou aspectual apenas para reproduzir uma estrutura formal do grego.

### 3.4. Expressões idiomáticas e figuras

- Preferir a expressão literal quando seu sentido for inteligível em português.
- Quando a literalidade gerar um sentido incorreto ou opaco, usar equivalência idiomática mínima e registrar a decisão se ela for relevante ou recorrente.
- Reservar traduções mais dinâmicas e explicações extensas para notas e comentários, quando previstos.

### 3.5. Acréscimos, notas e nomes

- Utilizar **[colchetes]** para palavras explicativas relevantes sem correspondência explícita no texto grego; não marcar automaticamente artigos ou conectivos exigidos pelo português.
- Preservar nomes próprios, topônimos e leituras características do TM; conferir formas controversas diretamente no texto-base.
- Usar terminologia religiosa segundo decisões lexicais documentadas, sem privilegiar automaticamente traduções tradicionais ou alternativas etimológicas.
- Não harmonizar relatos paralelos dos Evangelhos para produzir uma redação uniforme.
- Distinguir **notas textuais** (variantes/manuscritos), **notas lexicais** (vocabulário) e **comentários interpretativos**.

## 4. Consistência e exceções

Para cada decisão potencialmente recorrente:

1. Identificar a forma grega, o lema e, quando pertinente, o número Strong.
2. Conferir a tradução preferencial no dicionário definitivo.
3. Verificar a construção sintática e a acepção contextual.
4. Comparar ocorrências relevantes e traduções já aprovadas.
5. Manter a equivalência preferencial, salvo motivo linguístico identificável.
6. Registrar a exceção ou alteração consolidada em `docs/decisoes-traducao.md`.

**Homógrafos:** não pressupor que a remoção de diacríticos preserve uma análise única. Para formas ambíguas, verificar a grafia, o contexto e a morfologia antes de selecionar a tradução. Respeitar as exceções de normalização do projeto.

## 5. Formato de entrega

Cada capítulo será entregue como arquivo UTF-8 `N.txt` (por exemplo, `9.txt`), pronto para processamento pelo conversor existente. Estrutura:

```text
Título da primeira perícope (Mc 1:40-45; Lc 5:12-16)
1 Texto do primeiro versículo.
2 Texto do segundo versículo.

3 Texto do terceiro versículo.
--
Título da segunda perícope
4 Texto do quarto versículo.
```

Regras:

- Uma linha iniciada pelo número do versículo, seguida de espaço e do texto.
- Título de perícope antes dos versículos correspondentes; concordâncias opcionais entre parênteses.
- Uma linha em branco para separar parágrafos dentro da mesma perícope.
- Uma linha contendo apenas `--` para iniciar nova perícope.
- Numeração completa, contínua e sem duplicações.
- Marcação adicional (como `<rl>...</rl>`) somente quando necessária e suportada pelo conversor.
- Não alterar o conversor ou arquivos de publicação como parte da tradução, salvo pedido específico.

**Referências técnicas:** `SNIPPET-BIBLIA-USAGE.md` e `tools/biblech/gera_capitulos_html.py`.

## 6. Fluxo de trabalho por capítulo

1. **Extração:** identificar o capítulo e suas perícopes no material grego do TM.
2. **Conferência:** examinar formas, lemas e análises morfológicas; consultar o dicionário definitivo.
3. **Redação:** produzir o texto português contínuo, seguindo este protocolo.
4. **Controle lexical:** verificar termos recorrentes, construções ambíguas, variantes relevantes e exceções.
5. **Validação estrutural:** conferir total e sequência dos versículos, títulos, divisões e compatibilidade TXT.
6. **Entrega:** disponibilizar o TXT e destacar apenas as decisões que realmente exijam atenção editorial.
7. **Revisão:** incorporar as alterações pontuais solicitadas pelo responsável pelo projeto.
8. **Consolidação:** registrar decisões gerais reutilizáveis e identificar a versão como aprovada somente após confirmação.

## 7. Critérios de aceitação

- O capítulo corresponde integralmente ao TM adotado no projeto.
- Todos os versículos estão presentes, em ordem e sem duplicação.
- A tradução mantém literalidade e legibilidade próximas do padrão de Mateus 8.
- As escolhas lexicais foram conferidas com o dicionário definitivo; eventuais desvios têm justificativa contextual.
- O TXT respeita o formato do conversor.
- A aprovação editorial do responsável pelo projeto foi obtida antes de declarar a versão definitiva.

## 8. Governança editorial

O responsável pelo BEREIA define a redação final. Preferências estilísticas individuais podem motivar alterações pontuais sem que isso invalide o método. Mudanças com efeito em outras passagens devem ser registradas como decisões gerais; mudanças locais permanecem documentadas como exceções contextuais.

O protocolo poderá ser atualizado após novos capítulos, desde que se preserve o histórico das decisões e a consistência do conjunto.
