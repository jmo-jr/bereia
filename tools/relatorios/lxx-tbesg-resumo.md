# Auditoria TBESG — primeira etapa

Foram lidos 40 livros e 493,927 palavras. O dicionário atual deixou
28,950 formas distintas sem correspondência (78,400 ocorrências).
Todas essas ocorrências alinharam literalmente aos originais locais, por referência,
posição e forma grega. Nenhuma alteração foi feita no texto ou no dicionário.

## Candidatos lexicais (ainda não são traduções aprovadas)

- Um candidato, preservando diacríticos: 60.738 ocorrências (77,5% das lacunas).
- Um candidato, somente após retirar diacríticos: 1.696 ocorrências.
- Múltiplos candidatos: 1.324 ocorrências.
- Sem candidato pelo lema fornecido: 14.642 ocorrências.
- Algum candidato, somando os grupos acima: 63.758 ocorrências (81,3%).

Os grupos são definidos por forma, lema, parsing e classe da fonte. Não são
contagens de lemas distintos nem prova de ausência de uma palavra na TBESG.
Grafias diferentes, lemas incorretos na fonte ou alternativas não extraídas do
campo lexical podem explicar parte das lacunas. Não foi usada busca aproximada.

Entre as 60.738 ocorrências com um candidato acentuado, 44.140 apontam para
identificadores tradicionais (até G5624) e 16.598 para identificadores estendidos.
Portanto, a falta no dicionário de formas não demonstra a ausência de Strong.

## Fonte local

- 11.035 registros TBESG; IDs e linhas originais preservados.
- 1 registro sem grego, 105 sem transliteração, 1.263 sem Morph e 1 sem gloss.
- SHA-256 TBESG: `734a5b64a1152f67604bf09d32f15c0ba537151961752fcf168087b41b4d93ea`.
- Atribuição: Tyndale House e STEPBible.org, CC BY 4.0.
- Fonte: <https://github.com/STEPBible/STEPBible-Data/tree/master/Lexicons>.
- Originais consultados em `../bibliaaberta/lxx/lxx_morph/`, somente leitura.

## Limites e revisão

Morph da TBESG é categoria lexical; parsing de cada palavra vem do lxx-morph,
com confiança variável. Não foi corrigido nem tratado como análise aprovada.
A transliteração lexical não deve ser copiada para uma flexão diferente.
Nenhuma proposta portuguesa é aplicada automaticamente nesta etapa.

O CSV `lxx-tbesg-amostra-pendente.csv` contém cinco propostas para revisão,
classificadas como SUGERIR ou INCERTO. Todas estão pendentes. As transliterações
são propostas para a forma exibida e ainda precisam de conferência do padrão
editorial. Referências no CSV são exemplos, não uma análise contextual de todas
as ocorrências. O relatório JSON conserva as demais referências e os verbetes
em inglês necessários à conferência.

Esta etapa não altera o build, a janela de detalhes nem o dicionário definitivo.
