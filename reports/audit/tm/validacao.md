# Validação da implementação

- `python3 -B -m unittest tools.audit.test_audit_tm -v`: 9 testes passaram.
- Cache frio, quente e desativado: quatro relatórios JSON/Markdown idênticos byte a byte.
- Cache com chave obsoleta: recalculado, sem mudança dos resultados.
- Regressão ἀρχῇ/ἀρχή: exercitada também contra o loader JavaScript real.
- Hashes das fontes do inventário: conferidos novamente após os testes, sem alterações.
- Projeção plana e índice multianálise: coerentes com o léxico atual.
- `git diff --check`: passou.
- `npm test`: 4 passaram e 5 falharam na suíte existente. Há ausência de
  `src/_data/archive/strongsg.js`, divergência com o relatório histórico de
  alterações de tokens e falhas de renderização/navegação nas verificações
  existentes. Nenhum baseline, relatório histórico ou arquivo de produção foi
  ajustado para acomodar essas falhas. A auditoria nova passa separadamente.

Os relatórios em `reports/` são ignorados pelo Git conforme a configuração
existente. Os testes novos estão em `tools/audit/`, pois `tests/` também é ignorado.
