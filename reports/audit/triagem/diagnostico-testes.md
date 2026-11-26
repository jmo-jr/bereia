# Diagnóstico dos testes existentes

Execução registrada: 4 testes passaram; 5 falharam.

## integrity.test.js

Fonte histórica ausente, lida no topo do módulo; demais verificações desse arquivo nem chegam a executar.

Evidência: {"arquivo":"src/_data/archive/strongsg.js","existe":false,"sha256_esperado":"559229da5a0e85b860d70a31ae55957283ce17f927005eadc989afd23369a5b0","historico_git":{"recuperavel":true,"commit":"cc3b9c7029a69398c2b71b0d85daa8717174a160","caminho":"src/_data/archive/strongsg.js","sha256":"559229da5a0e85b860d70a31ae55957283ce17f927005eadc989afd23369a5b0","bytes":1308532}}

Proposta: Fonte original recuperável em memória pelo Git quando historico_git.recuperavel=true. Restaurar somente na etapa de manutenção autorizada; não fabricar substituto nem alterar baseline.

## interlinear.test.js: diferenças históricas

Reexecução com o TM atual diverge do relatório histórico congelado.

Evidência: {"diferencas_recalculadas":144,"diferencas_historicas":143,"adicionais":[{"livro":"JO","capitulo":21,"versiculo":10,"posicao":9,"forma":"ὧν","campos":{"strongs":{"antes":"3739","depois":null},"grego":{"antes":"ὢν","depois":null},"transliteracao":{"antes":"hōn","depois":null},"verbete":{"antes":"G3739: quem, qual, o que, que","depois":null},"ocorrencias":{"antes":"78","depois":null},"traducao":{"antes":"das quais, dos quais, das que, dos que","depois":null},"pt":{"antes":"das quais","depois":null},"morfologia":{"antes":"Pronome Relativo - Genitivo Neutro Plural","depois":null},"abrev_morf":{"antes":"RelPro-GNP","depois":null}}}],"ausentes_ou_modificadas":[]}

Proposta: Preservar o histórico. Na futura manutenção dos testes, reproduzir com o snapshot original do TM e testar o estado atual separadamente; não atualizar simplification.json para fazer passar.

## interlinear.test.js: Eleventy

Processo de renderização atingiu o limite de heap do Node, segundo o log da execução.

Evidência: {"heap_esgotado_no_log":true,"script_build":"env NODE_OPTIONS=--max-old-space-size=4096 NODE_ENV=production npx eleventy --incremental","limite_configurado_no_teste":"O spawn herda process.env e não define heap próprio; o comando npm test não inclui o limite de 4096 do build."}

Proposta: Isolar o caso de Mateus 8 com dependências mínimas e orçamento de memória explícito. Não repetir quatro builds integrais para validar a consulta lexical.

## lxx-pages.test.js: título

Texto esperado no teste não coincide com o título atual; o título móvel antigo está comentado.

Evidência: {"expectativa_presente":false,"titulos_atuais":["AT Grego (LXX) Interlinear Analítico"]}

Proposta: Revisar o contrato do título e testar o elemento ativo. Não modificar a interface só para satisfazer texto histórico.

## lxx-pages.test.js: navegação

Teste espera null no limite do livro; implementação aponta para o índice com #/.

Evidência: {"usa_indice_no_limite":true,"expectativa":null,"exemplo_atual":"/interlinear/gn/#/"}

Proposta: Definir o contrato de navegação separadamente da auditoria lexical. Verificar se #/ é destino válido antes de propor uma correção.

Diagnóstico somente leitura. Nenhum teste, baseline, relatório histórico ou arquivo de produção alterado.
