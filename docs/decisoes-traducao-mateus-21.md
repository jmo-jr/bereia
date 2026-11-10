# Mateus 21 — revisão do rascunho mecânico

- **Estado:** tradução contínua proposta; aprovação editorial pendente.
- **Material de partida:** `reports/traducao/mateus/21/21.txt`, `alinhamento.json` e `decisoes.md`; todos os arquivos da pasta foram preservados.
- **Texto-base:** capítulo 21 de `src/interlinear/nt/MT.json`, conferido com `tools/tmnt/with-parsing/MAT.csv`.
- **Dicionário:** `src/_data/nt/dict_flex_nt-lxx_greek-pt.json`, localização atual do derivado, sem uso de cópias históricas.
- **Orientação:** `docs/protocolo-traducao.md`, `docs/decisoes-traducao.md` e estilo do TXT aprovado de Mateus 8. As escolhas de capítulos propostos não são automaticamente consolidadas.
- **Entrega:** `src/biblia/nt/mateus/21.txt`. Não foram alterados dicionários, capítulos anteriores ou rascunhos mecânicos. Não houve chamada à API de geração.
- **Atualização paralela das fontes:** durante esta revisão, outra atividade atualizou o léxico e os derivados. As alterações foram preservadas. A reconferência dos grupos de formas presentes em Mateus 21 não encontrou mudança de equivalências portuguesas, Strong ou análises morfológicas por grupo normalizado; as mudanças gráficas de chaves não exigiram alteração da tradução. A normalização serviu somente à comparação das fontes, não à seleção automática de uma análise para cada ocorrência.

## Conferência textual

- Mantidos os seis títulos e intervalos do JSON; acrescentadas concordâncias editoriais.
- **21:3:** preservado o presente ἀποστέλλει, “envia”; não foi substituído por uma leitura com devolução dos animais.
- **21:4:** preservado ὅλον, “tudo”, na fórmula de cumprimento.
- **21:7:** mantidos os dois animais e os dois pronomes de “sobre eles”. Não se harmonizou o relato com uma versão de um só animal.
- **21:12:** preservado “templo de Deus”.
- **21:28–31:** mantida a ordem do TM local: o primeiro recusa e depois vai; o segundo concorda e não vai; a resposta é “o primeiro”.
- **21:44:** versículo integralmente preservado.
- **21:45:** respeitados “sumos sacerdotes e fariseus”, distintos dos “sumos sacerdotes e anciãos” de 21:23.

## Decisões lexicais e sintáticas

Todas as escolhas têm **aprovação editorial pendente**.

### 21:1–7 — animais, envio e pronomes

- **Formas/lemas:** ὄνον, ὄνος, G3688; πῶλον, πῶλος, G4454; δεδεμένην, δέω, G1210; ἀποστέλλει, ἀποστέλλω, G649; ἐπεκάθισεν, ἐπικαθίζω, G1940.
- **Dicionário:** ὄνος pode aparecer como “asno”; πῶλος: “jumentinho”; “tendo sido amarrada”; “envia”; “se sentou”.
- **Adotado:** “jumenta” em 21:2 e 7 observa os determinantes e a concordância feminina do TM, não o gênero isolado da glosa. “Tendo-os soltado, tragam-nos” conserva o plural referente aos dois animais. Na citação de 21:5, “jumenta” mantém a referência narrativa; a forma ὄνον isolada nessa citação não distingue os gêneros.
- **21:3:** “O Senhor tem necessidade deles; e imediatamente ele os envia” conserva a ordem, o presente e o sujeito não explicitado por nome. A pontuação deixa a última oração fora da resposta citada dos discípulos, como previsão de Jesus; a delimitação da fala e a identidade desse sujeito ficam para revisão manual.
- **21:7:** “colocaram sobre eles seus mantos, e ele se sentou sobre eles” não substitui o último pronome por “mantos” ou por um animal. O CSV identifica o primeiro referente como masculino plural e o último como neutro plural; o neutro favorece os mantos na análise fornecida, mas a forma grega αὐτῶν por si é comum aos gêneros. A conclusão não é imposta por uma explicitação no texto.
- **Classificação:** contextual; **INCERTO quanto à melhor redação que preserve a referência pronominal em 21:3 e 7**.

### 21:5, 8–11 — mansidão, mantos e Hosana

