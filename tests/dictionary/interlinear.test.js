const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const c = require('../../tools/dictionary/core');
const { expectedProjection } = require('./expected');
const { loadBooks, changes } = require('./loader');

test('tokens do NT correspondem à projeção independente e diferenças estão registradas', () => {
  const expected = loadBooks(JSON.stringify(expectedProjection(c.read(c.BACKUP))));
  const actual = loadBooks(c.serialize(c.flatten(c.read(c.SOURCE))));
  assert.deepEqual(actual, expected);
  assert.equal(actual.MT.find(x => x.number === 8).verses.length, 34);
  const differences = changes(loadBooks(fs.readFileSync(c.BACKUP, 'utf8')), actual);
  const report = c.read(path.join(c.ROOT, 'tools/dictionary/simplification.json'));
  assert.deepEqual(differences, report.alteracoes_nos_tokens);
});

test('Eleventy 3.1.2: Mateus 8 comparado ao original e à projeção independente', { timeout: 240000 }, () => {
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
    const generator = path.join(temporary, 'tools/dictionary/generate.js');
    const generatorCode = fs.readFileSync(generator, 'utf8');
    const render = (text, output, regenerate) => {
      // Baselines must consume their own dictionary without the new generation
      // hook replacing it. The final render uses the actual production hook.
      fs.writeFileSync(generator, regenerate ? generatorCode : 'module.exports = () => {};\n');
      fs.writeFileSync(dict, text);
      const run = spawnSync(process.execPath, [cli, '--quiet', `--output=${output}`], {
        cwd: temporary, encoding: 'utf8', timeout: 80000, env: { ...process.env, NODE_ENV: 'production' },
      });
      assert.equal(run.status, 0, `${run.error || ''}\n${run.stdout}\n${run.stderr}`);
      assert.equal(fs.readFileSync(dict, 'utf8'), text);
      return fs.readFileSync(path.join(temporary, output, 'interlinear/mt/8/index.html'), 'utf8');
    };
    const original = render(fs.readFileSync(c.BACKUP, 'utf8'), 'original', false);
    const expected = render(c.serialize(expectedProjection(c.read(c.BACKUP))), 'expected', false);
    const regenerated = render(c.serialize(c.flatten(c.read(c.SOURCE))), 'actual', true);
    assert.equal(regenerated, expected);
    assert(regenerated.includes('λόγ') || regenerated.includes('λογ'));
    const report = c.read(path.join(c.ROOT, 'tools/dictionary/simplification.json'));
    const mt8Changes = report.alteracoes_nos_tokens.filter(x => x.livro === 'MT' && x.capitulo === 8);
    if (!mt8Changes.length) assert.equal(regenerated, original);
    console.log(`Mateus 8: ${mt8Changes.length} tokens alterados; HTML ${regenerated === original ? 'idêntico ao original' : 'diferente do original'}, idêntico à projeção independente.`);
  } finally { fs.rmSync(temporary, { recursive: true, force: true }); }
});
