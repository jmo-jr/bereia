const fs = require('node:fs');
const path = require('node:path');
const { createEnhanceTokenWithDict } = require('../_data/nt');
const { reconcile } = require('./bible-reconcile');
const root = path.join(__dirname, '..');
const escape = value => String(value).replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);

function createRenderer() {
  const cache = new Map();
  let enhance;
  let exactForms;
  const canonical = value => String(value).toLowerCase().normalize('NFD').replace(/\u0300/g, '\u0301').normalize('NFC');
  const records = new Map();
  const render = function(text, book, chapter, verse) {
    const filename = path.join(root, 'alinhamentos', book, `${chapter}.json`);
    if (!fs.existsSync(filename)) return text;
    if (!cache.has(filename)) {
      const alignment = JSON.parse(fs.readFileSync(filename, 'utf8'));
      const source = JSON.parse(fs.readFileSync(path.join(root, 'interlinear', 'nt', `${alignment.sourceBook}.json`), 'utf8'));
      cache.set(filename, { alignment, source });
    }
    const { alignment, source } = cache.get(filename);
    const entry = alignment.verses[String(verse)];
    if (!entry) return text;
    const ref = `${book} ${chapter}:${verse}`;
    const fail = reason => { throw new Error(`Alinhamento ${ref}: ${reason}`); };
    const suspend = reason => {
      records.set(ref, { reference: ref, status: 'pendente', pending: [{ reason }], rendered: 0 });
      return text;
    };
    if (/<[^>]*>|&(?:#\d+|#x[\da-f]+|\w+);/i.test(text)) return suspend('Marcação HTML ou entidade: revisar o alinhamento do versículo.');
    const sourceChapter = source.find(item => item.chapter === Number(chapter));
    const tokens = sourceChapter?.pericopes.flatMap(item => item.verses).find(item => item.verse === Number(verse))?.tokens;
    if (!tokens || JSON.stringify(tokens.map(item => item.lemma)) !== JSON.stringify(entry.greek)) {
      return suspend('Texto grego alterado: revisar os vínculos do versículo.');
    }
    let end = 0;
    for (const segment of entry.segments) {
      if (!Number.isSafeInteger(segment.start) || segment.start < end || !segment.text || entry.text.slice(segment.start, segment.start + segment.text.length) !== segment.text) fail('segmento aprovado inválido ou sobreposto.');
      if (!Array.isArray(segment.tokens) || !segment.tokens.length || segment.tokens.some(position => !Number.isSafeInteger(position) || position < 1 || position > tokens.length)) fail('posição grega aprovada inválida.');
      if (segment.alternatives && (!Array.isArray(segment.alternatives) || segment.alternatives.some(label => typeof label !== 'string' || !label.trim()))) fail('equivalência aprovada inválida.');
      end = segment.start + segment.text.length;
    }
    const result = reconcile(entry, text);
    result.pending.push(...(entry.pendingReview || []));
    records.set(ref, { reference: ref, status: result.pending.length ? 'pendente' : 'atualizado', rendered: result.segments.length,
      segments: result.segments.map(({ start, text, tokens, status, alternatives }) => ({ start, text, tokens, status, ...(alternatives ? { alternatives } : {}) })), pending: result.pending });
    if (!enhance) {
      const dictionary = JSON.parse(fs.readFileSync(path.join(root, '_data/nt/dict_flex_nt-lxx_greek-pt.json'), 'utf8'));
      exactForms = new Map(Object.entries(dictionary).map(([form, data]) => [canonical(form), data]));
      enhance = createEnhanceTokenWithDict(dictionary, { record() {} });
    }
    const lexicalWarnings = new Map();
    records.get(ref).lexicalWarnings = [];
    let cursor = 0;
    const parts = [];
    for (const segment of result.segments) {
      const index = segment.index;
      const { start, text: label } = segment;
      if (!Number.isSafeInteger(start) || start < cursor || !label || text.slice(start, start + label.length) !== label) {
        fail(`trecho ${index + 1} inválido ou sobreposto.`);
      }
      if (!Array.isArray(segment.tokens) || !segment.tokens.length) fail('trecho sem tokens gregos.');
      const details = segment.tokens.map(position => {
        if (!Number.isSafeInteger(position) || position < 1 || position > tokens.length) fail('posição grega inválida.');
        const original = tokens[position - 1];
        const exact = exactForms.get(canonical(original.lemma));
        const token = exact ? { ...exact, lemma: original.lemma } : enhance(original);
        if (!exact || canonical(token.grego || '') !== canonical(original.lemma)) {
          lexicalWarnings.set(position, { position, greek: original.lemma, dictionaryForm: token.grego || null,
            reason: 'Forma exata não confirmada no dicionário; morfologia e transliteração não exibidas.' });
          delete token.transliteracao;
          token.morfologia = 'Morfologia não confirmada para esta forma';
        }
        const heading = token.transliteracao ? `${token.lemma} (${token.transliteracao})` : token.lemma;
        const strong = token.strongs ? `G${token.strongs}` : '';
        const meaning = token.verbete || strong;
        return [heading, token.morfologia || 'Análise não disponível', meaning]
          .filter(Boolean).join('\n');
      }).join('\n\n');
      const id = `original-${book}-${chapter}-${verse}-${index + 1}`;
      parts.push(text.slice(cursor, start), `<span class="bible-original" tabindex="0" aria-haspopup="dialog" aria-expanded="false" aria-controls="${id}">${escape(label)}<span id="${id}" class="bible-original-content" role="dialog" aria-label="Dados do termo original" data-pagefind-ignore hidden><button type="button" class="bible-original-close" aria-label="Fechar dados do termo original">×</button><span class="bible-original-details">${escape(details).replace(/\n/g, '&#10;')}</span></span></span>`);
      cursor = start + label.length;
    }
    records.get(ref).lexicalWarnings = [...lexicalWarnings.values()];
    parts.push(text.slice(cursor));
    return parts.join('');
  };
  render.records = records;
  return render;
}
module.exports = { createRenderer };
