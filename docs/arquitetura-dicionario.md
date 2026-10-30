# Dicionário lexical e arquivos derivados

A fonte principal é `src/_data/dict_lex_nt-lxx_greek-pt.json`.
O arquivo `src/_data/dict_flex_nt-lxx_greek-pt.json` é derivado e continua
alimentando os interlineares existentes. Edite a fonte principal, não o derivado.

## Estrutura

Cada chave identifica um Strong exatamente como registrado. Os grupos aparecem
no arquivo em ordem numérica crescente, sem preencher lacunas. Identificadores
com espaços permanecem distintos e próximos ao número correspondente: nenhum
Strong foi corrigido, inferido ou consolidado. O serializador trata explicitamente
a ordem textual, pois JavaScript enumera chaves inteiras antes de outras chaves.

Cada grupo contém:

- `lema` e `transliteracao`: dados lexicais associados pelo Strong exato.
- `pendencias`: presente somente quando há questões registradas no array.
- `verbete`: texto compartilhado pelas flexões, posicionado antes de `flexoes`.
  Nos grupos com variantes, `verbetes` guarda os textos em array e cada flexão
  contém seu próprio `verbete`, por extenso. Nenhuma variante é descartada.
- `flexoes`: um registro por entrada original, incluindo homógrafos e análises
  aparentemente repetidas. Os arrays são a representação completa dos dados.

Cada flexão possui a sequência fixa de campos:

1. `grego`
2. `transliteracao` da forma flexionada
3. `ocorrencias`
4. `traducao`
5. `pt`
6. `abrev_morf`
7. `morfologia`
8. `lxx`
9. `ocorrencias_lxx`

O campo `verbete` também aparece na flexão quando há variantes no grupo.
A transliteração do lema é distinta da transliteração da flexão.
As três flexões sem `ocorrencias_lxx` receberam o valor 0 por autorização
expressa. Os demais campos e valores, incluindo traduções e análises combinadas,
foram preservados sem correções. Não há `_origem`, lista `campos`, posição antiga,
chave de compatibilidade ou `origem_lexical` nos registros.

## Geração e edição

1. Faça backup da fonte lexical antes de editá-la.
2. Edite o grupo lexical ou a flexão correspondente.
3. Execute `npm run dict:generate`.
4. Execute `npm run dict:check` e `npm test`.

Para adicionar uma flexão, preencha os campos fixos no array do Strong correto;
não é preciso cadastrar metadados de origem. Quando o grupo possuir `verbetes`,
informe na flexão o `verbete` correspondente e mantenha-o também na lista do grupo.
O gerador recusa campos de flexão desconhecidos em vez de descartá-los. Novos
campos exigem atualização explícita do esquema em `tools/dictionary/core.js`.

A configuração `.eleventy.js` gera os derivados antes da leitura dos dados e
antes das reconstruções em watch. Isso cobre os comandos build/dev e chamadas
diretas ao Eleventy. Arquivos já atualizados não são regravados; a gravação usa
arquivo temporário e rename. Não há novas dependências externas.

As ferramentas antigas que escrevem no dicionário de flexões não foram convertidas
em editores lexicais. Alterações diretas no derivado serão substituídas na próxima
geração. Essas ferramentas deverão ser adaptadas antes de editar a fonte principal.

## Consultas por forma e homógrafos

O índice `src/_data/dict_form_index_nt-lxx_greek-pt.json` usa exclusivamente `grego`
como chave, sem normalização. Cada valor é um array de referências
`{ "strongs": "3056", "flexao": 0 }`, abrangendo todas as análises da forma.
As chaves antigas, inclusive espaços e caracteres invisíveis, não são reproduzidas.

O formato compatível é um objeto com uma entrada por `grego`. Quando a mesma forma
possui mais de uma análise, a primeira encontrada na enumeração dos grupos e de
suas flexões é usada nessa projeção. As demais análises continuam integralmente
no léxico e no índice. Essa escolha serve apenas à compatibilidade técnica e não
resolve ambiguidades linguísticas. A precedência original não é preservada.

O léxico contém 18.285 registros e o derivado contém 18.277 formas distintas.
Sete formas possuem múltiplos registros: `ἔπεσαν`, `εὗρον`, `ζητήσεις`,
`κακοποιῶν`, `καλῶν`, `οὐ` e `ὢν`. A última possui três registros; as demais, dois.
Não houve eliminação ou fusão de flexões na fonte principal.

O carregador interlinear atual permanece inalterado, inclusive sua normalização.
A substituição das 31 chaves diferentes de `grego` e a nova precedência alteram
os dados associados a 143 tokens do NT. Referências e valores antes/depois estão
em `tools/dictionary/simplification.json`. Em Mateus 8 não há tokens alterados;
o HTML continua idêntico byte a byte ao gerado com o dicionário original.
A revisão futura do carregador e de sua normalização é uma atividade separada.

## Procedência e auditoria

Os lemas e suas transliterações foram copiados por correspondência exata de
Strong de `src/_data/archive/strongsg.js`, lido como JSON, sem executar seu código.
A procedência é registrada aqui e o hash da fonte está no manifesto
`tools/dictionary/baseline.json`, sem repetição em cada verbete.

Há 5.481 grupos Strong literais, 5.370 lemas distintos resolvidos e 833 pares
distintos de código/descrição morfológica. As 136 flexões com espaços no Strong
permanecem com identificação lexical pendente, sem associação pelo valor aparado.

O backup original integral está em
`tools/backups/dictionary-migration/dict_flex_nt-lxx_greek-pt.json`.
A versão anterior à simplificação e seus scripts, testes e documentação estão em
`tools/backups/dictionary-simplification-20261030T211435Z/`.
`tools/dictionary/migrate.js` reproduz a migração no esquema simplificado e recusa
sobrescrever uma fonte já existente. Não é um comando de atualização cotidiana.

Os testes verificam os hashes de referência e comparam multiconjuntos de registros
completos, independentemente da ordem, preservando multiplicidade. A comparação
aceita apenas as alterações autorizadas: abandonar as chaves antigas e preencher
os três campos LXX ausentes. Também verifica campos fixos, homógrafos, variantes
de verbete, metadados lexicais e todas as referências do índice.

Um oráculo independente gera a projeção esperada a partir do backup. Todos os
tokens enriquecidos são comparados com esse resultado, e as diferenças em relação
ao carregamento antigo são auditadas no relatório da simplificação. Três builds
Eleventy isolados comparam Mateus 8: original, projeção independente e geração real.
Nenhum teste escreve em `_site` ou no log do repositório.

Essas comparações documentam a migração e sua simplificação. Futuras revisões
linguísticas deliberadas serão sinalizadas contra a referência. Não altere o
backup nem seus hashes apenas para fazer testes passarem; documente separadamente
as diferenças autorizadas e adapte a auditoria mantendo o histórico original.
