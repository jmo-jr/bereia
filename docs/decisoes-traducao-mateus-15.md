# Mateus 15 — revisão do rascunho mecânico

- **Estado:** tradução contínua proposta; aprovação editorial pendente.
- **Material de partida:** `reports/traducao/mateus/15/15.txt`, `alinhamento.json` e `decisoes.md`; todos os arquivos dessa pasta foram preservados.
- **Texto-base:** capítulo 15 de `src/interlinear/nt/MT.json`, conferido com `tools/tm_with-parsing/MAT.csv`.
- **Dicionário:** `src/_data/nt/dict_flex_nt-lxx_greek-pt.json`, localização atual do derivado. O protocolo ainda cita o caminho antigo; não foi usada uma cópia histórica.
- **Orientação editorial:** `docs/protocolo-traducao.md`, `docs/decisoes-traducao.md` e estilo do TXT aprovado de Mateus 8. Mateus 14 foi consultado para continuidade, sem pressupor sua aprovação.
- **Entrega:** `src/biblia/nt/mateus/15.txt`. Não foram alterados o dicionário, os demais capítulos ou os rascunhos mecânicos. Não houve chamada à API de geração.

## Conferência textual

- **Títulos e divisões:** mantidos os três títulos e os intervalos das perícopes do JSON, com concordâncias editoriais acrescentadas.
- **15:4:** preservado “Deus ordenou, dizendo”, sem substituir por uma formulação do relato paralelo.
- **15:5–6:** no TM local, a oração sobre não honrar pai ou mãe está no versículo 5. O versículo 6 começa com a anulação do mandamento; a tradução conserva essa distribuição.
- **15:8:** preservada a frase “Este povo se aproxima de mim com sua boca”, além da referência aos lábios e ao coração.
- **15:14:** preservado “guias cegos de cegos”.
- **15:16:** preservado o nome “Jesus”.
- **15:30:** mantida a ordem dos grupos: coxos, cegos, κωφούς, aleijados e muitos outros.
- **15:39:** preservado Μαγδαλά, “Magdala”, sem substituir por outro topônimo.

## Decisões lexicais e sintáticas

Todas as decisões abaixo permanecem com **aprovação editorial pendente**.

### 15:1–3 — tradição, transgressão e lavagem

- **Formas/lemas:** παράδοσιν, παράδοσις, G3862; πρεσβυτέρων, πρεσβύτερος, G4245; παραβαίνουσιν / παραβαίνετε, παραβαίνω, G3845; νίπτονται, νίπτω, G3538.
- **Dicionário:** “tradição”, “dos anciãos”, “transgridem/transgredis”, “se lavam”.
- **Adotado:** “tradição dos anciãos”, “transgridem/transgridem” e “lavam as mãos”. A voz média de νίπτονται exprime o ato sobre as próprias mãos; não se impôs a construção reflexiva “se lavam as mãos”. “Comem pão” conserva ἄρτον sem substituir automaticamente por “fazem refeições”.
- **Tempos:** προσέρχονται em 15:1 permanece presente histórico, “se aproximam”.
- **Classificação:** contextual / consistência lexical.

### 15:4 — falar mal e a fórmula de morte

- **Formas/lemas:** κακολογῶν, κακολογέω, G2551; θανάτῳ τελευτάτω; τελευτάω, G5053.
- **Dicionário:** “difamando, insultando, amaldiçoando, literalmente falando mal”; “à morte”; “termine, morra”.
- **Adotado:** “quem falar mal … seja morto”. A primeira expressão mantém a extensão lexical sem a restringir a uma fórmula de maldição. A segunda verte a fórmula enfática de pena de morte em português legível, em vez da expressão opaca “termine à morte”. O imperativo grego é ativo, “morra”; a passiva portuguesa exprime a execução prescrita pela fórmula, sem acrescentar agente ou procedimento.
- **Classificação:** contextual; revisão manual da expressão “seja morto”.

### 15:5–6 — oferta e obrigação de honrar

- **Formas/lemas:** δῶρον, G1435; ὠφεληθῇς, ὠφελέω, G5623; οὐ μὴ τιμήσῃ, τιμάω, G5091; ἠκυρώσατε, ἀκυρόω, G208.
- **Dicionário:** “oferta”; “sejas beneficiado, recebas proveito, sejas ajudado”; “honre, valorize, reverencie”; “anulastes, invalidastes”.
- **Adotado:** “É oferta aquilo com que você poderia ser beneficiado por mim”; “de modo algum honrará seu pai ou sua mãe”; “anularam o mandamento”. A construção mantém a oferta declarada pelo filho e a anulação atribuída aos interlocutores. Não foram acrescentados “a Deus”, o termo “Corbã” nem uma descrição do sistema de ofertas.
- **Pendência:** οὐ μή com subjuntivo foi mantido como negação enfática de ação futura. No argumento, essa negação pode expressar dispensa da obrigação de prover aos pais. “Não precisará honrar” ou “fica dispensado de honrar” são alternativas contextuais, mas explicitam uma modalidade não verbalizada separadamente no grego. A redação mais literal adotada pode ficar opaca em português.
- **Classificação:** **INCERTO quanto à melhor redação da dispensa de honrar**; decisão humana necessária antes de consolidar a expressão.

