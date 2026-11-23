# Auditoria de agrupamentos e morfologia

Estado: **AUDITORIA_CONCLUIDA**.

Dados originais preservados. Os achados contam regras acionadas: uma flexão pode aparecer em mais de uma categoria.

## Cobertura

- grupos_strong: 5379.
- flexoes: 18897.
- formas_nfc: 18889.
- cobertura_codigos: {"codigo_comparavel": 18802, "codigo_nao_comparavel": 95, "divergencias_nominais_uma_ocorrencia_ignoradas": 52, "registros_verbais_genericos_sem_analise_flexional": 1}.
- achados: 939.
- flexoes_com_achados: 878.
- achados_por_tipo: {"classe_flexao_lema": 329, "codigo_descricao": 14, "grafia_com_invisiveis_ou_espacos": 6, "parsing_auxiliar_divergente": 509, "strong_auxiliar_divergente": 79, "strong_verbete_lema": 2}.
- achados_por_estado: {"ERRO_COMPROVADO": 14, "REVISAO_MANUAL": 925}.
- formas_repetidas: 8.
- repeticoes_por_tipo: {"analises_distintas_atestadas": 2, "mesma_analise_metadados_distintos": 3, "multiplicidade_a_validar": 3}.

## Produtos derivados

- Formas divergentes no dicionário plano: 0.
- Formas com índice divergente: 0.
- Aliases com destino deslocado: 0.
- Detalhes em `produtos.json`. Nenhum produto foi regenerado durante a auditoria.

## Casos prioritários

- **G1510/49 — ὧν​** (grafia_com_invisiveis_ou_espacos): Pode ser marcador histórico de diferenciação. Conferir TM e agrupamento; não remover nem associar automaticamente.
- Valores e provas completas em `prioridades.json`; os registros atuais relacionados a ὢν/ὧν estão em `caso-on.json`.

## Inconsistências internas comprovadas

O erro comprovado é a contradição ou ausência técnica indicada. Nenhuma análise foi escolhida automaticamente para resolver o conflito.

- **G166 / flexão 4 — αἰωνίου** (codigo_descricao): `Adj-GFS`; Adjetivo - Genitivo Neutro Singular. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "genero", "codigo": ["F"], "descricao": ["N"]}]. Referências: MC 3:29#19, TT 1:2#4, TT 3:7#11, 1TM 6:12#9, 1TM 6:19#11, 2TM 2:10#19, AT 13:46#28, HB 13:20#19. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

- **G1510 / flexão 49 — ὧν​** (codigo_descricao): `V-PPA-NMS`; Verbo - Presente Particípio - Nominativo Masculino Singular. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "voz", "codigo": ["A"], "descricao": []}]. Referências: sem ocorrência literal/NFC no TM. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

- **G2052 / flexão 3 — ἐριθείας** (codigo_descricao): `S-GFS`; Substantivo - Genitivo Feminino Singular/Acusativo Feminino Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "caso", "codigo": ["G"], "descricao": ["A", "G"]}, {"traco": "numero", "codigo": ["S"], "descricao": ["P", "S"]}]. Referências: FP 1:16#4, RM 2:8#4. Código candidato pela fonte alinhada: `S-GFS` (não aplicado; conferir limites no JSON). Detalhamento completo no JSON.

- **G2064 / flexão 52 — ἔρχου** (codigo_descricao): `V-PIM-2S`; Verbo - Presente Imperativo Média - 2ª Pessoa Singular. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "modo", "codigo": ["I"], "descricao": ["M"]}]. Referências: AP 22:20#10, JO 11:34#9. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

- **G2478 / flexão 0 — ἰσχυρά** (codigo_descricao): `Adj-ANP`; Adjetivo - Acusativo Neutro Plural/Feminino Singular. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "genero", "codigo": ["N"], "descricao": ["F", "N"]}, {"traco": "numero", "codigo": ["P"], "descricao": ["P", "S"]}]. Referências: 1CO 1:27#24, AP 18:10#21. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

- **G2478 / flexão 11 — ἰσχυρῶν** (codigo_descricao): `Adj-GFP`; Adjetivo - Genitivo Masculino/Feminino Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "genero", "codigo": ["F"], "descricao": ["F", "M"]}]. Referências: AP 19:18#10, AP 19:6#16. Código candidato pela fonte alinhada: `Adj-GFP` (não aplicado; conferir limites no JSON). Detalhamento completo no JSON.

- **G2588 / flexão 4 — καρδίας** (codigo_descricao): `S-GFS`; Substantivo - Genitivo Feminino Singular/Acusativo Feminino Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "caso", "codigo": ["G"], "descricao": ["A", "G"]}, {"traco": "numero", "codigo": ["S"], "descricao": ["P", "S"]}]. Referências: 1PE 3:4#5, AT 2:46#20, CL 3:22#18, LC 9:47#8, MC 3:5#11, RM 2:29#9, 1JO 3:19#15, 1TS 2:4#22. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

- **G2605 / flexão 4 — καταγγέλλουσιν** (codigo_descricao): `V-PIA-3P`; Verbo - Presente Indicativo/Particípio Ativa - 3ª Pessoa/Dativo Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "modo", "codigo": ["I"], "descricao": ["I", "P"]}]. Referências: AT 16:17#19, AT 16:21#2, FP 1:16#7, 1CO 9:14#9. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

