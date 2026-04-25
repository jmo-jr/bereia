# Snippet para Criação de Documentos Bíblicos

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
