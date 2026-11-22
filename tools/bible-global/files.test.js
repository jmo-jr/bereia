const test = require('node:test');
const assert = require('node:assert/strict');
const { encode, parse } = require('./csv');
const { setValue } = require('./json-patch');

test('CSV global preserva UTF-8, aspas, quebras e campos que poderiam virar fórmulas', () => {
  const rows = [['palavra', 'grego'], ['a; "b"\nc', 'ἀρχῇ'], ['=1+1', '+2'], ["'=literal", "'Palavra"], ['-3', '@SUM(A1)']];
  assert.deepEqual(parse(encode(rows)), rows);
  assert.throws(() => parse('"texto'), /aspas não fechadas/);
});

test('edições globais não reformatam entradas vizinhas nem reordenam as chaves', () => {
  const raw = '{\r\n "version" : 1,\r\n "entries" : {"z":{"forms":["β"]}}\r\n}\r\n';
  let changed = setValue(raw, ['entries', 'a'], { forms: ['ἀρχῇ'] });
  assert.ok(changed.includes('"z":{"forms":["β"]}'));
  changed = setValue(changed, ['entries', 'a', 'forms'], ['λόγος']);
  assert.deepEqual(JSON.parse(changed).entries.a.forms, ['λόγος']);
  assert.ok(changed.indexOf('"z"') < changed.indexOf('"a"'));
});
