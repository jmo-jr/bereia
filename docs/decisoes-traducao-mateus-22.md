# Mateus 22 — revisão do rascunho mecânico

- **Estado:** tradução contínua proposta; aprovação editorial pendente.
- **Material de partida:** `reports/traducao/mateus/22/22.txt`, `alinhamento.json` e `decisoes.md`; todos os arquivos da pasta foram preservados.
- **Texto-base:** capítulo 22 de `src/interlinear/nt/MT.json`, conferido com `tools/tmnt/with-parsing/MAT.csv`.
- **Dicionário:** `src/_data/nt/dict_flex_nt-lxx_greek-pt.json`, localização atual do derivado, sem uso de cópias históricas.
- **Orientação:** `docs/protocolo-traducao.md`, `docs/decisoes-traducao.md` e estilo do TXT aprovado de Mateus 8. A recorrência de propostas anteriores não é aprovação editorial automática.
- **Entrega:** `src/biblia/nt/mateus/22.txt`. Não foram alterados dicionários, capítulos anteriores ou rascunhos mecânicos. Não houve chamada à API de geração.

## Conferência textual

- Mantidos os cinco títulos e intervalos do JSON; acrescentadas concordâncias editoriais. As concordâncias não significam identidade dos relatos nem foram usadas para harmonizá-los.
- **22:7:** preservados “tendo ouvido” e “aquele rei”.
- **22:10:** mantido γάμος, festa de casamento, sem substituição por uma leitura que nomeie apenas o salão.
- **22:13:** mantido ἄρατε αὐτόν, “levem-no”, além de amarrar e lançar.
- **22:14:** preservada a declaração sobre chamados e escolhidos, também presente no TM de Mt 20:16.
- **22:30:** preservado τοῦ θεοῦ, “de Deus”, em “anjos de Deus”.
- **22:37:** preservado “Jesus”, como sujeito da resposta.
- **22:38:** mantidos os dois qualificativos, “primeiro” e “grande”.
- **22:44:** preservado ὑποπόδιον τῶν ποδῶν σου, “estrado dos seus pés”, sem substituir o substantivo por outra construção do salmo.

## Decisões lexicais e sintáticas

Todas as escolhas têm **aprovação editorial pendente**.

### 22:1–10 — festa de casamento, chamados e comida

- **Formas/lemas:** γάμους / γάμος, G1062; καλέω, G2564; κεκλημένους / κεκλημένοις / κεκλημένοι; ἄριστον, G712; σιτιστά, σιτιστός, G4619; τεθυμένα, θύω, G2380.
- **Dicionário:** “casamentos/casamento”; “chamar, convidar”; “tendo sido chamados, convidados”; “refeição”; “engordados”; “tendo sido sacrificados”.
- **Adotado:** “festa de casamento” tanto para o plural quanto para o singular, pois o contexto descreve a celebração de um casamento do filho, não vários casamentos. O título editorial “bodas” permanece. “Convidados” verte os particípios perfeitos passivos de καλέω; em 22:14, “chamados” preserva a expressão já usada em Mt 20:16.
- **22:4:** “animais engordados” explicita o adjetivo substantivado, sem especificar espécies adicionais; “estão abatidos” escolhe a acepção de θύω no preparo da refeição, sem acrescentar rito de sacrifício. “Refeição” segue a glosa principal e não determina um horário moderno.
- **22:9:** “saídas dos caminhos” mantém διεξόδους τῶν ὁδῶν. “Encruzilhadas” é alternativa contextual possível, mas não foi imposta por tradição.
- **22:10:** “dos que estavam reclinados” conserva o particípio que designa os participantes da refeição, sem substituí-los por uma categoria religiosa identificada.
- **Classificação:** contextual; revisão manual de “saídas dos caminhos”.

### 22:6–7 — violência e destruição

- **Formas/lemas:** δοῦλος, G1401; ὕβρισαν, ὑβρίζω, G5195; ἀπώλεσεν, ἀπόλλυμι, G622; ἐνέπρησεν, ἐμπίπρημι, G1714.
- **Dicionário:** “escravo”; “insultaram, maltrataram”; a glosa de ἀπώλεσεν pode apresentar “pereceu, perdeu-se”; “ateou fogo, queimou”.
- **Adotado:** “escravos”, “maltrataram”, “destruiu aqueles assassinos” e “incendiou a cidade”. ἀπώλεσεν é transitivo, com “aqueles assassinos” como objeto direto, e o CSV confirma aoristo ativo de 3ª pessoa singular; não se aplicou mecanicamente a glosa intransitiva.
- **Limite:** a cidade não foi nomeada e os acontecimentos da parábola não foram convertidos em uma identificação histórica explícita.
- **Classificação:** contextual / conferência sintática.

