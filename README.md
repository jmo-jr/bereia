# Bíblia Interlinear Grego-Português 

Baseado no **Texto Majoritário**, com destaque para a *Família 35*

## Projeto baseado em 11ty

**Compile:** `eleventy`

**Run:** `npx @11ty/eleventy`

**Serve:** `npx @11ty/eleventy --serve`

## Regex para pesquisa de expressões:

Caracteres especiais devem ser acrescentados após a vírgula

> \b[\w\s\[\],]+

## Auxílios para tradução:

Glifos: ē, ō

- Aoristo Indicativo = Pretérito Perfeito Simples (eles foram)
- Dativo = (indireto) a, para; (instrumento) com, por meio de; (lugar) em, sobre
- Vocativo = Mestre!
- Genitivo = do
- Nominativo = A pesoa ...
- Acusativo = ... a coisa
- Particípio passivo = tendo visto, tendo sido visto
- Particípio ativo = Gerúndio (vendo)

## Templates para páginas
---
bookName: ""
bookChapter: 0
---
{% render '../../_includes/pageHeader', bookName: bookName, bookChapter: bookChapter %}

{% render '../../_includes/sideNav', bookName; bookName, bookChapter: bookChapter%}