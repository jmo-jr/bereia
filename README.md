# Bíblia Interlinear Grego-Português 

Baseado no **Texto Majoritário**, com destaque para a *Família 35*

## Projeto baseado em 11ty

**Compile:** `eleventy`

**Run:** `npx @11ty/eleventy`

**Serve:** `npx @11ty/eleventy --serve`

## Regex para pesquisa de expressões:

Caracteres especiais devem ser acrescentados após a vírgula

`\b[\w\s\[\],]+` (\b = limite de palavra; \w = letra; \s = espaço; \ = escapa carac. espec.; + = um ou mais)

Substituir os links das definições em grego do Bibleapps.com:

Find: `/greek/(\d{1,4})\.htm`

Replace: `https://bibleapps-com.translate.goog/strongs/greek/$1.htm?_x_tr_sl=en&_x_tr_tl=pt&_x_tr_hl=pt-BR&_x_tr_pto=wapp`

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

### Declinações do artigo definido

|  				| ACUSATIVO | NOMINATIVO | DATIVO | GENITIVO |
|----------|----------|----------|----------|----------|
| Masculino  | τὸν, τοὺς | ὁ, οἱ | τῷ, τοῖς | τοῦ, τῶν |
| Feminino  | τὴν, τὰς | ἡ, αἱ | τῇ, ταῖς | τῆς, τῶν |
| Neutro  | τὸ, τὰ | τὸ, τὰ | τῷ, τοῖς | τοῦ, τῶν |

## Templates para páginas

``` 
---
bookName: "Mateus"
bookChapter: 1
---
```

`{% render '../../_includes/pageHeader', bookName: bookName, bookChapter: bookChapter %}`

`{% render '../../_includes/sideNav', theBookName: bookName, theBookChapter: bookChapter %}`