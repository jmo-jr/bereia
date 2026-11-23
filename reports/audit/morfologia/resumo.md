# Auditoria de agrupamentos e morfologia

Estado: **AUDITORIA_CONCLUIDA**.

Dados originais preservados. Os achados contam regras acionadas: uma flexão pode aparecer em mais de uma categoria.

## Cobertura

- grupos_strong: 5379.
- flexoes: 19192.
- formas_nfc: 19184.
- cobertura_codigos: {"codigo_comparavel": 19095, "codigo_nao_comparavel": 97, "divergencias_nominais_uma_ocorrencia_ignoradas": 52, "registros_verbais_genericos_sem_analise_flexional": 1}.
- achados: 924.
- flexoes_com_achados: 869.
- achados_por_tipo: {"classe_flexao_lema": 333, "codigo_descricao": 1, "grafia_com_invisiveis_ou_espacos": 6, "parsing_auxiliar_divergente": 503, "strong_auxiliar_divergente": 79, "strong_verbete_lema": 2}.
- achados_por_estado: {"ERRO_COMPROVADO": 1, "REVISAO_MANUAL": 923}.
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

- **G1510 / flexão 49 — ὧν​** (codigo_descricao): `V-PPA-NMS`; Verbo - Presente Particípio - Nominativo Masculino Singular. Código e descrição expressam traços diferentes; a inconsistência é objetiva, mas o campo a corrigir exige validar a análise. Traços: [{"traco": "voz", "codigo": ["A"], "descricao": []}]. Referências: sem ocorrência literal/NFC no TM. Sem candidato único pela fonte alinhada. Detalhamento completo no JSON.

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
