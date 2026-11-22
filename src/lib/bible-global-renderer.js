const fs = require('node:fs');
const path = require('node:path');
const { parseDocument } = require('htmlparser2');
const { findAll, getOuterHTML } = require('domutils');
const { load, findMatches, canonicalGreek, ROOT } = require('./bible-global-lexicon');
const { words, normalizePortuguese } = require('./bible-lexical-text');
const { loadExceptions, resolveExceptions } = require('./bible-exceptions');
const escape = value => String(value).replace(/[&<>"']/gu, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const hasClass = (node, name) => node.attribs?.class?.split(/\s+/u).includes(name);
const overlaps = (a, b) => a.start < b.end && b.start < a.end;

function createGlobalRenderer({ root = ROOT, lexicon = load(root), exceptions = loadExceptions(root) } = {}) {
  const books = new Map(), records = new Map(), terms = new Map(), coverage = new Map(), ambiguities = new Map();
  function source(book, chapter, verse) {
    if (!books.has(book)) {
      const file = path.join(root, 'src/interlinear/nt', book.toUpperCase() + '.json');
      books.set(book, fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : []);
    }
    const item = books.get(book).find(item => Number(item.chapter) === chapter)?.pericopes.flatMap(item => item.verses).find(item => Number(item.verse) === verse);
    return item?.tokens.map(token => token.lemma);
  }
  function dataFor(candidate, index) {
    // Candidate keys are exact dictionary references; never choose the first
    // analysis of a homograph that was not explicitly selected.
    return lexicon.dictionary[candidate.dictionaryForms[index]];
  }
  function details(candidate, counter) {
    return candidate.forms.map((form, index) => {
      const key = candidate.dictionaryForms[index], entry = dataFor(candidate, index);
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
  function auditWord(word, index, reference, text, greek, classification, reason) {
    const term = normalizePortuguese(text.slice(word.start, word.end)), key = term + '\u0000' + classification;
    if (!coverage.has(key)) coverage.set(key, { term, classification, status: 'PENDENTE', reason, occurrences: [] });
    coverage.get(key).occurrences.push({ reference, position: index + 1, start: word.start, text: text.slice(word.start, word.end), context: text,
      greekCandidates: (lexicon.terms.get(term)?.forms || []).filter(form => greek.some(original => canonicalGreek(form) === canonicalGreek(original))) });
  }
  function transform(html) {
    if (!html.includes('verse-text')) return html;
    const document = parseDocument(html), elements = findAll(node => hasClass(node, 'verse-text'), document.children), counts = new Map();
    function identify(node) {
      let parent = node.parent; while (parent && !hasClass(parent, 'verse')) parent = parent.parent;
      return /^([a-z0-9]+)_(\d+)-(\d+)$/iu.exec(parent?.attribs?.id || '');
    }
    for (const element of elements) { const id = identify(element); if (id) { const ref = `${id[1].toLowerCase()} ${Number(id[2])}:${Number(id[3])}`; counts.set(ref, (counts.get(ref) || 0) + 1); } }
    for (const element of elements) {
      const id = identify(element); if (!id) continue;
      const book = id[1].toLowerCase(), chapter = Number(id[2]), verse = Number(id[3]), reference = `${book} ${chapter}:${verse}`;
      let text = ''; const nodes = [];
      function collect(node, blocked = false) {
        if (hasClass(node, 'bible-original-content') || hasClass(node, 'ref') || ['script', 'style', 'sup'].includes(node.name)) return;
        const skip = blocked || hasClass(node, 'bible-original') || hasClass(node, 'tooltip') || ['button', 'a'].includes(node.name);
        if (node.type === 'text') { const start = text.length; text += node.data; nodes.push({ node, start, end: text.length, blocked: skip }); }
        else for (const child of node.children || []) collect(child, skip);
      }
      collect(element);
      const pt = words(text), blocked = nodes.filter(item => item.blocked), greek = source(book, chapter, verse);
      const counter = { reference, tooltips: 0, controls: 0, alternatives: 0, missingMetadata: 0, portugueseTokens: pt.length,
        lexicalTokens: 0, unambiguousLexicalTokens: 0, confirmedTokens: 0, exceptionAlternatives: 0, suppliedTokens: 0, confirmedWithoutOriginal: 0, excludedMarkupTokens: 0, displayedTokens: 0, issues: [] };
      records.set(reference, counter);
      if (counts.get(reference) > 1) counter.issues.push('Id bíblico duplicado; associação automática suspensa.');
      if (!greek) counter.issues.push('Texto grego da referência não encontrado.');
      if (counter.issues.length) {
        pt.forEach((word, index) => auditWord(word, index, reference, text, greek || [], 'FONTE_INCOMPATIVEL', counter.issues[0]));
        continue;
      }
      const contextual = resolveExceptions(exceptions, reference, text, greek, lexicon);
      counter.issues.push(...contextual.issues);
      const protectedRanges = [...blocked, ...contextual.suppressed, ...contextual.matches];
      const automatic = findMatches(text, greek, lexicon, contextual.excludedTokens, protectedRanges);
      const matches = [...contextual.matches.filter(match => !blocked.some(item => overlaps(item, match))), ...automatic].sort((a, b) => a.start - b.start);
      const renderable = [];
      for (const [index, match] of matches.entries()) {
        const ambiguous = match.candidates.length > 1, wordCount = pt.filter(word => word.start >= match.start && word.end <= match.end).length;
        if (match.confirmed && !ambiguous) counter.confirmedTokens += wordCount;
        else if (match.confirmed) counter.exceptionAlternatives += wordCount;
        else { counter.lexicalTokens += wordCount; if (!ambiguous) counter.unambiguousLexicalTokens += wordCount; }
        if (ambiguous) {
          counter.alternatives++;
          if (!ambiguities.has(match.term)) ambiguities.set(match.term, { term: match.term, status: 'ALTERNATIVAS', occurrences: [] });
          ambiguities.get(match.term).occurrences.push({ reference, position: pt.findIndex(word => word.start === match.start) + 1, start: match.start, text: match.text, context: text,
            resolution: match.confirmed ? 'EXCECAO_COM_ALTERNATIVAS' : 'NAO_CONFIRMADA', candidates: match.candidates.map(candidate => ({ forms: candidate.forms, dictionaryKeys: candidate.dictionaryForms,
              analyses: candidate.forms.map((_, i) => { const data = dataFor(candidate, i); return { lemma: data?.lema || lexicon.lemmas?.[data?.strongs] || null, strongs: data?.strongs || null, morphology: data?.morfologia || null }; }) })) });
        }
        if (ambiguous && lexicon.ambiguityPolicy === 'omit') continue;
        const content = (ambiguous ? 'Alternativas lexicais presentes no versículo:\n\n' : '') + match.candidates.map((candidate, i) => (ambiguous ? `Possibilidade ${i + 1}\n` : '') + details(candidate, counter)).join('\n\n');
        renderable.push({ ...match, id: `global-original-${book}-${chapter}-${verse}-${index + 1}`, content });
        counter.tooltips++; counter.displayedTokens += wordCount;
        if (!terms.has(match.term)) terms.set(match.term, { tooltips: 0, alternatives: 0, examples: [] });
        const term = terms.get(match.term); term.tooltips++; if (ambiguous) term.alternatives++;
        if (term.examples.length < 3 && !term.examples.includes(reference)) term.examples.push(reference);
      }
      const supplied = [...text.matchAll(/\[[^\]]*\]/gu)].map(match => ({ start: match.index, end: match.index + match[0].length }));
      pt.forEach((word, index) => {
        if (matches.some(match => word.start >= match.start && word.end <= match.end)) return;
        if (blocked.some(item => overlaps(item, word))) { counter.excludedMarkupTokens++; return; }
        if (supplied.some(item => word.start >= item.start && word.end <= item.end)) { counter.suppliedTokens++; return; }
        if (contextual.suppressed.some(item => word.start >= item.start && word.end <= item.end)) { counter.confirmedWithoutOriginal++; return; }
        const entry = lexicon.terms.get(normalizePortuguese(text.slice(word.start, word.end)));
        const classification = entry?.enabled === false ? 'DESATIVADO_GLOBALMENTE' : entry ? 'SEM_CANDIDATO_NO_VERSICULO' : 'COBERTURA_LEXICAL_INSUFICIENTE';
        if (entry?.enabled === false) return;
        auditWord(word, index, reference, text, greek, classification, entry ? 'Há relação lexical, mas nenhuma candidata neste versículo; conferir expressão, contexto ou suprimento.' : 'Sem entrada lexical simples; pode ser expressão composta, auxiliar, suprimento ou sinônimo. Não é erro confirmado.');
      });
      // A phrase may cross formatting tags. Its pieces share the association,
      // but keep unique control ids and all original DOM structure.
      for (const item of nodes) {
        if (item.blocked) continue;
        const selected = renderable.filter(match => overlaps(item, match));
        if (!selected.length) continue;
        let cursor = 0; const parts = [];
        for (const match of selected) {
          const from = Math.max(item.start, match.start) - item.start, to = Math.min(item.end, match.end) - item.start;
          const id = `${match.id}-p${counter.controls++}`;
          parts.push(escape(item.node.data.slice(cursor, from)), `<span class="bible-original" tabindex="0" aria-haspopup="dialog" aria-expanded="false" aria-controls="${id}">${escape(item.node.data.slice(from, to))}<span id="${id}" class="bible-original-content" role="dialog" aria-label="Dados do termo original" data-pagefind-ignore hidden><button type="button" class="bible-original-close" aria-label="Fechar dados do termo original">×</button><span class="bible-original-details">${escape(match.content)}</span></span></span>`);
          cursor = to;
        }
        parts.push(escape(item.node.data.slice(cursor))); replaceText(item.node, parseDocument(parts.join('')).children);
      }
    }
    return getOuterHTML(document);
  }
  function report() {
    const values = [...records.values()], sum = key => values.reduce((n, item) => n + item[key], 0);
    const total = sum('portugueseTokens'), displayed = sum('displayedTokens');
    return { version: 2, source: 'Dicionário + complemento global + exceções opcionais com âncoras persistentes',
      totals: { verses: records.size, versesWithAutomaticTooltips: values.filter(record => record.tooltips).length, tooltips: sum('tooltips'), controls: sum('controls'), alternatives: sum('alternatives'), missingMetadata: sum('missingMetadata'),
        portugueseTokens: total, lexicalTokens: sum('lexicalTokens'), unambiguousLexicalTokens: sum('unambiguousLexicalTokens'), contextConfirmedTokens: sum('confirmedTokens'), exceptionAlternativeTokens: sum('exceptionAlternatives'), suppliedExplicitTokens: sum('suppliedTokens'), confirmedWithoutOriginal: sum('confirmedWithoutOriginal'), excludedMarkupTokens: sum('excludedMarkupTokens'), displayedTokens: displayed,
        lexicalCoveragePercent: total ? Number((100 * displayed / total).toFixed(2)) : 0 },
      definitions: { lexicalCoveragePercent: 'Tokens portugueses com tooltip / tokens portugueses analisados. Não mede confirmação contextual.', contextConfirmedTokens: 'Somente associações explícitas de exceções válidas e com uma análise.', suppliedExplicitTokens: 'Somente palavras explicitamente entre colchetes; ausências lexicais não são classificadas automaticamente como suprimentos.' },
      terms: Object.fromEntries([...terms].sort(([a], [b]) => a.localeCompare(b, 'pt-BR'))), issues: values.filter(record => record.issues.length) };
  }
  function reports() {
    return { summary: report(), coverage: { version: 1, scope: 'Pendências agrupadas por termo, com referências individuais. Não são correções automáticas do dicionário.', terms: [...coverage.values()].sort((a, b) => a.term.localeCompare(b.term, 'pt-BR')) },
      ambiguities: { version: 1, scope: 'Alternativas simultâneas são grupos; grupos diferentes são possibilidades, não uma escolha contextual automática.', terms: [...ambiguities.values()].sort((a, b) => a.term.localeCompare(b.term, 'pt-BR')) } };
  }
  return { transform, report, reports, records, lexicon };
}
module.exports = { createGlobalRenderer };
