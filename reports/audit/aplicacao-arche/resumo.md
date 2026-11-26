# Aplicação do piloto ἀρχῇ

Aplicada a nova flexão no Strong literal 746, índice 6, após aprovação das glosas e solicitação para avançar.

- Grego: ἀρχῇ; transliteração: archē.
- Tradução: no princípio, ao principado.
- pt: no princípio.
- Morfologia: S-DFS — Substantivo - Dativo Feminino Singular.
- Ocorrências: 5 no TM; 22 na LXX, por igualdade literal/NFC.
- Todas as entradas anteriores preservadas, inclusive ἀρχή; índices anteriores preservados.

## Consulta e painel

O loader passou a priorizar chave literal e equivalência NFC. O fallback legado e todas as exceções existentes foram preservados. O painel seleciona apenas flexões literais/NFC e conserva suas múltiplas análises.

A comparação com a versão anterior identificou oito grafias com saída diferente, em 235 tokens: o piloto (cinco tokens) e sete formas já cobertas que eram encobertas por outra chave normalizada (230 tokens). Detalhes antes/depois em aplicacao.json.

## Validação

- 20 testes Python, 5 regressões JavaScript e 3 testes de comparação existentes passaram (28 no total).
- Derivados regenerados; dict:check passou.
- Estado linguístico atualizado explicitamente por npm run dict:review-state; verificação passou.
- Comparação byte a byte confirmou que o JSON fonte só recebeu o bloco da nova flexão, sem reformatar registros existentes.
- Baseline, backups e relatório histórico de migração preservados.
- TM e capítulos traduzidos não foram editados por esta aplicação. Nenhum commit criado.
- As cinco falhas históricas já diagnosticadas não foram corrigidas nem mascaradas nesta etapa.

## Pendências

A auditoria ainda registra 2.773 grafias sem entrada literal/NFC. O fallback legado não comprova identidade morfológica e continua pendente de substituição validada. A inclusão de ἀρχῇ foi removida da lista de propostas pendentes; sua decisão e aplicação continuam documentadas.
