const fs = require('node:fs');
const path = require('node:path');
const { parseDocument } = require('htmlparser2');
const { findAll, getOuterHTML } = require('domutils');
const { load, findMatches, canonicalGreek, ROOT } = require('./bible-global-lexicon');
const { reconcile } = require('./bible-reconcile');
const escape = value => String(value).replace(/[&<>"']/gu, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const hasClass = (node, name) => node.attribs?.class?.split(/\s+/u).includes(name);
function createGlobalRenderer({ root = ROOT, lexicon = load(root), approvedRenderer } = {}) {
  const books = new Map(), overrides = new Map(), metadata = new Map();
  for (const [key, value] of Object.entries(lexicon.dictionary)) {
    const canonical = canonicalGreek(key); if (!metadata.has(canonical)) metadata.set(canonical, []);
    metadata.get(canonical).push({ key, value });
  }
  const records = new Map(), termRecords = new Map();
  function source(book, chapter, verse) {
    if (!books.has(book)) {
      const file = path.join(root, 'src/interlinear/nt', book.toUpperCase() + '.json');
      books.set(book, fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : []);
    }
    const item = books.get(book).find(item => Number(item.chapter) === chapter)?.pericopes.flatMap(item => item.verses).find(item => Number(item.verse) === verse);
    return item?.tokens.map(token => token.lemma);
  }
  function manual(book, chapter, verse) {
    const key = `${book}/${chapter}`;
    if (!overrides.has(key)) {
      const file = path.join(root, 'src/alinhamentos', book, chapter + '.json');
      overrides.set(key, fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')).verses : {});
    }
    return overrides.get(key)[verse];
  }
  function details(candidate, counter) {
    return candidate.forms.map((form, index) => {
      const key = candidate.dictionaryForms[index];
      const entry = Object.hasOwn(lexicon.dictionary, key) ? lexicon.dictionary[key] : metadata.get(canonicalGreek(form))?.[0]?.value;
      if (!entry || canonicalGreek(entry.grego || key) !== canonicalGreek(form)) {
        counter.missingMetadata++;
        return form + '\nDados desta flexão não disponíveis no dicionário.';
      }
      return [form + (entry.transliteracao ? ` (${entry.transliteracao})` : ''), entry.morfologia || 'Análise não disponível', entry.verbete || (entry.strongs ? `G${entry.strongs}` : '')].filter(Boolean).join('\n');
    }).join('\n\n');
  }
  function replaceText(node, nodes) {
    const siblings = node.parent.children, index = siblings.indexOf(node);
    siblings.splice(index, 1, ...nodes);
    for (let i = 0; i < siblings.length; i++) { siblings[i].parent = node.parent; siblings[i].prev = siblings[i - 1] || null; siblings[i].next = siblings[i + 1] || null; }
  }
  function transform(html) {
    if (!html.includes('verse-text')) return html;
    const document = parseDocument(html), elements = findAll(node => hasClass(node, 'verse-text'), document.children);
    const counts = new Map();
    function identify(node) {
      let parent = node.parent;
      while (parent && !hasClass(parent, 'verse')) parent = parent.parent;
      return /^([a-z0-9]+)_(\d+)-(\d+)$/iu.exec(parent?.attribs?.id || '');
    }
    for (const element of elements) { const id = identify(element); if (id) { const ref = `${id[1]} ${Number(id[2])}:${Number(id[3])}`; counts.set(ref, (counts.get(ref) || 0) + 1); } }
    for (const element of elements) {
      const id = identify(element); if (!id) continue;
      const book = id[1].toLowerCase(), chapter = Number(id[2]), verse = Number(id[3]), reference = `${book} ${chapter}:${verse}`;
      const counter = { reference, tooltips: 0, alternatives: 0, missingMetadata: 0, skippedMarkup: 0, issues: [] };
      records.set(reference, counter);
      if (counts.get(reference) > 1) { counter.issues.push('Id bíblico duplicado na página; associação automática suspensa.'); continue; }
      const greek = source(book, chapter, verse);
      if (!greek) { counter.issues.push('Texto grego da referência não encontrado.'); continue; }
      const useOverrides = process.env.BEREIA_VERSE_OVERRIDES === '1' || lexicon.rules.useVerseOverrides === true;
      const exception = useOverrides ? manual(book, chapter, verse) : undefined, excludedTokens = new Set();
      for (const segment of useOverrides ? approvedRenderer?.records.get(reference)?.segments || [] : []) for (const token of segment.tokens) excludedTokens.add(token);
      if (exception && JSON.stringify(exception.greek) === JSON.stringify(greek)) for (const item of exception.untranslatedTokens || []) excludedTokens.add(item.position);
      function visible(node) {
        if (hasClass(node, 'bible-original-content')) return '';
        return node.type === 'text' ? node.data : (node.children || []).map(visible).join('');
      }
      const text = visible(element);
      const protectedRanges = exception ? reconcile({ text: exception.text, segments: (exception.unlinkedPortuguese || []).map(note => ({ ...note, tokens: [] })) }, text).segments : [];
      let offset = 0, serial = 0;
      function visit(node, blocked = false) {
        if (hasClass(node, 'bible-original-content')) return;
        const skip = blocked || hasClass(node, 'bible-original') || hasClass(node, 'tooltip') || hasClass(node, 'ref') || ['script', 'style', 'button', 'a'].includes(node.name);
        if (node.type !== 'text') { for (const child of [...(node.children || [])]) visit(child, skip); return; }
        const from = offset; offset += node.data.length;
        if (skip) { counter.skippedMarkup++; return; }
        const matches = findMatches(node.data, greek, lexicon, excludedTokens).filter(match => !protectedRanges.some(range => from + match.start < range.start + range.text.length && range.start < from + match.end));
        if (!matches.length) return;
        let cursor = 0; const parts = [];
        for (const match of matches) {
          const ambiguous = match.candidates.length > 1;
          if (ambiguous && lexicon.ambiguityPolicy === 'omit') continue;
          const id = `global-original-${book}-${chapter}-${verse}-${++serial}`;
          const content = (ambiguous ? 'Alternativas lexicais presentes no versículo:\n\n' : '') + match.candidates.map((candidate, index) => (ambiguous ? `Possibilidade ${index + 1}\n` : '') + details(candidate, counter)).join('\n\n');
          parts.push(escape(node.data.slice(cursor, match.start)), `<span class="bible-original" tabindex="0" aria-haspopup="dialog" aria-expanded="false" aria-controls="${id}">${escape(match.text)}<span id="${id}" class="bible-original-content" role="dialog" aria-label="Dados do termo original" data-pagefind-ignore hidden><button type="button" class="bible-original-close" aria-label="Fechar dados do termo original">×</button><span class="bible-original-details">${escape(content)}</span></span></span>`);
          cursor = match.end; counter.tooltips++; if (ambiguous) counter.alternatives++;
          if (!termRecords.has(match.term)) termRecords.set(match.term, { tooltips: 0, alternatives: 0, examples: [] });
          const term = termRecords.get(match.term); term.tooltips++; if (ambiguous) term.alternatives++;
          if (term.examples.length < 3 && !term.examples.includes(reference)) term.examples.push(reference);
        }
        if (cursor) { parts.push(escape(node.data.slice(cursor))); replaceText(node, parseDocument(parts.join('')).children); }
      }
      visit(element);
    }
    return getOuterHTML(document);
  }
  function report() {
    return { version: 1, source: 'src/tooltip-relations.json + dicionário definitivo', scope: 'Busca lexical global, filtrada pelo grego de cada versículo; alternativas não são aprovação contextual.',
      totals: { verses: records.size, versesWithAutomaticTooltips: [...records.values()].filter(record => record.tooltips).length, tooltips: [...records.values()].reduce((n, item) => n + item.tooltips, 0), alternatives: [...records.values()].reduce((n, item) => n + item.alternatives, 0), missingMetadata: [...records.values()].reduce((n, item) => n + item.missingMetadata, 0) },
      terms: Object.fromEntries([...termRecords].sort(([a], [b]) => a.localeCompare(b, 'pt-BR'))), issues: [...records.values()].filter(record => record.issues.length) };
  }
  return { transform, report, records, lexicon };
}
module.exports = { createGlobalRenderer };
