# Auditoria do TM — etapa 1

Escopo: 1CO, 1JO, 1PE, 1TM, 1TS, 2CO, 2JO, 2PE, 2TM, 2TS, 3JO, AP, AT, CL, EF, FM, FP, GL, HB, JD, JO, LC, MC, MT, RM, TG, TT.

Dados originais preservados. Hashes, critérios e referências em inventario.json.

- tokens_tm: 140258
- formas_tm: 19596
- classes: {"ausente": 714, "exata": 17431, "somente_caixa": 1449, "somente_nfc": 2}
- ausentes_com_candidatos: 711
- formas_com_multiplas_analises: 10
- formas_com_multiplos_candidatos: 1489
- ausentes_apenas_caixa: 0
- formas_com_ambiguidade_caixa: 0
- formas_com_multiplas_analises_por_caixa: 2
- formas_com_alias_contextual_validado: 0
- tokens_alias_contextual_validado: 0
- tokens_alias_contextual_pendente: 0
- tokens_com_ambiguidade_caixa: 0
- consulta_atual_forma_diferente_nfc: 2163
- alinhamento_versiculos: {"alinhado": 6767, "parsing_invalido": 22, "quantidade_divergente": 2, "sem_fonte": 1, "sequencia_divergente": 1167}
- comparacoes: {"codigo_identico": 34, "forma_ausente": 709, "morfologia_divergente": 98, "nao_comparavel": 12754, "strong_divergente": 100, "substantivo_compativel": 4694, "substantivo_compativel_nom_acus_neutro": 144}
- Fontes referenciadas ausentes: ['src/_data/archive/strongsg.js', 'src/_data/strongs_greek_pt_defs.json'].
- Produtos derivados: {"derivado_coerente": false, "indice_coerente": true}
- Formas com divergências nas fontes ou na consulta atual: 334.

## Caso ἀρχῇ / ἀρχή

A flexão própria ἀρχῇ está no dicionário e a consulta atual a retorna separadamente de ἀρχή. Historicamente, a consulta removia marcas e selecionava ἀρχή para a chave αρχη. Em JO 1:1#2 e JO 1:2#4, o CSV alinhado informa G746 / N-DSF (dativo singular feminino). A associação ao nominativo perde o iota subscrito. NFC preserva essa distinção. Veja caso-arche.json.

## Limites e proposta de correção

- Três grafias sem candidatos contêm espaço final: Εὗρον , βασιλείας , εὗρον . Preservadas; conferir referências no inventário antes de propor qualquer ajuste.
- Ausências incluem caixa, acentos contextuais e flexões distintas; examinar as referências antes de propor inclusão.
- Fontes Strong históricas referenciadas pelos scripts (strongsg.js e strongs_greek_pt_defs.json) estão ausentes. TBESG está disponível; não foi usado para decidir flexões nesta etapa.
- Falhas de alinhamento ficam sem comparação auxiliar; não deslocar tokens nem inferir Strong pela forma normalizada.
- Divergências de parsing são evidências para revisão. Códigos verbais e compostos sem adaptador ficam não comparáveis.
- Substituir futuramente a consulta por índice literal/NFC multianálise, mantendo identificadores Strong e flexão. Em ambiguidade, conservar todas as análises.
- Usar candidatos sem diacríticos somente na revisão; não os usar como fallback automático. Validar cobertura e regressões antes de retirar exceções.
- Acompanhar a aplicação aprovada de ἀρχῇ em tools/audit/decisions.json; não renomear ἀρχή nem transferir sua tradução.
- Aplicar a mesma distinção no painel Strong. A projeção plana perde análises adicionais; usar o índice e a fonte completa.
- Etapa 2: propostas separadas por lema/Strong literal e por flexão, com IDs strong + flexao, hashes, referências e decisão humana. Nenhuma consolidação nesta etapa.
