# Aplicação dos casos morfológicos prioritários

Seis registros corrigidos, em sete campos técnicos. Todos os demais campos e bytes do léxico foram preservados.

- **G88/1 — ἀδιάλειπτος**: `morfologia`: `Substantivo - Nominativo Feminino Singular` → `Adjetivo - Nominativo Feminino Singular`. Corrigir a classe na descrição, preservando o código adjetival e a tradução. RM 9:2#7 concorda com ὀδύνη; TBESG classifica o lema como adjetivo.

- **G2608/2 — κατεάξει**: `abrev_morf`: `V-AIA-3S` → `V-FIA-3S`. Corrigir aoristo para futuro: κατεάξει, descrição e tradução apontam para futuro; parsing alinhado de MT 12:20#4 confirma V-FAI-3S.

- **G4687/19 — σπείροντι**: `abrev_morf`: `V-PPA-GMS` → `V-PPA-DMS`. Corrigir genitivo para dativo, coerente com σπείροντι, a descrição e o parsing alinhado em MT 13:24#12 e 2CO 9:10#6.

- **G4687/20 — σπείροντος**: `abrev_morf`: `V-PPA-DMS` → `V-PPA-GM/NS`. Corrigir dativo para genitivo. Conservar na codificação os gêneros masculino/neutro já explícitos na descrição, sem atribuir neutro à ocorrência. MT 13:18#7 confirma genitivo masculino; a terminação genitiva do particípio admite masculino/neutro.

- **G4931/0 — συνετέλεσεν**: `abrev_morf`: `V-APP-GFP` → `V-AIA-3S`. Corrigir código de particípio genitivo feminino plural para aoristo indicativo ativo, terceira pessoa singular, coerente com συνετέλεσεν, descrição e parsing alinhado de MT 7:28#4.

- **G1510/48 — ὢν**: `abrev_morf`: `V-PP-NMS` → `V-PPA-NMS`; `morfologia`: `Verbo - Presente Particípio - Nominativo Masculino Singular` → `Verbo - Presente Particípio Ativa - Nominativo Masculino Singular`. Explicitar voz ativa no registro incompleto de ὢν. Preservar ambos os registros e seus metadados LXX distintos; a mesma forma e o registro G1510/46 já têm análise ativa, corroborada por 29 referências alinhadas.

## Registro preservado para decisão humana

G1510/49 contém `ὧν` + U+200B. Não tem ocorrência literal/NFC no TM. Sem o marcador, a forma visível corresponde ao pronome relativo G3739 nas 56 ocorrências com parsing alinhado; outras 23 ocorrências ficam sem atribuição auxiliar. Isso não autoriza transformar o registro em pronome.

O backup histórico já misturava a chave `ὧν` + U+200B com `grego: ὢν`, código verbal genitivo plural e contagem vazia. O registro atual mistura 81 ocorrências com morfologia nominativa singular e 344 ocorrências LXX. Não há base para escolher quais contagens e campos transportar.

Proposta não aplicada: retirar isoladamente o registro contaminado, mantendo os registros verbais `ὢν`/`ὤν` em G1510 e o pronome `ὧν` em G3739. Antes de uma exclusão aprovada, comparar os índices posteriores e reconstruir os produtos; não fundir contagens nem remover globalmente U+200B.

A duplicidade de `ὢν` foi preservada: os dois registros agora explicitam voz ativa, mas têm metadados LXX diferentes (0 e 344). A consolidação desses metadados permanece revisão manual.

Evidências e valores completos no manifesto e em `aplicacao.json`. Os relatórios atuais da auditoria estão em `reports/audit/morfologia/`.
