const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { spawnSync } = require('node:child_process');
const c = require('../../tools/dictionary/core');

// Execute the production loader with only dictionary reads and log writes
// redirected. This compares every enriched token without modifying the repo.
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

test('todos os tokens enriquecidos permanecem idênticos', () => {
  const before = loadBooks(fs.readFileSync(c.BACKUP, 'utf8'));
  const after = loadBooks(c.serialize(c.flatten(c.read(c.SOURCE))));
  assert.deepEqual(after, before);
  assert.equal(before.MT.find(x => x.number === 8).verses.length, 34);
});

test('Eleventy 3.1.2: geração real de Mateus 8 idêntica', { timeout: 180000 }, () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-dictionary-'));
  try {
    fs.cpSync(path.join(c.ROOT, 'src'), path.join(temporary, 'src'), {
      recursive: true,
      filter: file => !['archive', 'assets', 'img', 'css', '.DS_Store'].includes(path.basename(file)),
    });
    for (const name of ['.eleventy.js', '.eleventyignore']) fs.copyFileSync(path.join(c.ROOT, name), path.join(temporary, name));
    fs.cpSync(path.join(c.ROOT, 'tools/dictionary'), path.join(temporary, 'tools/dictionary'), { recursive: true });
    fs.symlinkSync(path.join(c.ROOT, 'node_modules'), path.join(temporary, 'node_modules'), 'dir');
    const cli = path.join(c.ROOT, 'node_modules/@11ty/eleventy/cmd.cjs');
    const dict = path.join(temporary, 'src/_data', path.basename(c.DERIVED));
    const render = (text, output) => {
      fs.writeFileSync(dict, text);
      const run = spawnSync(process.execPath, [cli, '--quiet', `--output=${output}`], {
        cwd: temporary, encoding: 'utf8', timeout: 80000, env: { ...process.env, NODE_ENV: 'production' },
      });
      assert.equal(run.status, 0, `${run.error || ''}\n${run.stdout}\n${run.stderr}`);
      // The production generation hook must not silently change either input.
      assert.equal(fs.readFileSync(dict, 'utf8'), text);
      return fs.readFileSync(path.join(temporary, output, 'interlinear/mt/8/index.html'), 'utf8');
    };
    const original = render(fs.readFileSync(c.BACKUP, 'utf8'), 'before');
    const regenerated = render(c.serialize(c.flatten(c.read(c.SOURCE))), 'after');
    assert.equal(regenerated, original);
    assert(original.includes('λόγ') || original.includes('λογ'));
    console.log('Mateus 8: HTML idêntico byte a byte nas duas gerações Eleventy.');
  } finally { fs.rmSync(temporary, { recursive: true, force: true }); }
});
