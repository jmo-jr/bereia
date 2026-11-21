const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const { parseDocument } = require('htmlparser2');
const { findAll, textContent, removeElement } = require('domutils');
const root = path.resolve(__dirname, '..');

test('Eleventy gera o capítulo após revisão sem alterar seu texto ou parágrafos', { timeout: 30000 }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-tooltip-build-'));
  try {
    const input = path.join(temp, 'input'), output = path.join(temp, 'output');
    fs.mkdirSync(input);
    fs.symlinkSync(path.join(root, 'src/_includes'), path.join(input, '_includes'), 'dir');
    const original = fs.readFileSync(path.join(root, 'src/biblia/nt/joao/1.liquid'), 'utf8');
    const revised = original.replace('Todas as coisas vieram a ser', 'Todas as coisas passaram a existir');
    fs.writeFileSync(path.join(input, 'index.liquid'), revised);
    const config = path.join(temp, 'config.cjs');
    // Real shortcodes, layout, reconciliation and lifecycle. The fixture omits
    // global NT/LXX data and Pagefind, which are unrelated to this rendering.
    fs.writeFileSync(config, `module.exports = config => {
      const proxy = new Proxy(config, { get(target, name) {
        if (name === 'addPassthroughCopy' || name === 'addWatchTarget') return () => {};
        if (name === 'on') return (event, handler) => {
          if (event === 'eleventy.after' && handler.toString().includes('execSync')) return;
          return target.on(event, handler);
        };
        return typeof target[name] === 'function' ? target[name].bind(target) : target[name];
      }});
      require(${JSON.stringify(path.join(root, '.eleventy.js'))})(proxy);
      config.addGlobalData('layout', 'page.liquid');
      return { dir: { input: ${JSON.stringify(input)}, includes: '_includes', output: ${JSON.stringify(output)} } };
    };`);
    const run = spawnSync(process.execPath, [path.join(root, 'node_modules/@11ty/eleventy/cmd.cjs'), `--config=${config}`], {
      cwd: root, encoding: 'utf8', timeout: 20000,
      env: { ...process.env, BEREIA_BIBLE_ALIGNMENT_REPORT: path.join(temp, 'report.json') },
    });
    assert.equal(run.status, 0, `${run.error || ''}\n${run.stdout}\n${run.stderr}`);
    const html = fs.readFileSync(path.join(output, 'biblia/joao/1/index.html'), 'utf8');
    const doc = parseDocument(html);
    const verse = findAll(node => node.attribs?.id === 'jo_1-3', doc.children)[0];
    const content = findAll(node => node.attribs?.class?.startsWith('verse-text'), [verse])[0];
    const dialogs = findAll(node => node.attribs?.role === 'dialog', [content]);
    assert.ok(dialogs.length > 0 && dialogs.length < 12);
    dialogs.forEach(removeElement);
    assert.equal(textContent(content), /\{% verse bookAbbrev bookChapter 3 %\}([\s\S]*?)\{% endverse %\}/.exec(revised)[1]);
    assert.ok(html.includes('/assets/js/bible-original.js'));
    const report = JSON.parse(fs.readFileSync(path.join(temp, 'report.json'), 'utf8'));
    assert.equal(report.pendingVerses, 1);
    assert.ok(report.verses.find(item => item.reference === 'jo 1:3').pending.length);
  } finally { fs.rmSync(temp, { recursive: true }); }
});
