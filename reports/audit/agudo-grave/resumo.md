# Revisão do lote agudo/grave

Escopo: 1CO, 1JO, 1PE, 1TM, 1TS, 2CO, 2JO, 2PE, 2TM, 2TS, 3JO, AP, AT, CL, EF, FM, FP, GL, HB, JD, JO, LC, MC, MT, RM, TG, TT.

- formas: 636.
- tokens_nt: 26554.
- estados: {'INCERTO': 381, 'SUGERIR': 255}.
- grupos: {'cobertura_parcial_do_parsing': 169, 'evidencia_consistente': 255, 'morfologia_divergente': 41, 'morfologia_nao_comparavel': 128, 'outros_candidatos_sem_marcas': 2, 'sem_parsing_alinhado': 33, 'strong_divergente': 8}.
- sinais_sobrepostos: {'cobertura_parcial_do_parsing': 299, 'descricao_a_revisar': 119, 'morfologia_divergente': 41, 'morfologia_nao_comparavel': 131, 'outros_candidatos_sem_marcas': 2, 'sem_parsing_alinhado': 33, 'strong_divergente': 8}.
- com_parsing_integral: 337.
- tokens_das_sugestoes: 672.

Nenhum dado original alterado. As minutas dependem de aprovação lexical; consistência morfológica não basta para copiar glosas automaticamente.

SUGERIR indica evidência estrutural consistente em todas as ocorrências. INCERTO reúne lacunas e divergências, sem declarar erro objetivo.

Códigos completos e referências por evidência em revisao.json; as descrições e glosas anteriores permanecem nos candidatos.

Reprodução: `python3 -B -m tools.audit.audit_accents`.