### 15:8–9 — boca, lábios e ensinamentos

- **Formas/lemas:** τιμᾷ, τιμάω, G5091; σέβονται, σέβομαι, G4576; διδασκαλίας, διδασκαλία, G1319; ἐντάλματα, ἔνταλμα, G1778.
- **Dicionário:** “honrar”; “adoram, reverenciam, veneram”; “ensinamentos”; “mandamentos”.
- **Adotado:** “me honra”, “me adoram”, “ensinando como ensinamentos mandamentos de pessoas”. “Como” exprime a relação predicativa entre os dois substantivos; não se inseriu um título ou corpo doutrinário externo. A concordância de “sua boca”, “seus lábios” e “seu coração” acompanha o coletivo português “este povo”, sem eliminar partes da citação.
- **Morfologia:** τιμᾷ em 15:8 é presente indicativo de 3ª pessoa singular, não o imperativo τίμα de 15:4. A análise foi conferida pelo CSV e pela oração, não por normalização de diacríticos.
- **Classificação:** contextual / conferência morfológica.

### 15:10–20 — contaminação e compreensão

- **Formas/lemas:** κοινοῖ / κοινοῦντα, κοινόω, G2840; ἐσκανδαλίσθησαν, σκανδαλίζω, G4624; νοεῖτε, νοέω, G3539; χωρεῖ, χωρέω, G5562.
- **Dicionário:** “torna comum, contamina, considera impuro”; “tropeçaram, foram ofendidos, se escandalizaram”; “percebeis, compreendeis”; “cabe, comporta, dá espaço ou lugar”.
- **Adotado:** “contamina” nas recorrências de κοινόω; “tropeçaram” mantém a figura adotada nos capítulos anteriores; “compreendem” em 15:17 é indicativo na pergunta, não imperativo. “Vai para o ventre” escolhe a acepção de deslocamento de χωρέω no contexto da sequência alimentar; a glosa “cabe” não determina sozinha esta ocorrência.
- **Voz:** ἐκβάλλεται é “é expulso”, preservando a passiva e o destino “latrina”. A frase não recebeu a explicação sobre purificação de todos os alimentos de um relato paralelo.
- **Concordância:** os plurais portugueses de 15:18, “as coisas … vêm … contaminam”, acompanham os sujeitos neutros plurais gregos, apesar dos verbos gregos singulares.
- **Classificação:** contextual; revisão manual da naturalidade de “tropeçaram”.

### 15:13–14 — plantação e guias

- **Formas/lemas:** φυτεία, G5451; ἐκριζωθήσεται, ἐκριζόω, G1610; ἄφετε, ἀφίημι, G863; βόθυνον, βόθυνος, G999.
- **Dicionário:** “plantação”; “será desenraizado”; “deixai, perdoai, cancelai, permiti”; “poço”.
- **Adotado:** “plantação … será desenraizada”; “deixem-nos”; “poço”, como em Mt 12:11. Não se identificou a plantação por uma instituição ou grupo adicional à imagem. A acepção de ἀφίημι é deixar, não perdoar.
- **Classificação:** contextual.

### 15:19 — raciocínios, imoralidades e blasfêmias

- **Formas/lemas:** διαλογισμοί, διαλογισμός, G1261; πορνεῖαι, πορνεία, G4202; βλασφημίαι, βλασφημία, G988.
- **Dicionário:** “raciocínios”, “imoralidades”, “blasfêmias”.
- **Adotado:** mantidas essas equivalências e todos os itens da enumeração, sem fundir adultérios e πορνεῖαι. A acepção sexual de “imoralidades” deve ser entendida a partir do lema e deste contexto; “imoralidades sexuais” é alternativa mais explícita. “Blasfêmias” não recebeu objeto acrescentado; “calúnias” é alternativa contextual possível, sem que uma delas seja tratada automaticamente como erro.
- **Classificação:** contextual; revisão manual da extensão de “imoralidades” e “blasfêmias”.

### 15:21–23 — lugares, sofrimento e despedida

- **Formas/lemas:** Σιδῶνος; Χαναναία, G5478; κακῶς, G2560; δαιμονίζεται, δαιμονίζομαι, G1139; ἠρώτων, ἐρωτάω, G2065; ἀπόλυσον, ἀπολύω, G630.
- **Dicionário:** “de Sidom”; “cananéia”; “mal, gravemente, terrivelmente”; “está possuído por um demônio”; “eu pedia; eles pediam, solicitavam, perguntavam”; “libera, despede, manda embora”.
- **Adotado:** “Sidom” segue a forma atual do registro consultado; “Sidon”, usada na proposta de Mt 11, permanece variação editorial a harmonizar após decisão, sem alteração retroativa. “Cananeia” e “Galileia” em 15:29 usam ortografia brasileira atual na tradução, sem modificar as grafias do JSON.
- **Expressão:** “está terrivelmente endemoninhada” conserva κακῶς sem acrescentar a descrição de sintomas. ἠρώτων é 3ª pessoa plural com “discípulos”: “lhe pediam”. “Despeça-a” mantém o pedido sem resolver se esperavam cura prévia ou simples afastamento.
- **Classificação:** contextual / preferência ortográfica / conferência morfológica.

