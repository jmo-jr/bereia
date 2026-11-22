const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { parseTbesg } = require('../tools/lxx/audit_tbesg');

test('TBESG conserva IDs distintos, campos vazios, UTF-8 e posição da fonte', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-tbesg-'));
  const file = path.join(directory, 'source.txt');
  try {
    const original = '\ufeffDocumentação\n' +
      'G0001\tG0001G =\tG0001G\tἄλφα\talpha\tG:N\talpha\t<b>definition</b>\n' +
      'G0001\tG0001H =\tG0001H\tἆ\t\t\tah!\tmeaning\n';
    fs.writeFileSync(file, original);
    const rows = parseTbesg(file);
    assert.equal(rows.length, 2);
    assert.equal(rows[1].dStrong, 'G0001H =');
    assert.equal(rows[1].morph, '');
    assert.equal(rows[0].greek, 'ἄλφα');
    assert.equal(rows[0].line, 2);
    assert.equal(fs.readFileSync(file, 'utf8'), original);
    fs.writeFileSync(file, 'G0001\tincompleto');
    assert.throws(() => parseTbesg(file), /Linha TBESG inválida/);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
