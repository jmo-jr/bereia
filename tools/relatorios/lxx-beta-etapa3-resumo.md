# LXX beta — etapa 3

Aplicadas 11 correspondências explícitas de lemas da fonte com verbetes TBESG.
São escolhas editoriais para a beta, sem correção do texto grego original.

- 319 ocorrências adicionais preenchidas (68 grupos de forma/análise).
- 72.844 ocorrências anteriormente preenchidas preservadas integralmente.
- 73.163 ocorrências cobertas pelo suplemento; 1.440 ainda sem tradução.
- Dicionário principal, originais e livros gregos preservados.
- Identificadores TBESG são procedência interna; não geram links Strong.

As evidências e bases estão em `tools/lxx/tbesg_aliases_pt.json`; as referências
e traduções aplicadas, em `tools/relatorios/lxx-beta-etapa3.json`.

## Pendências

- Sem base portuguesa adequada: 1366 ocorrências.
- Análise original não reconhecida; flexão não inferida: 17 ocorrências.
- Base não reconhecida como infinitivo português: 16 ocorrências.
- Verbete INCERTO no cadastro de bases; aplicação automática bloqueada: 39 ocorrências.
- Análise verbal incompleta: 2 ocorrências.

Gentílicos, ambiguidades e remissões que exigem interpretação adicional continuam pendentes. A lista atual está em `lxx-beta-pendencias.csv`.

## Validação

- 10 testes Python e 2 testes Node aprovados.
- Regeneração idempotente; todas as entradas já preenchidas preservadas.
- `dict:check`, `dict:review-state` e `dict:review-state:check` aprovados.
- Build de produção concluído: 1.422 arquivos, saída 0.
