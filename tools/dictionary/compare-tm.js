const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '../..');
// Comparison keys never change the original forms stored in the report.
const exactKey = form => form.toLowerCase().normalize('NFC');
const withoutMarks = form => form.normalize('NFD').replace(/\p{M}/gu, '');

function collectTM(books) {
  const forms = new Map();
  for (const [file, chapters] of books) {
    assert(Array.isArray(chapters), `${file}: capítulos inválidos`);
    for (const chapter of chapters) {
      assert(Array.isArray(chapter.pericopes), `${file}: perícopes inválidas`);
      for (const pericope of chapter.pericopes) {
        assert(Array.isArray(pericope.verses), `${file}: versículos inválidos`);
        for (const verse of pericope.verses) {
          assert(Array.isArray(verse.tokens), `${file}: tokens inválidos`);
          verse.tokens.forEach((token, index) => {
            assert(typeof token.lemma === 'string' && token.lemma.length, `${file}: forma inválida`);
            const occurrences = forms.get(token.lemma) || [];
            occurrences.push({ arquivo: file, capitulo: chapter.chapter, versiculo: verse.verse, token: index + 1 });
            forms.set(token.lemma, occurrences);
          });
        }
      }
    }
  }
  return forms;
}

function compare(tm, lexicon) {
  const lex = new Map();
  const candidates = new Map();
  for (const [strong, entry] of Object.entries(lexicon)) {
    assert(Array.isArray(entry.flexoes), `${strong}: flexões inválidas`);
    entry.flexoes.forEach((flexion, index) => {
      const form = flexion.grego;
      assert(typeof form === 'string' && form.length, `${strong}/flexoes[${index}]: grego inválido`);
      if (!lex.has(form)) {
        lex.set(form, []);
        const key = withoutMarks(form).toLowerCase();
        if (!candidates.has(key)) candidates.set(key, []);
        candidates.get(key).push(form);
      }
      lex.get(form).push({ strong, lema: entry.lema, flexao: index });
    });
  }
  const lexKeys = new Set([...lex.keys()].map(exactKey));
  const tmKeys = new Set([...tm.keys()].map(exactKey));
  const missing = [];
  for (const [form, references] of tm) {
    if (lexKeys.has(exactKey(form))) continue;
    missing.push({
      forma_tm: form, ocorrencias: references.length,
      candidatos: (candidates.get(withoutMarks(form).toLowerCase()) || []).map(candidate => ({
        forma_lexico: candidate,
        diferenca: 'diacriticos',
        presente_exatamente_no_tm: tmKeys.has(exactKey(candidate)),
        entradas: lex.get(candidate),
      })),
    });
  }
  const unused = [...lex].filter(([form]) => !tmKeys.has(exactKey(form))).map(([form, entries]) => ({ forma_lexico: form, entradas: entries }));
  return {
    criterios: {
      exato: 'Igualdade literal, insensível a maiúsculas e à representação Unicode; sem trim ou normalização.',
      representacao_unicode: 'Equivalência canônica NFC somente na chave de comparação; sem remoção de diacríticos ou alteração das formas originais.',
      contagens: 'formas_tm e formas_lexico contam grafias originais distintas, inclusive variantes de caixa e representação Unicode.',
      candidatos: 'Mesmas letras após NFD, remoção de marcas Unicode e conversão para minúsculas. Não prova identidade lexical.',
      escopo: 'tokens[].lemma do TM versus flexoes[].grego; lemas de verbetes não são formas textuais por si só.',
      revisao: 'Formas ausentes do TM podem pertencer à LXX. Nenhuma entrada é alterada ou excluída. flexao usa índice a partir de zero.',
    },
    resumo: {
      tokens_tm: [...tm.values()].reduce((total, refs) => total + refs.length, 0),
      formas_tm: tm.size, formas_lexico: lex.size,
      formas_tm_encontradas: tm.size - missing.length,
      formas_tm_ausentes: missing.length,
      ausentes_com_candidatos: missing.filter(row => row.candidatos.length).length,
      formas_lexico_sem_ocorrencia_exata_tm: unused.length,
    },
    formas_tm_ausentes: missing,
    formas_lexico_sem_ocorrencia_exata_tm: unused,
  };
}

function main() {
  const args = process.argv.slice(2);
  if (args.length && (args.length !== 2 || args[0] !== '--output')) {
    throw new Error('Uso: node tools/dictionary/compare-tm.js [--output caminho.json]');
  }
  const directory = path.join(ROOT, 'src/interlinear/nt');
  const files = fs.readdirSync(directory).filter(file => file.endsWith('.json')).sort();
  assert(files.length, 'Nenhum JSON do TM encontrado');
  const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
  const tm = collectTM(files.map(file => [file, read(path.join(directory, file))]));
  const report = compare(tm, read(path.join(ROOT, 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json')));
  const output = path.resolve(ROOT, args[1] || 'reports/dictionary/tm-lexico.json');
  assert(!fs.existsSync(output), `O relatório já existe: ${output}. Remova-o explicitamente ou escolha outro --output.`);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`, { flag: 'wx' });
  console.log(JSON.stringify(report.resumo, null, 2));
  console.log(`Relatório: ${output}`);
}

if (require.main === module) {
  try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { collectTM, compare };