### 22:11–14 — veste, silêncio e servidores

- **Formas/lemas:** ἔνδυμα γάμου; ἐφιμώθη, φιμόω, G5392; διάκονος, G1249; αἴρω, G142; σκότος, G4655.
- **Dicionário:** “veste” e “casamento”; “foi silenciado, amordaçado”; διάκονος: “ministro”, com função de serviço no verbete; “tomar, erguer, carregar, remover”; “escuridão”.
- **Adotado:** “veste de casamento”, sem defini-la por símbolo teológico ou uma prática social não narrada. “Ficou sem fala” exprime o resultado da passiva de φιμόω, sem inserir uma mordaça física ou um agente de silenciamento.
- **22:13:** “servidores” mantém a proposta de Mt 20:26 e a distingue de δοῦλοι, “escravos”, no restante da parábola. “Tendo amarrado … levem-no e o lancem” conserva o particípio e os dois imperativos. O segundo “o” retoma a pessoa, sem redefinir o sujeito da ação.
- **Fórmula:** “escuridão exterior … choro e ranger dos dentes” mantém a redação de Mt 8:12. “Muitos chamados, poucos escolhidos” não recebe identificação dos grupos.
- **Morfologia:** εἰσῆλθες em 22:12 é 2ª pessoa singular, “você entrou”, conforme o CSV, apesar de uma glosa de 3ª pessoa na consulta lexical.
- **Classificação:** contextual / conferência morfológica.

### 22:15–18 — armadilha e imparcialidade

- **Formas/lemas:** συμβούλιον ἔλαβον; παγιδεύσωσιν, παγιδεύω, G3802; οὐ μέλει σοι περὶ οὐδενός; βλέπεις εἰς πρόσωπον ἀνθρώπων; πειράζετε, πειράζω, G3985.
- **Dicionário:** “concílio” e “tomaram”; “apanhem numa armadilha”; “se preocupa, se importa”; “olhas”, “rosto”, “das pessoas”; “testais”.
- **Adotado:** “tomaram conselho” mantém a locução de deliberação de Mt 12:14; “em uma palavra” conserva o domínio verbal da armadilha sem inventar uma resposta esperada. “Não se deixa influenciar por ninguém” escolhe a acepção idiomática de independência perante pessoas, não uma afirmação de indiferença ao sofrimento. A imagem explicativa seguinte, “não olha para o rosto das pessoas”, permanece literal.
- **Contexto da fala:** o elogio é atribuído aos enviados dos fariseus e aos herodianos; não foi transformado em comentário avaliativo independente do narrador.
- **Classificação:** contextual; revisão manual da naturalidade da combinação entre expressão idiomática e imagem literal em 22:16.

### 22:17–22 — imposto, imagem e devolução

- **Formas/lemas:** κῆνσος, G2778; νόμισμα, G3546; δηνάριον, δηνάριον, G1220; εἰκών, G1504; ἐπιγραφή, G1923; ἀπόδοτε, ἀποδίδωμι, G591.
- **Dicionário:** “imposto”; “moeda”; “denário”; “imagem”; “inscrição”; “retribuí, devolvei, rendei”.
- **Adotado:** “pagar imposto”, “moeda do imposto”, “um denário”, “imagem” e “inscrição”. Não foram acrescentados o teor da inscrição, metal ou valor atual.
- **22:21:** “Devolvam … as coisas de César … as coisas de Deus” conserva a acepção restitutiva de ἀποδίδωμι e os neutros substantivados, sem definir que bens ou deveres pertencem a cada domínio. “Deem” é alternativa idiomática possível, mas menos explícita quanto à restituição.
- **Morfologia:** τίνος em 22:20 é interrogativo, “de quem”, confirmado na pergunta, não o indefinido que pode aparecer entre candidatos normalizados.
- **Classificação:** contextual / conferência morfológica.

### 22:23–28 — irmãos e descendência

- **Formas/lemas:** ἀνάστασις, G386; ἐπιγαμβρεύσει, ἐπιγαμβρεύω, G1918; ἀναστήσει, ἀνίστημι, G450; σπέρμα, G4690.
- **Dicionário:** “ressurreição”; “se casará, iniciará uma relação matrimonial”; “levantará”; “semente”.
- **Adotado:** “se casará com sua mulher e levantará descendência para seu irmão”. “Descendência” é a acepção familiar da imagem de semente, repetida em 22:25, sem biologizar a comparação nem acrescentar um filho nomeado. “Levantará” conserva o verbo da fórmula, embora “suscitará” seja alternativa portuguesa.
- **22:25–28:** a narrativa hipotética dos saduceus permanece atribuída a eles, com sete irmãos e a morte da mulher depois de todos. “Todos a tiveram” não recebe explicitação de relações sexuais; o contexto matrimonial é mantido pelas orações anteriores.
- **Classificação:** contextual; revisão manual da naturalidade de “levantará descendência”.

