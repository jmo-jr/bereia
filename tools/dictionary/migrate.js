// One-time migration. Never overwrites the original or an existing source.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const c = require('./core');
assert(!fs.existsSync(c.SOURCE), 'A fonte lexical já existe; migração recusada.');
assert.equal(fs.readFileSync(c.DERIVED, 'utf8'), fs.readFileSync(c.BACKUP, 'utf8'));
const archivePath = path.join(c.ROOT, 'src/_data/archive/strongsg.js');
const archive = fs.readFileSync(archivePath, 'utf8');
// Parse only the JSON object; do not execute the archived JavaScript.
const lexical = JSON.parse(archive.slice(archive.indexOf('{', archive.indexOf('var strongsGreekDictionary')), archive.lastIndexOf('}') + 1));
const original = c.read(c.BACKUP);
const source = c.migrate(original, lexical);
// Authorized changes: use grego as key, fixed fields, default LXX count to 0.
// Compare complete records as a multiset before projecting one per form.
const originalRows = Object.values(original).map(c.fixedEntry).map(JSON.stringify).sort();
const migratedRows = c.records(source).map(JSON.stringify).sort();
assert.deepEqual(migratedRows, originalRows);
fs.writeFileSync(c.SOURCE, c.serializeLexicon(source), { flag: 'wx' });
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
fs.writeFileSync(path.join(__dirname, 'baseline.json'), c.serialize({
  backup_sha256: sha(c.BACKUP), lexical_archive_sha256: sha(archivePath),
  entradas: Object.keys(original).length,
  grupos_strong: Object.keys(source).length,
  lemas_resolvidos: new Set(Object.values(source).map(x => x.lema).filter(Boolean)).size,
  formas_gregas: new Set(Object.values(original).map(x => x.grego)).size,
  analises_morfologicas: new Set(Object.values(original).map(x => JSON.stringify([x.abrev_morf, x.morfologia]))).size,
}));
console.log('Fonte lexical criada; dicionário original intacto.');
