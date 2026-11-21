const canonicalGreek = value => String(value).toLowerCase().normalize('NFD').replace(/\u0300/g, '\u0301').normalize('NFC');
const looseGreek = value => canonicalGreek(value).normalize('NFD').replace(/\p{M}/gu, '');
const words = text => [...text.matchAll(/[\p{L}\p{N}][\p{L}\p{M}\p{N}]*/gu)].map(match => ({
  value: match[0].normalize('NFC').toLocaleLowerCase('pt-BR'), start: match.index, end: match.index + match[0].length,
}));

function phrases(value) {
  if (typeof value !== 'string' || /[()[\]{}]/u.test(value)) return [];
  // Do not expand grammatical notation such as eu/ele(a), bracketed text or gloss notes.
  return [...new Set(value.split(/[,;/]/u).map(part => part.trim()).filter(part =>
    part && part.length <= 120 && !(value.includes('/') && /^(eu|tu|ele|ela|nós|vós|vocês|eles|elas)$/iu.test(part)) && !/[()[\]{}:=\d]/u.test(part) && /^[\p{L}\p{M}\s’'–-]+$/u.test(part)))];
}

function createLexicon(dictionary, approved = []) {
  const exact = new Map(), loose = new Map(), learned = new Map();
  for (const [form, entry] of Object.entries(dictionary)) {
    const data = { form, entry };
    const key = canonicalGreek(form), fallback = looseGreek(form);
    if (!exact.has(key)) exact.set(key, []);
    exact.get(key).push(data);
    if (!loose.has(fallback)) loose.set(fallback, []);
    loose.get(fallback).push(data);
  }
  for (const example of approved) {
    const { entry, reference } = example;
    for (const segment of entry.segments) {
      // Crossed/noncontiguous source positions are contextual, never a reusable phrase rule.
      if (!segment.tokens.length || segment.tokens.some((position, index) => !Number.isInteger(position) || position < 1 || position > entry.greek.length || (index && position !== segment.tokens[index - 1] + 1))) continue;
      const forms = segment.tokens.map(position => canonicalGreek(entry.greek[position - 1]));
      const key = forms[0];
      if (!learned.has(key)) learned.set(key, []);
      for (const phrase of [segment.text, ...(segment.alternatives || [])]) {
        if (!words(phrase).length || /[<>[\]{}]/u.test(phrase)) continue;
        const kind = phrase === segment.text ? 'alinhamento-revisado' : 'equivalencia-explicita';
        const phraseKey = words(phrase).map(word => word.value).join(' ');
        let rule = learned.get(key).find(item => item.kind === kind && item.phraseKey === phraseKey && JSON.stringify(item.forms) === JSON.stringify(forms));
        if (!rule) { rule = { forms, phrase, phraseKey, kind, examples: [] }; learned.get(key).push(rule); }
        rule.examples.push({ reference, source: { text: segment.text, start: segment.start, tokens: segment.tokens } });
      }
    }
  }
  return { exact, loose, learned };
}

function propose({ text, greek, reference, lexicon, excludeReference, maxCandidates = 500 }) {
  const result = { status: 'PROPOSTA_NAO_APROVADA', text, greek, candidates: [], unmatchedPortuguese: [], unmatchedGreek: [], issues: [] };
  if (/<[^>]*>|\{%|\{\{|&(?:#\d+|#x[\da-f]+|\w+);/iu.test(text)) {
    result.issues.push('Marcação ou entidade no texto: é necessária revisão do formato antes do alinhamento. Nenhuma marcação foi removida.');
    result.unmatchedGreek = greek.map((form, index) => ({ position: index + 1, form }));
    result.unmatchedPortuguese = words(text).map(word => ({ start: word.start, text: text.slice(word.start, word.end), reason: 'Texto com marcação; não analisado.' }));
    return result;
  }
  const pt = words(text), supplied = [...text.matchAll(/\[[^\]]*\]/gu)].map(match => [match.index, match.index + match[0].length]);
  const phraseCache = new Map(), candidates = new Map();
  let truncated = false;
  function occurrences(phrase) {
    const sequence = words(phrase).map(word => word.value), key = sequence.join('\u0000');
    if (phraseCache.has(key)) return phraseCache.get(key);
    const found = [];
    if (!sequence.length) return found;
    for (let i = 0; i <= pt.length - sequence.length; i++) {
      if (!sequence.every((word, j) => word === pt[i + j].value)) continue;
      const start = pt[i].start, end = pt[i + sequence.length - 1].end;
      if (supplied.some(([from, to]) => start < to && from < end)) continue;
      // Do not match across sentence or clause punctuation.
      if (pt.slice(i, i + sequence.length - 1).some((word, j) => /[^\s’'–-]/u.test(text.slice(word.end, pt[i + j + 1].start)))) continue;
      found.push({ start, text: text.slice(start, end) });
    }
    phraseCache.set(key, found);
    return found;
  }
  function offer(phrase, positions, evidence) {
    for (const match of occurrences(phrase)) {
      const key = `${match.start}:${match.text.length}:${positions.join(',')}`;
      if (!candidates.has(key)) {
        if (candidates.size >= maxCandidates) { truncated = true; continue; }
        candidates.set(key, { ...match, tokens: positions, evidence: [] });
      }
      const candidate = candidates.get(key);
      if (!candidate.evidence.some(item => JSON.stringify(item) === JSON.stringify(evidence))) candidate.evidence.push(evidence);
    }
  }
  greek.forEach((form, index) => {
    const key = canonicalGreek(form);
    const exact = lexicon.exact.get(key);
    const entries = exact || lexicon.loose.get(looseGreek(form)) || [];
    for (const { form: dictionaryForm, entry } of entries) {
      for (const field of ['pt', 'traducao']) for (const phrase of phrases(entry[field])) {
        offer(phrase, [index + 1], { kind: exact ? 'dicionario-forma-exata' : 'dicionario-forma-aproximada', form: dictionaryForm, field, phrase });
      }
    }
    for (const rule of lexicon.learned.get(key) || []) {
      if (!rule.forms.every((item, j) => item === canonicalGreek(greek[index + j] || ''))) continue;
      const examples = rule.examples.filter(example => example.reference !== excludeReference);
      if (examples.length) offer(rule.phrase, rule.forms.map((_, j) => index + j + 1), { kind: rule.kind, examples: examples.slice(0, 3), exampleCount: examples.length, phrase: rule.phrase });
    }
  });
  result.candidates = [...candidates.values()].sort((a, b) => a.start - b.start || b.text.length - a.text.length || a.tokens.join(',').localeCompare(b.tokens.join(','), 'en', { numeric: true }));
  result.candidates.forEach((candidate, index) => { candidate.id = `c${index + 1}`; candidate.conflicts = []; });
  for (let i = 0; i < result.candidates.length; i++) for (let j = i + 1; j < result.candidates.length; j++) {
    const a = result.candidates[i], b = result.candidates[j];
    if ((a.start < b.start + b.text.length && b.start < a.start + a.text.length) || a.tokens.some(token => b.tokens.includes(token))) {
      a.conflicts.push(b.id); b.conflicts.push(a.id);
    }
  }
  for (const candidate of result.candidates) {
    const approximateOnly = candidate.evidence.every(item => item.kind === 'dicionario-forma-aproximada');
    const generic = words(candidate.text).every(word => ['a', 'o', 'as', 'os', 'e', 'em', 'de', 'do', 'da', 'dos', 'das', 'um', 'uma', 'que', 'se', 'no', 'na', 'ao'].includes(word.value));
    candidate.review = candidate.conflicts.length ? 'AMBIGUO' : 'CANDIDATO_UNICO';
    candidate.priority = approximateOnly || generic || candidate.conflicts.length || truncated ? 'baixa' :
      candidate.evidence.some(item => ['alinhamento-revisado', 'equivalencia-explicita'].includes(item.kind)) ? 'alta' : 'media';
    if (approximateOnly) candidate.warning = 'A busca ignorou diacríticos gregos; conferir a forma e a flexão.';
  }
  if (truncated) result.issues.push(`Limite de ${maxCandidates} candidatos atingido; resultado parcial, não usar para inferir unicidade.`);
  if (truncated) result.candidates.forEach(candidate => { candidate.review = 'RESULTADO_PARCIAL'; });
  for (const word of pt) {
    if (!result.candidates.some(candidate => word.start >= candidate.start && word.end <= candidate.start + candidate.text.length)) {
      result.unmatchedPortuguese.push({ start: word.start, text: text.slice(word.start, word.end),
        reason: supplied.some(([from, to]) => word.start >= from && word.end <= to) ? 'Termo explicitamente suprido entre colchetes.' : 'Sem candidato lexical; requer revisão.' });
    }
  }
  result.unmatchedGreek = greek.flatMap((form, index) => result.candidates.some(candidate => candidate.tokens.includes(index + 1)) ? [] : [{ position: index + 1, form }]);
  return result;
}

function evaluate(proposal, gold) {
  const key = segment => JSON.stringify([segment.start, segment.text, segment.tokens]);
  const expected = new Set(gold.segments.map(key));
  const candidates = proposal.candidates;
  const found = candidates.filter(candidate => expected.has(key(candidate)));
  const unique = candidates.filter(candidate => candidate.review === 'CANDIDATO_UNICO');
  return { approvedSegments: expected.size, candidates: candidates.length, matchedApprovedSegments: new Set(found.map(key)).size,
    uniqueCandidates: unique.length, uniqueMatches: unique.filter(candidate => expected.has(key(candidate))).length };
}
module.exports = { canonicalGreek, phrases, words, createLexicon, propose, evaluate };
