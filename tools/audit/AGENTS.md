# Agente de auditoria BEREIA

Siga o AGENTS.md da raiz. Nesta etapa, opere exclusivamente em leitura sobre
TM, dicionários, traduções, índices, exceções e fontes auxiliares. Nem mesmo
inconsistências técnicas autorizam alterações nos dados durante a auditoria.

## Aplicação do piloto aprovada pelo usuário

O usuário aprovou as glosas de `ἀρχῇ` e solicitou avançar para sua inclusão.
Essa aplicação é distinta da execução da auditoria: permite incluir somente a
nova flexão no Strong literal 746, regenerar os derivados, atualizar o estado
linguístico e corrigir a consulta do piloto. Preserve todas as flexões anteriores,
inclusive `ἀρχή`, e registre as referências e o resultado da aplicação. Os scripts
de auditoria continuam somente leitura. Não estenda a aprovação aos demais casos.

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
- Durante a execução dos scripts de auditoria, não execute geradores que escrevem
  dados. A aplicação aprovada acima segue o fluxo próprio da raiz. Não crie
  backups e não faça commit.
