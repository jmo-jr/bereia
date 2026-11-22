# Validação da triagem

- 19 testes da auditoria e da triagem passaram.
- Literal/NFC, caixa, iota subscrito, espíritos, trema e posição de acento têm regressões específicas.
- Homógrafos, inclusive análises com grafias canonicamente equivalentes, são preservados.
- Consulta estrita testada sem fallback por caixa, espaços ou remoção de marcas.
- Relatórios reproduzidos byte a byte; inventários desatualizados são recusados.
- Hashes das fontes originais e dos contextos do piloto conferidos após os testes.
- `git diff --check` passou.
- A suíte existente continua com 4 aprovados e 5 falhas, diagnosticadas separadamente.
- A fonte Strong histórica foi localizada no Git com SHA256 idêntico ao baseline; nenhuma cópia foi gravada ou restaurada.
- Nenhum dicionário, TM, tradução, consulta em produção, exceção, teste histórico ou baseline alterado.
- Glosas do piloto aprovadas pelo usuário e registradas em decisions.json; inclusão ainda não aplicada. Nenhum commit criado.
