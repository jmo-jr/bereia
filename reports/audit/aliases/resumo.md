# Aliases agudo/grave — implementação na develop

Lista positiva: src/_data/nt/greek_accent_aliases.json.

- 355 grafias examinadas; 170 pares com equivalência contextual validada.
- 13.092 ocorrências atendidas, em 13.076 referências distintas.
- 10.908 ocorrências ainda pendentes. Todas as 355 grafias têm alguma pendência; 185 não têm alias ativo.
- As diferenças entre referências e tokens decorrem das referências repetidas na estrutura de perícopes; o TM não foi deduplicado nem alterado.

O registro autoriza somente a troca final agudo/grave nas referências NT comprovadas. Conserva todos os demais sinais. Strong, flexão e assinatura morfológica do destino são validados; cada referência foi novamente conferida diretamente nos JSONs e CSVs, com alinhamento do versículo inteiro. As exceções de interrogativos e elisão ficam fora da regra.

A consulta prioriza literal/NFC e caixa. Nos casos controlados sem prova, não utiliza o fallback sem diacríticos. Mudanças nas fontes invalidam os aliases do livro; alterações na identidade morfológica do destino bloqueiam a equivalência. Glosas e contagens aprovadas da entrada canônica são reutilizadas sem duplicação de registros.

A grafia do TM é mantida na exibição. O painel recebe somente o destino validado e identifica a forma de referência. As contagens da grafia original ficam separadas das contagens da entrada de referência.

## Validação

- 65 testes direcionados passaram: 44 Python e 21 JavaScript.
- O loader real do NT foi executado com o log isolado: todos os 140.258 tokens conservaram suas grafias; foram confirmadas 13.092 associações validadas e 10.908 pendentes no lote.
- Reconstrução a partir de auditoria com aliases ativos produziu o mesmo registro, verificada com --check.
- dict:check e dict:review-state:check passaram. O estado linguístico do dicionário permaneceu intacto.
- Dicionário, índices gerados, TM, LXX, traduções, backups e baseline não foram alterados. As 255 inclusões anteriores foram preservadas. Sem commit.

## Arquivos

- equivalencias.md: pares e referências permitidas.
- validacao.json: métricas e pendências detalhadas.
- pendencias.csv: somente ocorrências não validadas, agrupadas por grafia.
- atual/inventario.json: auditoria com consultas contextuais por ocorrência.
- integracao-nt.json: prova do loader completo com preservação das grafias.

Os 1.069 casos sem correspondência literal/NFC/caixa continuam sendo uma métrica distinta: os aliases dão cobertura parcial a 170 dessas grafias, sem declarar resolvidas suas demais ocorrências.