- **Formas/lemas:** πραΰς, G4239; ἱμάτια, ἱμάτιον, G2440; πλεῖστος, G4118; ὡσαννά, G5614; ὑψίστοις, ὕψιστος, G5310; ἐσείσθη, σείω, G4579.
- **Dicionário:** “manso”; “mantos”; “muito grande”; “Hosana”; “altíssimos”; “foi agitado, sacudido, tremeu”.
- **Adotado:** “manso” e “mantos” mantêm as equivalências anteriores. “A maior parte da multidão” é leitura quantitativa do superlativo; “uma multidão muito grande” é alternativa aceitável, a avaliar. A concordância verbal portuguesa acompanha o coletivo singular; os verbos de cortar e estender ramos permanecem no imperfeito.
- **Aclamação:** “Hosana … nas alturas” conserva a transliteração e a locução espacial, sem acrescentar uma tradução etimológica ou identificar os locais celestes. “Toda a cidade foi agitada” mantém a passiva e a personificação; não se introduziu um terremoto físico.
- **Classificação:** contextual; revisão manual da nuance de πλεῖστος.

### 21:12–17 — templo, meninos e louvor

- **Formas/lemas:** ἱερόν, G2411; λῃστῶν, λῃστής, G3027; παῖδας, παῖς, G3816; νηπίων, νήπιος, G3516; θηλαζόντων, θηλάζω, G2337; κατηρτίσω, καταρτίζω, G2675.
- **Dicionário:** “templo”; “saqueadores”; “meninos, servos”; “infantis, crianças”; “amamentando, mamando”; “restauraste, equipaste, aperfeiçoaste, preparaste”.
- **Adotado:** “templo” sem reduzir ἱερόν a um recinto mais específico. “Caverna de saqueadores” conserva a imagem e a glosa, sem substituir obrigatoriamente por “covil de ladrões”. “Meninos” escolhe a acepção de παῖς apropriada à cena, em vez de “servos”.
- **Citação:** “Da boca de crianças e dos que mamam preparaste louvor” distingue o particípio dos que mamam da ação de amamentar realizada por outra pessoa. “Preparaste” é alternativa presente no dicionário; “aperfeiçoaste” também é aceitável. A citação conserva a 2ª pessoa singular sem convertê-la em explicação da própria narração.
- **Morfologia:** εἰσῆλθεν em 21:12 é indicativo ativo de 3ª pessoa singular, “entrou”, conforme o CSV e o sujeito Jesus, sem reproduzir “entraste” da consulta lexical.
- **Classificação:** contextual / conferência morfológica.

### 21:18–22 — figueira, permanência e fé

- **Formas/lemas:** ἐπανάγων, ἐπανάγω, G1877; εἰς τὸν αἰῶνα; ἐξηράνθη, ξηραίνω, G3583; διακριθῆτε, διακρίνω, G1252; ἄρθητι, αἴρω, G142; βλήθητι, βάλλω, G906.
- **Dicionário:** “retornando”; αἰών: “era, eternidade”; “secou”; “duvideis, hesiteis”; “sê erguido”; “sê lançado”.
- **Adotado:** “voltando”; “Nunca mais venha de você fruto, para sempre” mantém tanto μηκέτι quanto a expressão de duração. Essa redação é literal e pode merecer ajuste de naturalidade; não se inseriu uma limitação sazonal.
- **21:21:** “[foi feito]” explicita o conteúdo elíptico de τὸ τῆς συκῆς, sem atribuir a fala a outro agente. “Seja erguida e lançada” mantém as duas passivas imperativas dirigidas à montanha; a concordância é feminina em português.
- **Limite:** a promessa de 21:22 permanece sem condições ou explicações adicionadas; não se harmonizou a sequência temporal da figueira com Marcos.
- **Classificação:** contextual; revisão manual de 21:19 e da explicitação em 21:21.

### 21:23–27 — autoridade e imersão de João

- **Formas/lemas:** ἐξουσία, G1849; ἐρωτήσω, ἐρωτάω, G2065; λόγον ἕνα; βάπτισμα, G908; διαλογίζομαι, G1260.
- **Dicionário:** “autoridade”; ἐρωτήσω pode receber glosa subjuntiva; λόγος admite palavra/declaração; βάπτισμα: “batismo”, com “imersão” no verbete; “refletir, debater”.
- **Adotado:** “farei … uma pergunta” e “se me responderem” vertem a locução de pergunta/resposta, sem forçar “perguntarei uma palavra”. O CSV confirma futuro indicativo de ἐρωτήσω nesta oração.
- **Imagem lexical:** “imersão de João” mantém a preferência documentada por imergir e a solução nominal proposta em Mt 20:22–23. Aqui o contexto é a origem da prática de João, sem substituir a pergunta por um resumo de todo o seu ministério.
- **Diálogo:** “discutiam entre si” é a acepção de deliberação conjunta. A condição “se dissermos … das pessoas” permanece sem uma consequência verbal acrescentada antes de “tememos a multidão”. “Todos têm João como profeta” não foi convertido em afirmação independente do narrador sobre a opinião de cada indivíduo.
- **Classificação:** contextual / conferência morfológica.

### 21:28–32 — mudar de ideia e ir adiante

