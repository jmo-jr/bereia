# AI-GREEK-REVIEW

## 1. Objetivo

Este documento define as regras para revisão do dicionário de flexões gregas utilizado no projeto de interlinear bíblico.

O objetivo é identificar e corrigir, com segurança:

- erros de forma grega;
- erros de flexão ou análise morfológica;
- erros de Strong's;
- erros de transliteração;
- traduções inadequadas;
- inconsistências entre formas equivalentes;
- ambiguidades morfológicas;
- homógrafos que diferem apenas por diacríticos;
- inconsistências de tratamento entre entradas.

A revisão deve priorizar **precisão morfológica, consistência e rastreabilidade**, e não a naturalidade literária da tradução portuguesa.

---

# 2. Regra fundamental: não alterar sem evidência

Não modificar uma entrada apenas porque outra tradução parece mais elegante ou natural.

Antes de alterar qualquer campo, verificar:

1. a forma grega;
2. o lema correspondente;
3. a análise morfológica;
4. o Strong's;
5. a transliteração;
6. o sentido lexical;
7. a função da forma no contexto bíblico, quando necessário.

Quando houver dúvida real, **marcar a entrada como SUSPEITA ou AMBIGUIDADE em vez de inventar uma correção**.

Nunca realizar alterações em massa sem verificar se a regra realmente se aplica a todas as ocorrências.

---

# 3. Estrutura das entradas

O dicionário utiliza informações equivalentes a:

```json
{
  "strongs": "...",
  "grego": "...",
  "transliteracao": "...",
  "verbete": "...",
  "traducao": "...",
  "pt": "...",
  "abrev_morf": "...",
  "morfologia": "..."
}
```

Os campos devem permanecer semanticamente coerentes entre si.

## 3.1. strongs

O Strong's deve corresponder ao lema/entrada lexical correta.

Não inferir um Strong's apenas pela semelhança gráfica.

Quando dois lemas possuem formas semelhantes, verificar o lema e a morfologia antes de decidir.

---

# 4. Forma grega

A forma grega deve ser preservada com sua ortografia correta, incluindo:

- acentos;
- espíritos;
- iota subscrito;
- diacríticos pertinentes.

Não remover diacríticos para "padronizar" as formas.

A comparação sem diacríticos deve ser utilizada apenas para detectar possíveis homógrafos conforme as regras abaixo.

---

# 5. Homógrafos

## 5.1. Definição adotada no projeto

Considerar **homógrafas** as formas que possuem exatamente a mesma sequência de letras quando os diacríticos são removidos, mas diferem por algum diacrítico, especialmente acento.

Exemplo:

```text
φόβου
φοβοῦ
```

Sem os diacríticos:

```text
φοβου
```

Portanto, devem ser sinalizadas como formas homógrafas.

O objetivo aqui é **ortográfico**, não lexical.

Não classificar como homógrafas apenas porque:

- pertencem ao mesmo lema;
- são formas flexionadas do mesmo verbo;
- possuem significado relacionado;
- possuem a mesma pronúncia;
- são semanticamente próximas.

A comparação deve ser restrita à sequência de letras.

---

# 6. Lista atual de exceções/conjuntos conhecidos

O projeto já possui uma lista de formas para as quais a coincidência sem diacríticos é conhecida:

```text
[
  "α",
  "εν",
  "η",
  "ης",
  "ην",
  "ητε",
  "ου",
  "ους",
  "ει",
  "ως",
  "ο",
  "ος",
  "αν",
  "τις",
  "που",
  "πως",
  "αυτου",
  "αυτη",
  "δη",
  "ανω",
  "ημερα",
  "εκτος",
  "τι",
  "εις",
  "τινι",
  "γενεας",
  "ετερα",
  "τινες",
  "ηλιου",
  "φοβου",
  "προσευχη",
  "ωσιν"
]
```

Essa lista não deve ser considerada necessariamente completa.

Ao encontrar uma nova forma que satisfaz a regra de coincidência sem diacríticos, sinalizar para possível inclusão.

---

# 7. Formas idênticas sem diacríticos

Apenas a coincidência ortográfica não significa que duas entradas devam ser unificadas.

Exemplo conceitual:

```text
forma A → análise morfológica A
forma B → análise morfológica B
```

Se ambas possuem a mesma sequência de letras sem diacríticos, devem continuar sendo entradas distintas quando representam análises diferentes.

O objetivo do dicionário é preservar a informação morfológica, e não reduzir formas distintas a uma única entrada.

---

