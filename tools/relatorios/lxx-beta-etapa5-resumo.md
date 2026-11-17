# LXX beta — etapa 5: propostas AncientBible aprovadas

Aplicação autorizada pela instrução do usuário: “poe aplicar tudo”.
O arquivo de propostas e seu hash foram preservados no registro de aprovação.

- Aplicados os 44 pares aprovados, correspondentes a 41 lemas e 112 ocorrências.
- 69 grupos de forma/lema/análise/classe receberam tradução.
- As 73.557 ocorrências anteriormente traduzidas foram preservadas integralmente.
- O suplemento cobre agora 73.669 ocorrências; restam 934 sem tradução.
- Textos gregos, léxico principal, concordância inglesa e propostas originais
  foram preservados. Não foram criados números ou links Strong.

## Tratamento das alternativas e análises

- ἄπειμι mantém as alternativas “estar ausente / ir”, flexionadas conforme a
  análise disponível.
- σύνειμι mantém “estar com / reunir”, sem escolher automaticamente uma delas.
- κραταιός mantém “poderoso / vigorosamente”; sua ocorrência está classificada
  como verbal na fonte e não admite flexão verbal dessas bases.
- Para διορίζοντα, cuja análise não informa tempo/voz, foi exibida a base
  “determinar”.
- Para ἐτρύφησαν, classificado como verbo, foi exibida “autoindulgência”,
  sem criar um infinitivo que não estava nas propostas aprovadas.

Essas três ocorrências recebem apenas a glosa lexical aprovada. Isso preenche
a lacuna de apresentação, mas não resolve a incompatibilidade ou insuficiência
da análise original. As ressalvas permanecem na evidência de aplicação.

As adaptações gramaticais do português foram registradas explicitamente:
“verdadeiramente”, “profanamente”, “diferentemente”, “inteligivelmente” e
“fielmente” para advérbios; “benevolentes” para o adjetivo; “cortesãos do templo”
para o masculino plural. O comparativo é expresso por “mais”. A análise
`futperf` foi traduzida como futuro perfeito, preservando alternativas de voz.
Não houve correção nem substituição das formas gregas.

## Casos anteriormente INCERTO

A aprovação abrangeu 33 ocorrências de 10 lemas que constavam como INCERTO no
cadastro de bases. Sua aplicação foi liberada somente por decisões explícitas
vinculadas ao hash das propostas aprovadas. O cadastro TBESG e suas ressalvas
não foram alterados, nem o bloqueio geral removido. A carga rejeita liberações
sem aprovação correspondente ou candidatos que não pertençam ao lema.

Glosas como “curar”, “cortesãs do templo”, “sátiro”, “unicórnio”,
“pastel-dos-tintureiros” e a correspondência ε → “ou” são as propostas aprovadas;
a aplicação não equivale a validação lexical/contextual. As fontes, bases
originais e modos de flexão ou fallback constam no registro para revisão futura.

## Artefatos

- `tools/lxx/reviewed_step5.json`: decisões por forma, evidências, aprovação
  e restrição ao conjunto de referências revisado.
- `tools/relatorios/lxx-beta-etapa5.json`: mudanças por grupo.
- `tools/relatorios/lxx-ancientbible-en-aplicacao.json`: estado de aplicação
  de cada um dos 44 pares do JSON de revisão.
- `tools/relatorios/lxx-beta-pendencias.csv`: somente pendências não aplicadas.

## Reprodução

```sh
python3 -B tools/lxx/prepare_ancientbible_application.py --instruction 'poe aplicar tudo'
python3 -B tools/lxx/generate_beta.py ../bibliaaberta/lxx/lxx_morph --audit tools/relatorios/lxx-tbesg-cobertura-etapa4.json --bases tools/lxx/tbesg_bases_pt.json --aliases tools/lxx/tbesg_aliases_pt.json --stage 5 --reviewed tools/lxx/reviewed_step5.json
```

## Validação

- 17 testes Python e 2 testes Node aprovados.
- Regeneração idempotente; todas as traduções anteriores preservadas.
- `dict:check`, `dict:review-state` e `dict:review-state:check` aprovados.
- Conferidos os hashes das fontes, do léxico, dos dicionários derivados e dos
  relatórios históricos, além da preservação das alterações prévias do usuário.

O primeiro build identificou um erro preexistente no filtro `addZeros`, que
recebia `value` mas referenciava a variável inexistente `valor`. A referência
foi corrigida para `value` em `.eleventy.js`, preservando a alteração do usuário
nos links da concordância.

Build final aprovado com saída 0: 1.422 arquivos em 105,84 segundos. Foram
conferidos no HTML κεκράξομαι → “terei clamado” (Hc 1), ἀποσυνάξει → “curará”
(2Rs 5) e συνέστω → “esteja com / reúna” (Pv 5), com âncoras Strong vazias.
O filtro `addZeros` também foi conferido nas URLs produzidas para o NT.