- **Formas/lemas:** μεταμεληθείς / μετεμελήθητε, μεταμέλομαι, G3338; ἐγώ, κύριε; τελώνης, G5057; προάγω, G4254; δικαιοσύνη, G1343.
- **Dicionário:** “arrependido, mudado de ideia”; “eu, senhor”; “cobrador de impostos”, com “arrecadador” no verbete; “preceder, ir adiante”; “justiça”.
- **Adotado:** “tendo mudado de ideia” / “mudaram de ideia” conserva o mesmo lema, sem impor identidade total com μετανοέω, traduzido por arrepender-se em Mt 11. “[Vou]” explicita o verbo elíptico na concordância do segundo filho, mantendo “eu” e “senhor”.
- **Vocabulário:** “arrecadadores” mantém o termo já usado nos capítulos anteriores; “prostitutas” não é substituído por uma generalização de pecado. “Vão adiante de vocês para o Reino de Deus” conserva o presente e a imagem de precedência, sem acrescentar uma declaração de exclusão definitiva dos interlocutores.
- **21:32:** “caminho da justiça” mantém a figura; “para crer nele” expressa o infinitivo articulado de resultado/finalidade, sem definir uma teoria do arrependimento.
- **Classificação:** contextual; revisão manual de “[vou]”.

### 21:33–41 — agricultores, frutos e arrendamento

- **Formas/lemas:** ἀμπελών, G290; γεωργός, G1092; ἐξέδοτο / ἐκδώσεται, ἐκδίδωμι, G1554; καρπός, G2590; δοῦλος, G1401; κακοὺς κακῶς ἀπολέσει.
- **Dicionário:** “vinhedo”; “agricultor”; “cedeu, concedeu, entregou”; “fruto”; “escravo”; “maus”, “terrivelmente”, e glosas de destruir/perder.
- **Adotado:** “vinhedo” e “agricultores” no corpo, conservando o título editorial “lavradores maus”. “Arrendou/arrendará” é a acepção contextual da entrega para exploração com prestação de frutos, sem acrescentar um contrato ou valor. “Seus frutos” mantém o possessivo sem explicitar uma porcentagem.
- **21:35–39:** conservadas as ações contra os escravos e, depois, a sequência de lançar o filho para fora e matá-lo. O filho é enviado após os escravos; sua identificação fora da parábola não foi inserida no relato.
- **21:41:** “Destruirá terrivelmente esses maus” preserva adjetivo e advérbio cognatos em sentido, embora a figura sonora grega não seja reproduzida. ἀπολέσει é futuro indicativo conforme o CSV e a pergunta/resposta, sem aplicar a abreviatura subjuntiva de um registro lexical. “Nos seus tempos” não recebe uma cronologia adicional.
- **Classificação:** contextual / conferência morfológica.

### 21:42–46 — pedra e nação

- **Formas/lemas:** κεφαλὴν γωνίας; κεφαλή, G2776; γωνία, G1137; ἔθνει, ἔθνος, G1484; συνθλασθήσεται, συνθλάω, G4917; λικμήσει, λικμάω, G3039.
- **Dicionário:** “cabeça”; “esquina, pedra angular”; “nação”; “será esmagado, quebrado em pedaços”; “joeirará, esmagará, espalhará”.
- **Adotado:** “pedra principal da esquina” exprime a metáfora arquitetônica de κεφαλή, evitando a expressão opaca “cabeça da esquina”; “pedra angular” é alternativa aceitável. Não se definiu sua posição exata na estrutura nem se trocou o texto por explicação cristológica.
- **21:43:** “uma nação que produza seus frutos” mantém o singular e a relação com os frutos do Reino. A nação não é identificada explicitamente como um povo moderno, os gentios em bloco ou uma instituição; isso seria comentário interpretativo.
- **21:44:** “será quebrado em pedaços” / “ela o esmagará” preserva a distinção entre os dois verbos e a passagem da passiva à ativa. Não se acrescentou uma definição do juízo simbolizado.
- **21:45–46:** a compreensão de que as parábolas se referiam aos líderes permanece atribuída aos próprios ouvintes. “Procurando prendê-lo” escolhe a acepção de apreensão de κρατέω na cena, sem antecipar uma prisão consumada.
- **Classificação:** contextual; revisão manual da expressão arquitetônica.

## Pendências prioritárias

- **21:3, 7:** delimitação da fala e referências pronominais sem harmonização dos animais.
- **21:19–21, 30:** naturalidade da fala à figueira e das explicitações marcadas.
- **21:42–43:** expressão arquitetônica e preservação do grau de identificação da “nação”.
- O capítulo está completo para revisão humana. Nenhuma equivalência nova foi consolidada; validação estrutural não certifica por si fidelidade linguística.
