# Snippet para Criação de Documentos Bíblicos

## Fluxo recomendado para capítulos do NT

Para novos capítulos de tradução, coloque o arquivo diretamente na pasta do livro, por exemplo `src/biblia/nt/mateus/1.md`, `src/biblia/nt/mateus/2.md` ou `src/biblia/nt/mateus/3.liquid`. O Eleventy descobre arquivos `.md` e `.liquid` recursivamente em `src/` e transforma cada arquivo diretamente na página final durante o build; não é preciso criar uma pasta por capítulo nem gerar HTML intermediário em `src/`.

O front matter deve informar `bookName`, `bookAbbrev`, `bookChapter`, `permalink` e `bee`. Use o include de cabeçalho e os shortcodes Liquid `pericope` e `verse`:

```liquid
---
bookName: "Mateus"
bookAbbrev: "mt"
bookChapter: 1
permalink: "/biblia/mateus/1/"
bee: true
---
{% render 'bibleChapterHeader.liquid', bookName: bookName, bookAbbrev: bookAbbrev, bookChapter: bookChapter %}

{% pericope "A Genealogia de Jesus", "Lucas 3:23-38" %}
{% verse bookAbbrev bookChapter 1 %}Livro da origem de Jesus <span class="tooltip" data-tooltip-content="#cristo">Cristo</span>, filho de Davi, filho de Abraão.{% endverse %}
{% endpericope %}
</div>
```

- O título e a concordância são escapados pelo shortcode; o conteúdo do versículo aceita HTML inline confiável, como tooltips, `<cite>` e referências.
- Uma linha em branco entre grupos de shortcodes `verse` inicia outro parágrafo dentro da perícope; sem linha em branco, os versículos ficam no mesmo `<p>`.
- O shortcode `verse` monta o ID no padrão `{abreviação}_{capítulo}-{versículo}` e rejeita números inválidos.
- Compile com `npm run build`. A saída de Mateus 1, por exemplo, fica em `_site/biblia/mateus/1/index.html`.
- A migração é gradual: páginas `.html` e `.liquid` ainda existentes continuam no fluxo atual.

O script `tools/gera_capitulos_html.py` é executado manualmente, separado do build do Eleventy. Ele reconhece `<rl>` como marcação especial; outros shortcodes Liquid ou HTML devem ser escritos diretamente no texto do versículo.

## Gerar capítulos Liquid a partir de texto

O script `tools/gera_capitulos_html.py` agora gera os arquivos `.liquid` que o Eleventy compila. O TXT de entrada usa uma linha por versículo; uma linha em branco começa outro parágrafo e uma linha contendo apenas `--` começa outra perícope:

```text
A purificação do leproso (Lc 5:12-16)
1 Tendo ele descido da montanha, muitas multidões o seguiram.
2 E eis que um leproso, vindo, prostrou-se diante dele.

3 E Jesus, estendendo a mão, o tocou.
--
A fé do centurião
5 Tendo ele entrado em Cafarnaum, aproximou-se dele um centurião.
```

O título e a concordância são separados pelo último par de parênteses da linha do título. A concordância é opcional. Dentro do texto do versículo, `<rl>...</rl>` marca o trecho em vermelho. Os versículos podem ser numerados como `1`, `2` etc. quando se informa `--chapter`, ou como `8:1`, `8:2` para indicar o capítulo em cada linha.

Exemplo para um único capítulo:

```sh
python3 tools/gera_capitulos_html.py entrada.txt --book-name Mateus --book-abbrev mt --chapter 8
```

O resultado será `src/biblia/nt/mateus/8.liquid`, pronto para o build. Se o arquivo já existir, o script interrompe sem sobrescrevê-lo; use `--force` apenas quando quiser substituí-lo. Para várias perícopes/capítulos, a checagem de arquivos existentes é feita antes de qualquer escrita.

## Fluxo legado para páginas ainda não migradas

## Arquivo Template
`SNIPPET-BIBLIA-TEMPLATE.html` - Template base para novos capítulos bíblicos

## Como Usar

1. **Copiar o snippet** como base para um novo arquivo
2. **Substituir os placeholders** com os dados reais:

### Placeholders no Front Matter
- `NOME_DO_LIVRO` → ex: "Mateus", "Hebreus"
- `NUMERO_CAPITULO` → ex: 1, 2, 3
- `LIVRO_MINUSCULO` → ex: "mateus", "hebreus" (usado na URL)

### Placeholders na Estrutura HTML

#### Seção (Perícope)
```html
<h4 class="pericope title">
    TITULO_PERICOPE_1        <!-- ex: "A Genealogia de Jesus" -->
    <small class="pericope concordance">LIVRO_PARALELO CAPITULO:VERSOS</small>
    <!-- ex: "Lucas 3:23-38" -->
</h4>
```

#### Versículo
```html
<span id="PREFIXO_VERSO-NUMERO" class="verse">
    <!-- PREFIXO_VERSO = prefixo do livro (mt, mr, lc, jo, at...)
         NUMERO = número do versículo -->
    <span class="verse-number">NUMERO</span>
    <span class="verse-text">TEXTO_DO_VERSO</span>
</span>
```

## Estrutura de Referências

- **ID do Versículo**: `{prefixo_livro}_{capitulo}-{numero_verso}`
  - Ex: `mt_1-1`, `mt_1-2`, `hebreus_1-1`

- **Referência Cruzada**: 
  ```html
  <sup class="ref tooltip" title="Is 7:14, 8:8-10"> [ref]</sup>
  ```

- **Tooltip para Palavra**:
  ```html
  <span class="tooltip" data-tooltip-content="#id_tooltip">Palavra</span>
  ```

## Exemplo de Conversão

### Template
```html
<span id="mt_1-1" class="verse">
    <span class="verse-number">1</span>
    <span class="verse-text">Livro da origem de Jesus Cristo, filho de Davi, filho de Abraão.</span>
</span>
```

### Múltiplos Versículos no Mesmo Parágrafo
```html
<p>
    <span id="mt_1-2" class="verse">
        <span class="verse-number">2</span>
        <span class="verse-text">Primeiro versículo...</span>
    </span>
    <span id="mt_1-3" class="verse">
        <span class="verse-number">3</span>
        <span class="verse-text">Segundo versículo...</span>
    </span>
</p>
```

## Dicas

- Agrupar versículos em `<p>` de acordo com as pausas naturais do texto
- Cada seção (perícope) tem seu próprio `<h4>` e `<div class="pericope text">`
- Sempre incluir referências cruzadas quando houver paralelos nos Evangelhos
- Manter consistência com os prefixos de livros já usados no projeto
