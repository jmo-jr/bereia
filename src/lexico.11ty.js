const normalize = value => String(value).normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
const removeStrongPrefix = value => typeof value === 'string'
  ? value.replace(/^G\d+:\s*/, '')
  : value;

module.exports = class {
  data() {
    return { permalink: '/assets/lexico/greek.json', layout: false, eleventyExcludeFromCollections: true };
  }

  render(data) {
    const dictionary = data.nt['dict_lex_nt-lxx_greek-pt'];
    const lxx = data.lxx['lexico_lxx_gr-pt-heb'];
    const notes = data['notas-lexicais'];
    const hebrew = new Map();
    for (const group of Object.values(lxx)) {
      if (!group || typeof group !== 'object') continue;
      for (const [lemma, value] of Object.entries(group)) {
        const entries = Array.isArray(value) ? value : [value];
        for (const entry of entries) {
          if (!entry.heb) continue;
          const key = normalize(lemma);
          if (!hebrew.has(key)) hebrew.set(key, []);
          hebrew.get(key).push({ lema: lemma, texto: entry.heb });
        }
      }
    }

    const result = {};
    for (const [strong, entry] of Object.entries(dictionary)) {
      // Preserve literal identifiers, including distinct historical keys.
      const key = 'G' + strong;
      result[key] = {
        lema: entry.lema,
        transliteracao: entry.transliteracao,
        verbete: removeStrongPrefix(entry.verbete),
        ...(entry.verbetes ? { verbetes: entry.verbetes } : {}),
        nota: notes[key]?.nota || '',
        hebraico: hebrew.get(normalize(entry.lema)) || [],
        flexoes: entry.flexoes.map(form => ({
          grego: form.grego,
          transliteracao: form.transliteracao,
          traducao: form.traducao,
          morfologia: form.morfologia,
          ocorrencias: form.ocorrencias,
          ocorrencias_lxx: form.ocorrencias_lxx,
          ...(form.verbete ? { verbete: removeStrongPrefix(form.verbete) } : {})
        }))
      };
    }
    return JSON.stringify({ fonte_lxx: lxx.fonte, verbetes: result });
  }
};
