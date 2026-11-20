# Agente de auditoria BEREIA

Siga o AGENTS.md da raiz. Nesta etapa, opere exclusivamente em leitura sobre
TM, dicionários, traduções, índices, exceções e fontes auxiliares. Nem mesmo
inconsistências técnicas autorizam alterações nos dados durante a auditoria.

- Grave código em tools/audit e relatórios/cache em reports/audit.
- Preserve grafias, referências, identificadores Strong literais e índices de
  flexão; nunca funda homógrafos ou selecione a primeira análise como verdade.
- Separe igualdade literal, equivalência NFC, caixa e candidatos sem diacríticos.
  Somente NFC é equivalência canônica; candidatos não comprovam identidade.
- Parsing auxiliar só fornece evidência contextual após alinhamento do versículo
  inteiro (mesma quantidade e sequência de palavras). Registre falhas e lacunas.
- Divergência entre fontes é pendência de revisão, não correção comprovada.
  Não automatize decisões lexicais, traduções ou consolidação de lemas/flexões.
- Relatórios devem ser determinísticos, versionados e conter hashes das fontes.
  Cache é descartável, validado por conteúdo e versão, sem alterar resultados.
- Teste diferenças de diacríticos, NFC, homógrafos, fontes divergentes e cache.
- Não execute geradores que escrevem dados, não crie backups e não faça commit.
