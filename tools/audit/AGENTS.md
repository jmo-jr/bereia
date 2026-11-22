# Agente de auditoria BEREIA

Siga o AGENTS.md da raiz. Nesta etapa, opere exclusivamente em leitura sobre
TM, dicionários, traduções, índices, exceções e fontes auxiliares. Nem mesmo
inconsistências técnicas autorizam alterações nos dados durante a auditoria.

## Política de caixa autorizada pelo usuário

Maiúsculas/minúsculas podem ser ignoradas na chave de consulta, mantendo NFC e
todos os diacríticos. Preserve a capitalização original no TM, nos registros e
na exibição; não determine automaticamente quais palavras são nomes próprios.
Correspondências por caixa não exigem duplicar flexões no dicionário. Preserve
todas as análises e não selecione a primeira em colisões entre formas canônicas
diferentes ou entre Strong diferentes. Para uma só forma canônica e um só Strong
com múltiplas análises, mantenha a projeção
de compatibilidade já usada pela consulta literal e exponha todos os pares
Strong/índice, sem fundir ou excluir registros. Não use casefold
que expanda o iota subscrito nem retire marcas para resolver essas colisões.

## Equivalências de acento autorizadas pelo usuário

O usuário autorizou executar a estratégia de aliases agudo/grave validados.
Permite-se criar e atualizar a lista positiva separada do dicionário e usá-la na
consulta, mantendo os registros e o TM intactos. Cada alias deve conservar todos
os demais sinais e vincular destino Strong/índice a referências com parsing
alinhado e compatível. Evidência parcial só autoriza as referências comprovadas;
não estenda a equivalência às demais ocorrências. As origens deste lote sem prova
ficam pendentes e não podem atravessar o fallback legado sem marcas. Não funda
nem apague as 255 inclusões anteriores. Interrogativos τίς/τί, deslocamentos de
acento, circunflexos, espíritos, elisão e iota subscrito não entram nessa regra.

## Aplicação do piloto aprovada pelo usuário

O usuário aprovou as glosas de `ἀρχῇ` e solicitou avançar para sua inclusão.
Essa aplicação é distinta da execução da auditoria: permite incluir somente a
nova flexão no Strong literal 746, regenerar os derivados, atualizar o estado
linguístico e corrigir a consulta do piloto. Preserve todas as flexões anteriores,
inclusive `ἀρχή`, e registre as referências e o resultado da aplicação. Os scripts
de auditoria continuam somente leitura. Não estenda a aprovação aos demais casos.

## Aplicação do lote agudo/grave aprovada pelo usuário

O usuário aprovou explicitamente as 255 minutas SUGERIR do relatório
`reports/audit/agudo-grave/revisao.json`. É permitido aplicar somente essas
minutas, acrescentando-as ao final das flexões dos respectivos Strong literais,
regenerar os derivados e atualizar o estado linguístico. Registre a aprovação
vinculada ao hash do relatório. Preserve todos os registros e índices anteriores;
os 381 INCERTO não estão aprovados. A aplicação deve validar as fontes, preservar
a formatação e recusar conflitos. Não faça commit nem crie backups.

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
