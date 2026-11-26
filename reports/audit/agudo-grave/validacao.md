# Validação do lote agudo/grave

- 11 testes novos passaram.
- Relatórios de duas execuções com as mesmas fontes foram idênticos byte a byte.
- Comparação de códigos cobre ordem de gênero/número, voz, pessoa, tempo e prefixos 2A/2R; códigos incompletos ou não suportados não se tornam correspondências positivas.
- Descrição morfológica é conferida contra o código; perfeito não é confundido com imperfeito ou mais-que-perfeito.
- Referências não alinhadas não recebem parsing por analogia.
- Candidatos adicionais, Strong divergente e análises incompatíveis bloqueiam a minuta.
- Sincretismo neutro nominativo/acusativo não gera pendência por si só.
- Contagens e referências LXX usam literal/NFC; não recebem Strong inferido nem vínculos do candidato.
- Hashes das fontes foram conferidos novamente ao final, sem alteração do dicionário, TM, painel, consulta ou estado linguístico neste lote.
- Todas as 636 formas permanecem pendentes: 255 SUGERIR e 381 INCERTO. Nenhuma inclusão aplicada, nenhum backup ou commit criado.
- git diff --check passou.
