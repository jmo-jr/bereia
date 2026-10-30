const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const c = require('../../tools/dictionary/core');

// Production loader, with dictionary reads and log writes isolated.
function loadBooks(dictText) {
  const filename = path.join(c.ROOT, 'src/_data/nt/index.js');
  const sandbox = { module: { exports: {} }, __dirname: path.dirname(filename), process,
    require(name) {
      if (name !== 'fs') return require(name);
      return { ...fs,
        readFileSync(file, ...args) { return file === c.DERIVED ? dictText : fs.readFileSync(file, ...args); },
        writeFileSync(file) { assert.equal(path.basename(file), 'nt-missing-lemmas.log'); },
      };
    } };
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), sandbox, { filename });
  return JSON.parse(JSON.stringify(sandbox.module.exports()));
}

function changes(before, after) {
  const result = [];
  for (const [book, chapters] of Object.entries(before)) {
    chapters.forEach((chapter, ci) => chapter.verses.forEach((verse, vi) => verse.tokens.forEach((token, ti) => {
      const next = after[book][ci].verses[vi].tokens[ti];
      const fields = {};
      for (const field of new Set([...Object.keys(token), ...Object.keys(next)])) {
        if (JSON.stringify(token[field]) !== JSON.stringify(next[field])) {
          fields[field] = { antes: token[field] ?? null, depois: next[field] ?? null };
        }
      }
      if (Object.keys(fields).length) result.push({ livro: book, capitulo: chapter.number,
        versiculo: verse.number, posicao: ti + 1, forma: token.lemma, campos: fields });
    })));
  }
  return result;
}
module.exports = { loadBooks, changes };
