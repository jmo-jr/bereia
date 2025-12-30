# Copilot / AI Agent Guide — Bereia (Resumo curto)

Objetivo: permitir que um agente seja imediatamente produtivo no repositório, com comandos exatos, padrões de dados e arquivos de referência.

## Arquitetura em alto nível 🔧
- Site estático gerado por **Eleventy (11ty)**. Código fonte em `src/`; build em `_site/`.
- Dados importantes estão em `src/_data/` (ex.: `nt_greek-pt_dict.json`, `greeknt_dict.json`, `strongsg.js`). Muitos scripts editam esses arquivos.
- Templates Liquid (`.liquid`) em `src/_includes/` e páginas em `src/nt/*` (cada capítulo como página).
- Busca: Pagefind é executado automaticamente após o build via `.eleventy.js` (gera `_site/biblia/pagefind`).
- Servidor local custom: `server.js` — serve `_site/` em `http://localhost:8080` e remove o prefixo `/bereia/` (importante para reproduzir comportamento em produção).

## Comandos de desenvolvimento e build ✅
- Instalar dependências: `npm install`
- Build para produção (usa path prefix): `npm run build`  (executa `npx eleventy --pathprefix 'bereia'`)
- Desenvolver com live-server do Eleventy: `npm run dev` (usa `--serve`).
- Servir com correção do prefixo (modo dev com server.js): `npm run dev:full` — executa Eleventy `--serve` e `node server.js` em paralelo. Use este quando testar URLs que incluem `/bereia/`.
- Servir apenas o servidor estático (útil após `npm run build`): `npm run serve` (executa `node server.js` em `PORT=8080`).

OBS: muitos builds podem precisar de mais memória — os scripts já usam `NODE_OPTIONS=--max-old-space-size=4096`.

## Padrões e convenções do projeto 📁
- Templates usam front matter com `bookName` e `bookChapter`:
  ```yaml
  ---
  bookName: "Mateus"
  bookChapter: 1
  ---
  ```
  Inclusões comuns:
  - `{% render './_includes/bookNav', bookName: bookName, bookChapter: bookChapter %}`
  - `{% render './_includes/sideNav', theBookName: bookName, theBookChapter: bookChapter %}`

- Eleventy config (`.eleventy.js`):
  - `pathPrefix: "/bereia/"` — o build assume esse prefixo em produção.
  - `eleventyConfig.addPassthroughCopy('src/assets')`, `src/css`, `src/img`.
  - Pagefind é invocado com: `npx pagefind --site _site/biblia --output-subdir pagefind --glob "**/*.html"`.

- Dados JSON grandes:
  - `src/_data/nt_greek-pt_dict.json` é muito grande — evite cargas desnecessárias em runtime; use scripts que processem por streaming ou rodem offline.
  - Quando scripts escrevem JSON, o projeto geralmente usa tab (`"\t"`) como indentação (ver `tools/update_greeknt_translations.js`).
  - Ordem preferencial de chaves nas entradas JSON: ver `ENTRY_KEY_ORDER` em `tools/flexiona_verbos.py`.

## Scripts de manutenção e atualização (exemplos) 🔄
- Atualizar traduções / verbetes de Strong: `node tools/update_greeknt_translations.js` (altera `src/_data/greeknt_dict.json` lendo `src/_data/strongsg.js`).
- Gerar flexões em PT para verbos: `python3 tools/flexiona_verbos.py --input src/_data/nt_greek-pt_dict.json` (script contém documentação no topo explicar flags e `--strong` para alvo único).
- Atualizar transliteração interlinear: `python3 tools/update_interlinear_translit.py` (ver script para flags/uso).

Nota: esses scripts alteram arquivos em `src/_data/` — revise diff antes de commitar.

## Arquivos que merecem atenção para alterações de dados ✍️
- `src/_data/nt_greek-pt_dict.json` — dicionário principal (morfologia, traduções, transliteração).
- `src/_data/greeknt_dict.json`, `src/_data/strongsg.js` — fonte de definições Strong e sinônimos.
- `src/nt/*` e `html-srcs/nt/` — conteúdo por livro/capítulo; qualquer alteração de estrutura de dados pode afetar templates.

## Debug e problemas comuns 🐞
- Erros por memória durante build: aumentar `NODE_OPTIONS=--max-old-space-size=4096` (já usado nos scripts de `package.json`).
- Índice de busca (Pagefind) não atualizado: execute `npm run build` (Pagefind é chamado automaticamente no hook `eleventy.after`).
- URL 404s em ambiente local quando a hospedagem usa `/bereia/`: use `npm run dev:full` (eleventy serve + `server.js`) ou `npm run build` + `npm run serve`.

## Regras práticas úteis para agentes 🤖 (curtas e acionáveis)
- Antes de alterar dados massivos (ex.: `nt_greek-pt_dict.json`), rode os scripts localmente e verifique diffs (`git diff`).
- Use `npm run dev:full` para testar navegação com prefixo `/bereia/` e `http://localhost:8080`.
- Quando adicionar campos a dicionários, siga a ordem e indentação existentes; scripts Python/Javascript dependem de chaves específicas (`strongs`, `grego`, `traducao`, `pt`).
- Não altere manualmente `src/_data/strongsg.js` sem validar o formato — `tools/update_greeknt_translations.js` procura a âncora `var strongsGreekDictionary`.

## Onde procurar mais contexto 🔎
- Layouts e includes: `src/_includes/` e `src/_data/` — padrão das páginas e dados.
- Hooks de build: `.eleventy.js` (pagefind, passthroughs, pathPrefix).
- Scripts auxiliares: `tools/` (Python e JS) — cada script tem uso documentado no topo.
- Servidor local: `server.js` (porta 8080, tratamento do prefixo `/bereia/`).

---
Se quiser, eu posso condensar isso em uma versão ainda mais curta (para leitura rápida) ou expandir com exemplos de PRs comuns e checagens automáticas. Deseja que eu já crie uma variante curta para a descrição do repo (README)?
