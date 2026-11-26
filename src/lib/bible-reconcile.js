// Preserve only word matches present in every optimal, order-preserving alignment.
const words = text => [...text.matchAll(/[\p{L}\p{N}][\p{L}\p{M}\p{N}]*/gu)].map(match => ({
  text: match[0].normalize('NFC').toLocaleLowerCase('pt-BR'), start: match.index, end: match.index + match[0].length,
}));

function mandatoryMatches(before, after) {
  const a = words(before), b = words(after);
  const n = a.length, m = b.length;
  if (n * m > 1000000) return { a, b, matches: new Map() };
  const prefix = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  const suffix = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = 0; i < n; i++) for (let j = 0; j < m; j++) {
    prefix[i + 1][j + 1] = a[i].text === b[j].text ? prefix[i][j] + 1 : Math.max(prefix[i][j + 1], prefix[i + 1][j]);
  }
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) {
    suffix[i][j] = a[i].text === b[j].text ? suffix[i + 1][j + 1] + 1 : Math.max(suffix[i + 1][j], suffix[i][j + 1]);
  }
  const length = prefix[n][m], matches = new Map();
  for (let i = 0; i < n; i++) {
    const candidates = [];
    let optional = false;
    for (let j = 0; j <= m; j++) {
      if (prefix[i][j] + suffix[i + 1][j] === length) optional = true;
      if (j < m && a[i].text === b[j].text && prefix[i][j] + 1 + suffix[i + 1][j + 1] === length) candidates.push(j);
    }
    if (!optional && candidates.length === 1) matches.set(i, candidates[0]);
  }
  return { a, b, matches };
}

function locate(mapping, start, label, text) {
  const indices = mapping.a.flatMap((word, index) => word.start >= start && word.end <= start + label.length ? [index] : []);
  if (!indices.length || mapping.a[indices[0]].start !== start || mapping.a[indices.at(-1)].end !== start + label.length) return;
  const targets = indices.map(index => mapping.matches.get(index));
  if (targets.some((target, index) => target === undefined || (index && target !== targets[index - 1] + 1))) return;
  const from = mapping.b[targets[0]].start, to = mapping.b[targets.at(-1)].end;
  return { start: from, text: text.slice(from, to) };
}

function reconcile(entry, text) {
  if (text === entry.text) return { segments: entry.segments.map((segment, index) => ({ ...segment, index, status: 'preservado' })), pending: [] };
  const mapping = mandatoryMatches(entry.text, text);
  const candidates = [], pending = [];
  entry.segments.forEach((segment, index) => {
    let found = locate(mapping, segment.start, segment.text, text);
    let status = 'reposicionado';
    if (!found) {
      const alternatives = (segment.alternatives || []).flatMap(label => {
        const variant = entry.text.slice(0, segment.start) + label + entry.text.slice(segment.start + segment.text.length);
        const match = locate(mandatoryMatches(variant, text), segment.start, label, text);
        return match ? [match] : [];
      });
      const distinct = [...new Map(alternatives.map(item => [`${item.start}:${item.text}`, item])).values()];
      if (distinct.length === 1) { found = distinct[0]; status = 'equivalencia-aprovada'; }
    }
    if (found) candidates.push({ ...segment, ...found, index, status });
    else pending.push({ index, text: segment.text, tokens: segment.tokens, reason: 'Trecho alterado, removido ou correspondência ambígua.' });
  });
  const segments = candidates.filter(segment => {
    const overlap = candidates.some(other => other !== segment && segment.start < other.start + other.text.length && other.start < segment.start + segment.text.length);
    if (overlap) pending.push({ index: segment.index, text: segment.text, tokens: segment.tokens, reason: 'Vínculos concorrentes para o mesmo trecho.' });
    return !overlap;
  }).sort((a, b) => a.start - b.start);
  // New words get reported even when every old segment remains valid.
  const uncovered = words(text).filter(word => !segments.some(segment => word.start >= segment.start && word.end <= segment.start + segment.text.length));
  const originalUncovered = words(entry.text).filter(word => !entry.segments.some(segment => word.start >= segment.start && word.end <= segment.start + segment.text.length));
  const knownUncovered = new Set(originalUncovered.flatMap(word => {
    const index = mapping.a.findIndex(item => item.start === word.start);
    const target = mapping.matches.get(index);
    return target === undefined ? [] : [mapping.b[target].start];
  }));
  for (const word of uncovered) {
    if (!knownUncovered.has(word.start)) pending.push({ text: text.slice(word.start, word.end), start: word.start, reason: 'Palavra atual sem vínculo seguro.' });
  }
  return { segments, pending };
}
module.exports = { reconcile, mandatoryMatches };
