# Triagem de cobertura e consulta experimental

Escopo: 1CO, 1JO, 1PE, 1TM, 1TS, 2CO, 2JO, 2PE, 2TM, 2TS, 3JO, AP, AT, CL, EF, FM, FP, GL, HB, JD, JO, LC, MC, MT, RM, TG, TT.

Formas sem cobertura literal/NFC: 1069.

- agudo_grave_mesma_posicao: 355.
- espacos_marginais: 3.
- outras_marcas: 172.
- outros_acentos: 539.

As categorias descrevem diferenças gráficas. Nenhuma cria equivalência ou autoriza fusão.
Agudo/grave conserva a posição da marca. Outros acentos incluem diferenças de posição, presença e circunflexo.
Os grupos também podem conter candidatos de outras categorias; cada candidato tem classificação própria.

## Consulta estrita em paralelo

- cobertura_estrita: 18517 formas.
- multiplas_analises_preservadas: 10 formas.
- sem_cobertura_estrita_com_fallback_atual: 1069 formas.

- cobertura_estrita: 108442 tokens.
- multiplas_analises_preservadas: 768 tokens.
- sem_cobertura_estrita_com_fallback_atual: 31048 tokens.

A consulta sem retirada de marcas aceita literal/NFC e equivalência por caixa, preservando todas as análises correspondentes.
Consulta em produção registrada no inventário: literal_nfc_caixa_antes_do_fallback_legado.
Não altera o loader, o painel, os dados ou as exceções. Diferença entre consultas não comprova erro de tradução.

## Decisão humana

O piloto ἀρχῇ mantém a proposta técnica S-DFS separada da decisão de glosas.
O piloto registra contextos do TM e traduções existentes com hashes; o número de ocorrências depende do escopo.
No escopo integral, cinco ocorrências estão registradas e quatro têm parsing auxiliar alinhado N-DSF.
Glosas aprovadas pelo usuário: traducao="no princípio, ao principado"; pt="no princípio".
Lucas 20:20 usa poder na tradução existente; as demais usam princípio. Não atribuir acepções automaticamente.
A inclusão de ἀρχῇ foi aplicada ao dicionário com as glosas aprovadas; não consta das propostas pendentes.

## Reprodução

`python3 -B -m tools.audit.triage_tm`

A execução recusa inventários com fontes alteradas. Artefatos determinísticos, sem data ou caminho absoluto.