# 8. Ambiguidade morfológica

Uma mesma forma gráfica pode representar mais de uma análise morfológica.

Isso deve ser **explicitamente sinalizado**.

Exemplos já identificados no projeto:

### εὗρον

Pode representar:

- 1ª pessoa do singular;
- 3ª pessoa do plural.

O contexto deve determinar a interpretação.

### ἔρχου

A forma pode gerar ambiguidade de análise dependendo do sistema morfológico utilizado.

Não assumir automaticamente uma única análise quando a forma permite outra.

### κλίνῃ

Verificar cuidadosamente as possibilidades morfológicas antes de classificá-la.

### ἀκολουθοῦσιν / ἀκολουθοῦσίν

Verificar se a forma está sendo tratada como:

- verbo;
- particípio;

ou outra análise possível segundo o paradigma e o sistema morfológico utilizado.

## Regra geral

Sempre que uma sequência gráfica puder corresponder a mais de uma:

- pessoa;
- número;
- tempo;
- modo;
- voz;
- caso;
- gênero;
- função morfológica;

registrar a ambiguidade.

Não escolher arbitrariamente uma análise apenas porque uma delas é mais frequente.

---

# 9. Contexto resolve ambiguidades

Quando uma forma é morfologicamente ambígua, a análise lexical/morfológica deve distinguir:

**forma possível** de **interpretação contextual**.

Não transformar automaticamente uma interpretação contextual em uma propriedade absoluta da forma.

Exemplo:

```text
Forma: εὗρον

Possibilidades morfológicas:
- 1ª pessoa singular
- 3ª pessoa plural

A tradução/interpretação final depende do contexto.
```

---

# 10. Tradução

## 10.1. Prioridade

A tradução deve buscar uma correspondência **consistente com a função e o valor da forma grega**.

Não priorizar uma tradução portuguesa estilisticamente elegante se isso sacrificar a consistência interlinear.

O interlinear não precisa produzir português natural.

---

# 11. Traduções genéricas

Quando um termo possui vários sentidos contextuais, estabelecer uma tradução-base que possa funcionar de maneira consistente no maior número possível de ocorrências.

Não criar dezenas de traduções diferentes apenas para produzir português natural.

Entretanto, não forçar uma tradução genérica quando a morfologia ou o contexto tornam o sentido claramente diferente.

---

# 12. δέ

Para fins de tradução-base do projeto, evitar tratar δέ simplesmente como:

```text
e
```

Quando funcionar como elemento de continuidade, contraste leve ou progressão discursiva, considerar especialmente:

```text
então
por sua vez
```

A escolha exata depende do contexto.

A tradução-base deve refletir sua função discursiva, não apenas substituir mecanicamente δέ por "e".

---

# 13. Tradução baseada na voz verbal

Não assumir que a voz, isoladamente, determina sempre a tradução.

Entretanto, para verbos cuja diferença semântica entre voz ativa e passiva seja consistente, a voz pode servir como critério de generalização.

Exemplo discutido:

## ἵστημι

Como generalização inicial:

### Ativa

```text
colocar
posicionar
```

### Passiva

```text
ser colocado
estar de pé
```

A escolha final deve respeitar a morfologia e o sentido lexical da forma.

Não aplicar automaticamente essa regra a qualquer verbo.

---

# 14. Transitivo / intransitivo

Não utilizar simplesmente "transitivo" ou "intransitivo" como substituto da análise de voz.

Um verbo pode ter comportamentos diferentes dependendo:

- do contexto;
- da construção sintática;
- da voz;
- do sentido lexical.

A voz pode ajudar na escolha de uma tradução-base, mas não deve ser utilizada como regra universal.

---

# 15. φαίνω

Ao revisar φαίνω e formas relacionadas, verificar:

- voz;
- transitividade;
- sentido contextual;
- construção sintática.

Não assumir que a voz, sozinha, determina automaticamente o significado.

---

# 16. Verbos com tradução dependente da construção

Para verbos como:

- δύναμαι;
- ἀφίημι;
- παρακαλέω;
- φαίνω;
- ἵστημι;

considerar a construção completa antes de alterar a tradução.

A tradução-base deve ser suficientemente genérica para representar o lema sem eliminar distinções morfológicas importantes.

---

# 17. Diacríticos

Não tratar diferenças de acento como erros automaticamente.

Exemplo:

```text
Ἀκοῇ
ἀκοαῖς
```

não são simplesmente "a mesma palavra com acentos diferentes".

A comparação ortográfica deve considerar a sequência real das letras.

