# Revisão do lote agudo/grave

Escopo: 1CO, 1JO, 1PE, 1TM, 1TS, 2CO, 2JO, 2PE, 2TM, 2TS, 3JO, AP, AT, CL, EF, FM, FP, GL, HB, JD, JO, LC, MC, MT, RM, TG, TT.

- formas: 355.
- tokens_nt: 24000.
- estados: {'INCERTO': 353, 'SUGERIR': 2}.
- grupos: {'cobertura_parcial_do_parsing': 153, 'evidencia_consistente': 2, 'morfologia_divergente': 38, 'morfologia_nao_comparavel': 121, 'outros_candidatos_sem_marcas': 2, 'sem_parsing_alinhado': 31, 'strong_divergente': 8}.
- sinais_sobrepostos: {'cobertura_parcial_do_parsing': 274, 'descricao_a_revisar': 112, 'morfologia_divergente': 38, 'morfologia_nao_comparavel': 124, 'outros_candidatos_sem_marcas': 2, 'sem_parsing_alinhado': 31, 'strong_divergente': 8}.
- com_parsing_integral: 81.
- tokens_das_sugestoes: 3.

Nenhum dado original alterado. As minutas dependem de aprovação lexical; consistência morfológica não basta para copiar glosas automaticamente.

SUGERIR indica evidência estrutural consistente em todas as ocorrências. INCERTO reúne lacunas e divergências, sem declarar erro objetivo.

Códigos completos e referências por evidência em revisao.json; as descrições e glosas anteriores permanecem nos candidatos.

Reprodução: `python3 -B -m tools.audit.audit_accents`.