### 15:24–28 — ovelhas, filhos e cachorrinhos

- **Formas/lemas:** ἀπολωλότα, ἀπόλλυμι, G622; προσεκύνησεν, προσκυνέω, G4352; κυνάρια / κυναρίοις, κυνάριον, G2952; κυρίων, κύριος, G2962.
- **Dicionário:** “tendo perecido, estando perdidos”; “se prostrou, reverenciou, adorou”; “cachorrinhos”; “dos senhores”.
- **Adotado:** “ovelhas perdidas da casa de Israel”, como em Mt 10:6; “prostrou-se diante dele”, como em Mt 8:2; “cachorrinhos” nas duas ocorrências e “seus senhores”. O diminutivo é preservado sem comentário sobre tom afetivo ou depreciativo. A comparação não recebe uma identificação explicativa dos filhos e dos cachorrinhos no corpo da tradução.
- **15:27:** “pois também” conserva a ligação de καὶ γάρ; a fala da mulher não foi reformulada como uma refutação explícita.
- **15:28:** “Seja feito a você como quer” mantém a construção de Mt 8:13. ἰάθη é “foi curada”, aoristo passivo; não se substituiu por “salva”. O espaçamento após Ὦ no JSON não motivou correção da fonte grega.
- **Classificação:** contextual / preferência observada.

### 15:29–31 — postura e curas

- **Formas/lemas:** ἐκάθητο, κάθημαι, G2521; κωφούς, κωφός, G2974; κυλλούς, κυλλός, G2948; ἔρριψαν, ῥίπτω, G4496.
- **Dicionário:** “se sentava, residia”; “surdos”; “aleijados”; “lançaram, arremessaram”.
- **Adotado:** “estava sentado” exprime a postura no imperfeito. “Mudos” em 15:30–31 decorre da ação explícita “falando” em 15:31, como na acepção proposta em Mt 9:32–33 e 12:22. Não se acrescentou surdez. “Aleijados” mantém a glosa sem determinar a condição médica ou o membro afetado.
- **Ação:** “os lançaram junto aos pés” conserva a força de ῥίπτω, sem inventar intenção violenta. “Colocaram” é alternativa contextual mais suave, a avaliar; não se adotou por mera preferência estilística.
- **Classificação:** contextual; revisão manual de “lançaram” e da acepção de κωφός.

### 15:32–39 — saciedade e distinção de cestas

- **Formas/lemas:** νήστεις, νῆστις, G3523; ἐκλυθῶσιν, ἐκλύω, G1590; χορτάσαι / ἐχορτάσθησαν, χορτάζω, G5526; εὐχαριστήσας, εὐχαριστέω, G2168; σπυρίδας, σπυρίς, G4711.
- **Dicionário:** “sem comerem, em jejum”; “desmaiem, fiquem cansados”; “alimentar, preencher, satisfazer” / “foram saciados”; “tendo dado graças”; “cestas”.
- **Adotado:** “sem comer”, sem atribuir jejum ritual; “desfaleçam”; “saciar” / “foram saciados”. “Tendo dado graças” mantém o verbo distinto de εὐλόγησεν, “bendisse”, em Mt 14:19; não se harmonizaram as duas formulações.
- **Objetos e elipse:** em 15:36, “partiu e deu” mantém o objeto retomado dos pães e peixes, sem acrescentar uma descrição de distribuição. O segmento “e os discípulos, à multidão” permanece elíptico.
- **Recipientes:** “cestas” distingue σπυρίς dos “cestos” de κόφινος em Mt 14:20, seguindo o dicionário, sem quantificar sua capacidade.
- **15:38:** mantidos quatro mil homens, além de mulheres e crianças; não se acrescentou “cerca de”, ausente nesta contagem, embora presente na de Mt 14:21.
- **Tempos:** preservados os presentes históricos λέγουσιν e λέγει em 15:33–34; ἔφαγον em 15:37 é 3ª pessoa plural com πάντες, sem alterar o registro combinado 1S/3P do dicionário.
- **Classificação:** contextual / consistência lexical.

## Pendências prioritárias

- **15:5:** INCERTO — redação portuguesa da dispensa de honrar, distinguindo a tradução literal da explicitação interpretativa.
- **15:4, 12, 19, 30:** avaliar a naturalidade e a extensão semântica das soluções indicadas acima. Não são correções objetivas do dicionário.
- Nenhuma escolha lexical nova está consolidada. O capítulo está completo para revisão humana; a validação estrutural não certifica por si a fidelidade linguística.