Da mesma forma, formas como:

```text
ὠσὶν
ὦσιν
```

devem ser verificadas quanto à sequência de letras e à análise morfológica.

---

# 18. Formas parecidas, mas não homógrafas

Não expandir a análise de homógrafos para palavras apenas semelhantes.

Exemplo:

Duas formas podem:

- possuir o mesmo radical;
- pertencer ao mesmo lema;
- possuir significados relacionados;

e ainda assim não serem homógrafas.

O critério de homografia utilizado neste projeto é estritamente ortográfico:

> mesma sequência de letras após remoção dos diacríticos.

---

# 19. Formas que diferem apenas por diacríticos

Sempre que uma nova entrada for encontrada, verificar se existe outra entrada cuja forma:

1. possui exatamente as mesmas letras;
2. difere somente em acento, espírito ou outro diacrítico.

Quando existir, sinalizar:

```text
HOMÓGRAFA POR DIACRÍTICO
```

e apresentar as formas lado a lado.

Exemplo:

```text
φόβου
φοβοῦ
```

---

# 20. Casos de ambiguidade versus homografia

Não confundir:

### Homografia por diacrítico

Duas formas diferentes na grafia completa, mas iguais quando os diacríticos são removidos.

### Ambiguidade morfológica

Uma mesma forma pode receber mais de uma análise morfológica.

É possível que uma forma seja simultaneamente:

- parte de um conjunto de homógrafos;
- morfologicamente ambígua.

As duas propriedades devem ser registradas separadamente.

---

# 21. Tradução de partículas e preposições

Para partículas e preposições, considerar especialmente:

- função sintática;
- função discursiva;
- caso governado;
- valor semântico;
- construção em que aparecem.

Exemplos que exigem atenção especial:

```text
δέ
ἐπί
ἀντί
διά
ὑπό
εἰς
```

Não atribuir automaticamente uma única tradução portuguesa a todas as ocorrências quando a construção produzir valores claramente diferentes.

---

# 22. εἰς

Não traduzir εἰς mecanicamente sempre da mesma maneira.

O sentido-base deve considerar sua função preposicional e o contexto.

Possibilidades incluem, conforme a construção:

```text
para
em
até
```

A escolha deve preservar, tanto quanto possível, a relação expressa pela preposição.

---

# 23. Morfologia

A abreviação morfológica deve corresponder à análise morfológica completa.

Exemplo conceitual:

```text
abrev_morf: V-AAI-3P
morfologia: verbo, aoristo, ativo, indicativo, 3ª pessoa do plural
```

Não permitir que:

- abreviação;
- descrição textual;
- forma grega;

se contradigam.

---

# 24. Flexões verbais

Ao revisar uma forma verbal, verificar:

1. lema;
2. tempo;
3. aspecto quando relevante;
4. voz;
5. modo;
6. pessoa;
7. número;
8. forma ortográfica;
9. tradução.

Exemplos que já exigiram atenção especial:

```text
ἐθρηνήσαμεν
ἐκόψασθε
ὑψωθεῖσα
καταβιβασθήσῃ
ἐγένοντο
ἔμειναν
Ἐξομολογοῦμαί
κοπιῶντες
ἀναπαύσω
ἐξῆλθον
```

Não presumir que duas formas semanticamente próximas possuam a mesma análise morfológica.

---

# 25. Formas nominais

Para substantivos, adjetivos, particípios e pronomes, verificar:

- caso;
- número;
- gênero;
- lema;
- forma;
- concordância quando o contexto estiver disponível.

Particular atenção para formas que podem compartilhar a mesma grafia em casos ou números diferentes.

---

# 26. Pronomes

Pronomes devem ser analisados com atenção especial porque algumas formas são muito ambíguas.

Exemplo:

```text
σεαυτόν
```

Verificar:

- pessoa;
- número;
- caso;
- gênero;
- natureza reflexiva;
- lema correspondente.

Não reduzir a análise simplesmente à tradução portuguesa.

---

# 27. Tradução interlinear

A tradução deve permanecer suficientemente próxima da estrutura grega para permitir que o leitor:

1. veja a forma grega;
2. identifique a flexão;
3. veja a tradução correspondente;
4. compreenda a função da forma.

Evitar "corrigir" o grego para produzir uma tradução literária.

---

# 28. Consistência

Quando duas formas pertencem ao mesmo lema e possuem funções equivalentes, verificar se suas traduções-base são coerentes.

