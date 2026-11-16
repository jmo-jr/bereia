# BEREIA - Bíblia de Estudo com Recursos Exegéticos e Interlinear Analítico 

## https://bereia.app.br

Baseado no **Texto Majoritário**, com destaque para a *Família 35*

## Projeto baseado em 11ty

**Compile:** `eleventy`

**Run:** `npx @11ty/eleventy`

**Serve:** `npx @11ty/eleventy --serve`

## Dicionário grego

A fonte principal é `src/_data/dict_lex_nt-lxx_greek-pt.json`, organizada por
Strong e lema. O dicionário de flexões e o índice de formas são gerados
automaticamente pelo Eleventy. Para gerar e verificar manualmente, use
`npm run dict:generate`, `npm run dict:check` e `npm test`.
Consulte [a arquitetura e o fluxo de atualização](docs/arquitetura-dicionario.md).

## Detalhes sobre o NT de Estudo

- Tradução priorizando a literalidade, secundariamente a legibilidade
- Coerência de tradução de palavras sempre que possível
- Comentários tooltip com tradução alternativa (dinâmica), notas, etc.
- Palavras-chave do NT (grego e detalhe sobre a palavra) tooltip
- Parágrafos baseados na NVI
- Negrito nas referências ao AT, tanto diretas, quanto indiretas (consultar Bíbllia Judaica Comentada)
- Palavras de Jesus em vermelho 

## Ferramentas e repositórios utilizados

Tooltipster: https://calebjacob.github.io/tooltipster
Texto da Septuaginta (Rahlfs): https://github.com/OpenScriptorium/lxx-morph
Texto Majoritário (Bizantino): https://github.com/byztxt/byzantine-majority-text
https://biblehub.com/
https://septuaginta.online/