- **G2634 / flexão 1 — κατακυριεύουσιν** (codigo_descricao): `V-PIA-3P`; Verbo - Presente Indicativo/Subjuntivo Ativa - 3ª Pessoa/Dativo Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "modo", "codigo": ["I"], "descricao": ["I", "S"]}]. Referências: MC 10:42#15, MT 20:25#13. Código candidato pela fonte alinhada: `V-PIA-3P` (não aplicado; conferir limites no JSON). Detalhamento completo no JSON.

- **G2635 / flexão 3 — καταλαλοῦσιν** (codigo_descricao): `V-PIA-3P`; Verbo - Presente Indicativo/Subjuntivo Ativa - 3ª Pessoa/Dativo Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "modo", "codigo": ["I"], "descricao": ["I", "S"]}]. Referências: 1PE 2:12#12, 1PE 3:16#7. Código candidato pela fonte alinhada: `V-PIA-3P` (não aplicado; conferir limites no JSON). Detalhamento completo no JSON.

- **G3498 / flexão 8 — νεκρῶν** (codigo_descricao): `Adj-GMP`; Adjetivo - Genitivo Neutro Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "genero", "codigo": ["M"], "descricao": ["N"]}]. Referências: 1CO 15:21#11, 1PE 1:21#11, 1PE 1:3#27, GL 1:1#20, JO 12:17#20, JO 12:9#27, LC 16:30#11, LC 9:7#22. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

- **G3860 / flexão 11 — παραδίδοται** (codigo_descricao): `V-PIP-3S`; Verbo - Presente Indicativo Média ou Passiva - 3ª Pessoa Singular. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "voz", "codigo": ["P"], "descricao": ["M", "P"]}]. Referências: LC 22:22#18, MC 14:21#22, MC 14:41#17, MT 26:24#22, MT 26:45#24, MC 9:31#14, MT 26:2#14. Código candidato pela fonte alinhada: `V-PIP-3S` (não aplicado; conferir limites no JSON). Detalhamento completo no JSON.

- **G4863 / flexão 22 — συνηγάγετέ** (codigo_descricao): `V-AI/MA-2P`; Verbo - Aoristo Indicativo Ativa - 2ª Pessoa Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "modo", "codigo": ["I", "M"], "descricao": ["I"]}]. Referências: MT 25:35#14, MT 25:43#5. Código candidato pela fonte alinhada: `V-AIA-2P` (não aplicado; conferir limites no JSON). Detalhamento completo no JSON.

- **G5100 / flexão 5 — τινες** (codigo_descricao): `IPro-NMP`; Pronome Interrogativo/Indefinido - Nominativo Neutro Plural. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "genero", "codigo": ["M"], "descricao": ["N"]}]. Referências: 1CO 6:11#3, AT 17:28#11, AT 19:9#3, JO 6:64#5, MC 14:57#2, 1TM 5:15#3, LC 24:1#17, LC 24:22#4. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

## Formas repetidas

- **εὗρον** — REVISAO_MANUAL: multiplicidade_a_validar. G2147/36: V-AIA-1S/3P; G2147/37: V-AIA-1S.

- **ζητήσεις** — REVISAO_MANUAL: multiplicidade_a_validar. G2212/17: V-FIA-2S; G2214/1: S-AFP.

- **κακοποιῶν** — AMBIGUIDADE_LEGITIMA: analises_distintas_atestadas. G2554/2: V-PPA-NMS; G2555/1: Adj-GMP.

- **καλῶν** — AMBIGUIDADE_LEGITIMA: analises_distintas_atestadas. G2564/33: V-PPA-NMS; G2570/11: Adj-GNP.

- **κλάσει** — REVISAO_MANUAL: multiplicidade_a_validar. G2800/0: S-DFS; G2806/4: V-FIA-3S.

- **οὐ** — REVISAO_MANUAL: mesma_analise_metadados_distintos. G3756/0: Adv; G3756/1: Adv.

- **ἀγαθοποιῆσαι** — REVISAO_MANUAL: mesma_analise_metadados_distintos. G15/0: V-ANA; G15/2: V-ANA.

- **ὢν** — REVISAO_MANUAL: mesma_analise_metadados_distintos. G1510/46: V-PPA-NMS; G1510/48: V-PPA-NMS.

## Próximos passos

- JSON válido nesta execução; conferir os produtos derivados e o estado linguístico após qualquer aplicação.
- Priorizar contradições internas e registros verbais incompletos, validando a forma e o parsing alinhado antes de decidir qual campo corrigir.
- Examinar os marcadores invisíveis sem apagá-los: podem participar da diferenciação histórica de homógrafos.
- Manter divergências entre fontes e classes lexicais em revisão manual; não converter particípios ou infinitivos em substantivos por causa da tradução.
- Não excluir duplicatas nem verbetes flexionais antes de revisar metadados e dependências de índices.
- A lista de códigos não comparáveis é limite explícito da auditoria, não lista de códigos necessariamente errados.

Fonte lexical: TBESG, Tyndale House/STEPBible, baseado em Abbott-Smith, CC BY 4.0 ([origem](https://STEPBible.github.io/STEPBible-Data)). As classes são usadas apenas para triagem.