Por outro lado, não exigir uniformidade artificial quando a diferença morfológica ou sintática justifica traduções diferentes.

A pergunta principal é:

> A diferença de tradução é explicada por uma diferença real da forma ou do contexto?

Se não houver justificativa, sinalizar possível inconsistência.

---

# 29. Procedimento de revisão

Nunca revisar o arquivo inteiro de uma única vez.

Preferir lotes pequenos, por exemplo:

```text
50–100 entradas por etapa
```

Para cada lote:

### Etapa 1 — análise

Não alterar o arquivo.

Classificar cada entrada como:

```text
OK
SUSPEITA
ERRO
AMBIGUIDADE
HOMÓGRAFA
```

### Etapa 2 — relatório

Para cada problema:

```text
Forma:
Strong's:
Problema:
Análise atual:
Análise sugerida:
Tradução atual:
Tradução sugerida:
Motivo:
Confiança:
```

### Etapa 3 — aprovação

Aguardar aprovação humana quando houver alteração substantiva.

### Etapa 4 — alteração

Modificar somente as entradas aprovadas.

### Etapa 5 — validação

Depois da alteração:

- validar JSON;
- verificar estrutura;
- verificar campos obrigatórios;
- procurar duplicações acidentais;
- verificar inconsistências introduzidas pela alteração.

---

# 30. Níveis de confiança

Sempre que houver dúvida, classificar:

### ALTA

A forma e a análise são claramente determinadas.

### MÉDIA

Há evidência forte, mas existe alguma possibilidade alternativa.

### BAIXA

A decisão depende de contexto ou de uma questão lexical/morfológica discutível.

Não alterar automaticamente entradas com confiança baixa.

---

# 31. Alterações proibidas sem confirmação

Não fazer automaticamente:

- mudanças grandes de tradução;
- mudança de Strong's;
- mudança de lema;
- alteração de análise morfológica ambígua;
- fusão de entradas;
- exclusão de entradas;
- normalização de diacríticos;
- substituição sistemática de traduções;
- alterações que afetem muitas entradas por uma regra ainda não validada.

Primeiro apresentar os casos.

---

# 32. Comparação com fontes externas

Quando uma questão morfológica não puder ser resolvida com segurança pelo próprio paradigma ou pelos dados existentes no projeto, consultar fontes lexicais/morfológicas confiáveis.

Dar preferência a:

1. texto grego utilizado pelo projeto;
2. dados morfológicos do projeto;
3. MorphGNT e recursos equivalentes;
4. léxicos gregos confiáveis;
5. outras fontes acadêmicas.

Não alterar o dicionário simplesmente porque uma fonte externa apresenta uma preferência diferente.

---

# 33. Strong's e lema

Não utilizar Strong's como substituto da identificação do lema.

O fluxo correto é:

```text
forma → análise morfológica → lema → Strong's
```

e não:

```text
forma → Strong's → análise inventada
```

---

# 34. Regras de segurança para edição automática

Antes de salvar alterações:

1. confirmar que a chave da entrada correta foi modificada;
2. preservar campos não relacionados;
3. não alterar formatação desnecessariamente;
4. não reordenar todo o JSON sem necessidade;
5. não remover comentários ou metadados existentes;
6. preservar codificação Unicode;
7. validar o JSON após a alteração.

Sempre que possível, produzir um diff pequeno e facilmente revisável.

---

# 35. Princípio de conservadorismo

Quando houver duas análises plausíveis:

```text
não escolher arbitrariamente.
```

Registrar a ambiguidade.

Quando houver duas traduções plausíveis:

```text
preferir a tradução-base já estabelecida pelo projeto,
```

desde que ela não produza erro semântico.

Quando houver uma forma cuja análise não possa ser determinada com segurança:

```text
SINALIZAR
```

em vez de fabricar certeza.

---

# 36. Regra final

O revisor deve funcionar como **assistente filológico**, não como autor da tradução.

A prioridade é:

```text
1. forma grega correta
2. análise morfológica correta
3. lema correto
4. Strong's correto
5. transliteração correta
6. tradução semanticamente defensável
7. consistência com o restante do dicionário
8. naturalidade portuguesa
```

A naturalidade portuguesa nunca deve prevalecer sobre uma distinção morfológica ou semântica real.

O objetivo final é produzir um dicionário interlinear:

- morfologicamente confiável;
- lexicalmente consistente;
- transparente;
- auditável;
- conservador diante de ambiguidades;
- adequado para processamento automático;
- e suficientemente consistente para servir de base à tradução interlinear do projeto.