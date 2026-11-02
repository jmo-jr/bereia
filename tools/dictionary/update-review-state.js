const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const c = require('./core');

const STATE = path.join(__dirname, 'review-state.json');

function currentState() {
  const sourceText = fs.readFileSync(c.SOURCE);
  const source = JSON.parse(sourceText);
  const rows = c.records(source);
  const index = c.buildFormIndex(source);
  return {
    source_sha256: crypto.createHash('sha256').update(sourceText).digest('hex'),
    entradas: rows.length,
    grupos_strong: Object.keys(source).length,
    lemas_resolvidos: new Set(Object.values(source).map(group => group.lema).filter(Boolean)).size,
    formas_gregas: new Set(rows.map(row => row.grego)).size,
    analises_morfologicas: new Set(rows.map(row => JSON.stringify([row.abrev_morf, row.morfologia]))).size,
    formas_com_multiplas_analises: Object.values(index).filter(refs => refs.length > 1).length,
    referencias_indice: Object.values(index).reduce((total, refs) => total + refs.length, 0),
    flexoes_sem_lema: Object.values(source).filter(group => group.lema === null)
      .reduce((total, group) => total + group.flexoes.length, 0),
  };
}

function update({ check = false } = {}) {
  const current = currentState();
  if (check) {
    assert.deepEqual(c.read(STATE), current,
      'Estado linguístico alterado sem atualizar tools/dictionary/review-state.json');
    return false;
  }
  return c.writeIfChanged(STATE, c.serialize(current));
}

if (require.main === module) {
  const check = process.argv.includes('--check');
  const changed = update({ check });
  console.log(check ? 'Estado linguístico aprovado e atual.' :
    changed ? 'Estado linguístico aprovado atualizado.' : 'Estado linguístico já estava atualizado.');
}

module.exports = { STATE, currentState, update };
