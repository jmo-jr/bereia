# Páginas da LXX

`npm run build` lê os JSONs convertidos de `src/interlinear/at/*.json` e gera
`_site/interlinear/{sigla}/{capitulo}/index.html`, por exemplo
`_site/interlinear/gn/1/index.html`.

- `src/_data/atBooks.json` define a ordem, os nomes, os títulos gregos e os
  permalinks. `src/_data/atBooks.js` associa esses metadados aos livros disponíveis
  e calcula `chapters` e `chapterNumbers` a partir dos JSONs de capítulos.
- `src/_data/atChapterPages.js` prepara os capítulos e consulta o mesmo
  dicionário de formas usado pelo NT, sem modificar os JSONs de origem.
- `src/interlinear/book.liquid` e `book.11tydata.js` fazem a paginação
  compartilhada do AT e do NT no 11ty.
- `src/_includes/interlinearChapter.liquid` contém a apresentação compartilhada
  com o NT. As páginas do interlinear possuem seletor de livros do AT e do NT;
  as páginas de `/biblia/` mantêm somente o NT.

Jó permanece em `jo.json`, mas usa `/interlinear/jó/`, pois `/interlinear/jo/`
pertence a João. Capítulos zero (como o prólogo de Eclesiástico) e referências
de versículos com sufixos são preservados. Os links anterior/próximo da LXX
seguem os capítulos efetivamente presentes, sem apontar além do livro.

Formas sem correspondência no dicionário continuam visíveis em grego, com os
campos lexicais ausentes em branco. Não se infere tradução ou morfologia da
fonte. As contagens apresentadas na LXX usam `ocorrencias_lxx` do dicionário,
quando disponível. A integração não incorpora automaticamente o léxico
separado em `src/_data/lxx`.

Para adicionar livros, coloque os JSONs no mesmo formato nessa pasta e execute
o build. Novos livros devem receber metadados em `atBooks.json`; quando a sigla da URL
  difere do arquivo, informe `id` com o nome do arquivo sem `.json` ou ajuste
  `SOURCE_IDS` em `atBooks.js`. Não é necessário informar `chapters` no JSON.
Os JSONs são acompanhados no modo de desenvolvimento do 11ty.
