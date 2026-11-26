# Consulta insensível a caixa — develop

Implementada a equivalência por minúsculas + NFC na consulta do NT, LXX, painel Strong e auditoria. A exibição preserva a grafia original do TM; nomes próprios não foram reescritos ou classificados automaticamente.

- 1.449 grafias, em 9.441 tokens, passaram a ter correspondência por caixa sem retirada de diacríticos.
- O lote histórico de 1.448 não contava um caso com espaço marginal presente também no dicionário; nenhum espaço foi retirado.
- Restam 1.069 grafias sem correspondência literal/NFC/caixa.
- Εὗρον e Οὐ preservam os múltiplos pares Strong/índice, mantendo a projeção de compatibilidade já existente para a mesma forma canônica e o mesmo Strong.
- Colisões entre formas canônicas ou Strong diferentes são bloqueadas, sem escolher o primeiro ou recorrer ao fallback legado.
- 51 testes direcionados passaram: 37 Python e 14 JavaScript.
- dict:check, dict:review-state:check e git diff --check passaram.
- Dicionários, índices gerados, TM/LXX, capítulos traduzidos e estado linguístico não foram alterados. Nenhuma exceção removida. Sem commit.

A chave não usa remoção de marcas nem casefold que expanda o iota subscrito: ἀρχῇ continua distinta de ἀρχή. O fallback legado para outras lacunas permanece temporariamente ativo e continua pendente de substituição.

Implementação realizada no worktree develop em /private/tmp/bereia-original-tooltip, preservando o outro checkout. O inventário completo e os hashes estão em tm/inventario.json.
