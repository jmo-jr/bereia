# Dicionário lexical e arquivos derivados

A fonte principal é `src/_data/dict_lex_nt-lxx_greek-pt.json`.
O arquivo `src/_data/dict_flex_nt-lxx_greek-pt.json` é derivado e continua
alimentando os interlineares existentes. Não edite diretamente o derivado.

## Estrutura

Cada chave identifica um Strong exatamente como estava registrado na origem.
Os grupos aparecem no arquivo em ordem numérica crescente, sem preencher lacunas.
Identificadores com espaços permanecem distintos, junto ao número correspondente;
nenhum Strong foi corrigido, atribuído por semelhança ou consolidado.
Leitores JavaScript podem enumerar chaves inteiras antes das chaves com espaços;
o serializador lexical trata explicitamente a ordem textual.

Cada grupo contém:

- `lema` e `transliteracao`: dados lexicais copiados por correspondência exata
  de Strong de `src/_data/archive/strongsg.js`, com procedência em `origem_lexical`.
  São metadados acrescentados; não substituem nenhum valor do dicionário original.
  Esse arquivo arquivado é lido como JSON na migração, sem executar JavaScript.
- `pendencias`: questões de identificação lexical ou transliteração ausente.
  Um valor `null` não autoriza inferir o dado a partir da flexão.
- `verbete`: verbete original quando todas as flexões do grupo o compartilham.
  Havendo variantes, `verbetes` guarda todas elas em array e cada flexão aponta
  para seu índice em `_origem.verbete`. Nenhuma variante foi escolhida como principal.
- `flexoes`: array com um registro por entrada original, inclusive homógrafos
  e análises aparentemente repetidas.

Cada flexão preserva `grego`, `transliteracao` da forma flexionada, `ocorrencias`,
`traducao`, `pt`, `abrev_morf`, `morfologia`, `lxx` e, quando originalmente presente,
`ocorrencias_lxx`. Campos futuros também são transportados sem uma lista fixa.
Não se confundem transliteração do lema e transliteração da flexão.

`_origem` registra a chave original (`chave`), a posição global (`ordem`),
a sequência de campos (`campos`) e, quando necessário, o índice do verbete.
Esses metadados permitem reconstruir a estrutura e a ordem antigas mesmo que
os grupos lexicais e seus arrays sejam reordenados. A chave original pode diferir
de `grego`, inclusive por caracteres invisíveis: não a substitua automaticamente.

As análises combinadas permanecem nas strings originais. A migração não as
divide, corrige ou interpreta e não escolhe uma leitura contextual.

## Atualização

1. Faça backup da fonte lexical antes de editá-la.
2. Edite os dados lexicais ou a flexão correspondente na fonte principal.
3. Execute `npm run dict:generate`.
4. Execute `npm run dict:check` para verificar os derivados.
5. Execute `npm test` para auditar a preservação da migração e os interlineares.

Ao adicionar uma flexão, forneça uma chave original única, uma posição `ordem`
inteira não utilizada e `campos` com todos os campos que o derivado deverá conter,
incluindo `strongs` e `verbete`. Preserve a distinção entre campo ausente, vazio
e zero. Não reutilize a mesma chave para duas análises: o formato compatível é
um objeto e não suporta chaves repetidas. O gerador recusa essa perda de dados.

Os scripts antigos de revisão/contagem que escrevem no formato de flexões não
foram convertidos em editores da fonte lexical. Não os execute sobre o derivado
esperando persistência: a geração seguinte o reconstruirá. Adaptações desses
editores devem ser feitas separadamente, preservando os metadados de origem.

A configuração `.eleventy.js` gera os derivados antes da leitura dos dados e
novamente antes das reconstruções em watch. Isso cobre `npm run build`,
`npm run dev`, `npm run dev:full` e chamadas diretas ao Eleventy. Arquivos que
já estão corretos não são regravados. A gravação usa arquivo temporário e rename.

## Índice de formas

`src/_data/dict_form_index_nt-lxx_greek-pt.json` é derivado. Suas chaves são
formas exatas, sem normalização, e seus valores são arrays de referências
`{ "strongs": "3056", "flexao": 0 }`. O índice inclui tanto a chave original
quanto `grego`, sem repetir uma referência quando ambos coincidem.
Ele preserva todas as correspondências; não decide qual homógrafo usar.
Os interlineares atuais continuam usando seu índice anterior, inclusive sua
regra de primeira correspondência após normalização.

## Auditoria da migração

O backup integral está em
`tools/backups/dictionary-migration/dict_flex_nt-lxx_greek-pt.json`.
O manifesto `tools/dictionary/baseline.json` registra hashes e contagens.
`tools/dictionary/migrate.js` documenta a transformação inicial e recusa
sobrescrever uma fonte lexical existente. Ele não é um comando de atualização.

A migração preserva 18.285 entradas, 18.277 formas em `grego`, 5.481 grupos
Strong literais e 833 pares distintos de código/descrição morfológica.
Há 5.370 lemas distintos resolvidos por associação exata à fonte arquivada.
As 136 flexões cujos Strong contêm espaços permanecem com lema pendente;
não foram associadas pelo identificador aparado. A quantidade de lemas reais
dessas pendências não pode ser deduzida com segurança dessa contagem.

Os testes comparam multiconjuntos de registros completos, incluindo as chaves,
independentemente da ordem dos objetos JSON. Também conferem multiplicidade,
ordem de compatibilidade, campos ausentes, homógrafos, análises combinadas,
formatação original e hashes do backup. Um teste adicional compara todos os
tokens enriquecidos pelo carregador de produção. Duas execuções reais do
Eleventy em diretório temporário comparam o HTML de Mateus 8 byte a byte;
nenhuma tolerância de formatação foi necessária.

Esses testes são uma auditoria congelada da migração: alterações de conteúdo
posteriores e intencionais serão sinalizadas contra o backup. Não atualize o
backup ou seus hashes para apenas fazer os testes passarem. Uma futura revisão
linguística deverá documentar separadamente as diferenças autorizadas e adaptar
a auditoria de comparação, mantendo intacta a referência original.