### 22:29–33 — engano, casamento e vivos

- **Formas/lemas:** πλανᾶσθε, πλανάω, G4105; δύναμις, G1411; γαμοῦσιν, γαμέω, G1060; ἐκγαμίζονται, ἐκγαμίζω, G1547; ἄγγελοι, ἄγγελος, G32; ζώντων, ζάω, G2198.
- **Dicionário:** “vos enganais”; “poder, milagre”; “casam”; “são dados em casamento”; “mensageiros”, com acepção de anjo; “dos que vivem, viventes”.
- **Adotado:** “Vocês se enganam” é indicativo, não imperativo selecionado por ambiguidade formal. “Poder de Deus” escolhe a acepção de capacidade, não um milagre específico. “Nem se casam nem são dados em casamento” mantém ativa e passiva e não acrescenta sujeitos de gênero distintos que o texto não explicita.
- **Comparação:** “como anjos de Deus no céu” conserva a comparação, sem afirmar que as pessoas se tornam anjos. “Deus de mortos … de vivos” mantém os substantivos derivados dos qualificativos, sem inserir uma definição da condição dos patriarcas.
- **Classificação:** contextual / conferência morfológica.

### 22:34–40 — Lei, amor e dependência

- **Formas/lemas:** νομικός, G3544; ἀγαπήσεις, ἀγαπάω, G25; ψυχή, G5590; διάνοια, G1271; κρέμανται, κρεμάννυμι, G2910.
- **Dicionário:** “jurista, intérprete da lei”; “amarás”; “alma”; “mente”; “estão pendurados, suspensos; dependem”.
- **Adotado:** “intérprete da Lei” não pressupõe um cargo jurídico moderno. “Amarás” conserva o futuro de formulação normativa, como nas citações de Mt 19:18–19, com tratamento tradicional na citação e você/vocês no diálogo.
- **Enumeração:** coração, alma e mente permanecem como três termos distintos, sem acrescentar “força” a partir de outras passagens ou uma teoria das faculdades humanas.
- **22:40:** “dependem toda a Lei e os Profetas” é equivalência idiomática admitida no dicionário para κρέμανται; não se impôs a imagem física de estarem pendurados. “Primeiro e grande” de 22:38 não foi reduzido apenas a “maior”.
- **Classificação:** contextual / consistência editorial.

### 22:41–46 — Cristo, Senhor e estrado

- **Formas/lemas:** χριστός, G5547; ἐν πνεύματι; καλεῖ, καλέω, G2564; κύριος, G2962; ὑποπόδιον, G5286.
- **Dicionário:** “Cristo”; “espírito”; uma busca normalizada pode apresentar o imperativo κάλει, “chama”; “senhor”; “escabelo, estrado para os pés”.
- **Adotado:** “a respeito do Cristo” mantém o título sem explicação adicional. “Em espírito” conserva a expressão, sem acrescentar “Santo” ou uma identificação do processo de inspiração.
- **Morfologia:** καλεῖ em 22:43 e 45 é presente indicativo ativo de 3ª pessoa singular, com Davi como sujeito, confirmado no CSV e na sintaxe; não se aplicou uma glosa imperativa normalizada. “Senhor” é a mesma equivalência de κύριος nos dois lugares da citação; a tradução não substitui um deles por um nome ausente do grego de Mateus.
- **Imagem:** “estrado dos seus pés” conserva o objeto e a parte do corpo, sem converter os inimigos em um grupo contemporâneo ou acrescentar uma cronologia ao “até que”. A pergunta final permanece sem resposta explicativa suprida.
- **22:46:** “ninguém podia … nem … ousou” mantém a distinção entre incapacidade de responder e decisão de não voltar a perguntar.
- **Classificação:** contextual / conferência morfológica.

## Pendências prioritárias

- **22:9, 16, 24:** naturalidade de “saídas dos caminhos”, da formulação de imparcialidade e de “levantará descendência”.
- **22:21, 43–44:** avaliar as escolhas de “devolvam”, “em espírito” e a representação de κύριος, sem inserir interpretação doutrinária no texto principal.
- O capítulo está completo para revisão humana. Nenhuma equivalência nova foi consolidada; a validação estrutural não substitui a avaliação linguística e editorial.
