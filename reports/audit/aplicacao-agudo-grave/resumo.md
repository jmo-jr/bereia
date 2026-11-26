# Aplicação aprovada — 255 flexões de agudo/grave

Aplicadas as 255 minutas aprovadas pelo usuário, em 188 grupos Strong. O manifesto durável está em tools/audit/approvals/agudo-grave-255.json, vinculado ao hash do relatório original.

- 255 novas flexões; todas as grafias e glosas foram aplicadas exatamente como nas minutas aprovadas.
- 672 tokens do TM passaram a ter correspondência literal com suas próprias entradas.
- Registros e índices anteriores preservados; a reversão em memória das inserções reproduz o SHA256 anterior do léxico.
- A projeção e o índice anteriores foram comparados com os atuais e permaneceram intactos para todas as formas antigas.
- A consulta real mudou somente para as 255 grafias aprovadas, em 672 tokens; nenhum token fora dessas grafias teve saída diferente.
- Derivados regenerados e estado linguístico atualizado por npm run dict:review-state.
- dict:check e dict:review-state:check passaram.
- 37 testes Python e 9 JavaScript passaram (46 no total).
- Reexecutar a aplicação não duplica registros nem escreve na fonte já aplicada.

## Pendências preservadas

O lote original mantém 381 INCERTO, sem aplicação. Todos constam de pendencias.json e pendencias.csv; o CSV não contém itens aplicados. Vinte e seis desses casos agora aparecem como diferenças apenas de caixa na auditoria atual, e 355 continuam no grupo agudo/grave. Nenhum foi apagado do histórico.

A cobertura geral passou de 2.773 para 2.518 grafias do TM sem entrada literal/NFC. O fallback legado continua ativo para as lacunas restantes; esta aplicação não o considera prova de identidade morfológica.

## Histórico e preservação

O relatório aprovado reports/audit/agudo-grave/revisao.json e sua lista de sugestões permaneceram intactos. A nova auditoria do grupo está em reports/audit/agudo-grave/pendentes/. O registro de aprovação foi acrescentado a decisions.json.

Baseline, backups e relatório histórico de migração foram preservados. TM, LXX e capítulos traduzidos não foram editados por esta aplicação. As alterações externas em Mateus 19 e no log de formas ausentes foram preservadas. Não foi criado backup nem commit.

## Limites da validação

Os testes direcionados passaram. A suíte completa tem falhas históricas já diagnosticadas; o build integral não foi repetido e nenhum baseline foi alterado para mascará-las. A verificação de espaços dos arquivos do lote passou; a global apontou espaço final no arquivo Mateus 19, que já estava em edição fora do lote e não foi alterado por esta aplicação.
