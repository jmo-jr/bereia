const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const { parseDocument } = require('htmlparser2');
const { findAll, textContent, removeElement } = require('domutils');
const root = path.resolve(__dirname, '..');

test('piloto Mateus 8: Eleventy preserva os 34 versículos, marcações e gera auditorias separadas', { timeout: 30000 }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-tooltip-build-'));
  try {
    const input = path.join(temp, 'input'), output = path.join(temp, 'output'), reports = path.join(temp, 'reports');
    fs.mkdirSync(input);
    fs.symlinkSync(path.join(root, 'src/_includes'), path.join(input, '_includes'), 'dir');
    const original = fs.readFileSync(path.join(root, 'src/biblia/nt/mateus/8.liquid'), 'utf8');
    fs.writeFileSync(path.join(input, 'index.liquid'), original);
    const config = path.join(temp, 'config.cjs');
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
      cwd: root, encoding: 'utf8', timeout: 20000, env: { ...process.env, BEREIA_BIBLE_REPORT_DIR: reports },
    });
    assert.equal(run.status, 0, `${run.error || ''}\n${run.stdout}\n${run.stderr}`);
    const html = fs.readFileSync(path.join(output, 'biblia/mateus/8/index.html'), 'utf8'), doc = parseDocument(html);
    const sourceVerses = [...original.matchAll(/\{% verse bookAbbrev bookChapter (\d+)(?:\s+[^%]*)? %\}([\s\S]*?)\{% endverse %\}/g)];
    assert.equal(sourceVerses.length, 34);
    for (const match of sourceVerses) {
      const verse = findAll(node => node.attribs?.id === `mt_8-${match[1]}`, doc.children)[0];
      const content = findAll(node => node.attribs?.class?.split(/\s+/u).includes('verse-text'), [verse])[0];
      assert.ok(content);
      findAll(node => node.attribs?.class === 'bible-original-content', [content]).forEach(removeElement);
      assert.equal(textContent(content), textContent(parseDocument(match[2].trim())), `Mt 8:${match[1]}`);
    }
    const summary = JSON.parse(fs.readFileSync(path.join(reports, 'bible-tooltip-summary.json'), 'utf8'));
    assert.equal(summary.totals.verses, 34);
    assert.ok(summary.totals.tooltips > 0);
    assert.equal(summary.totals.contextConfirmedTokens, 0);
    assert.ok(fs.existsSync(path.join(reports, 'bible-lexical-coverage.json')));
    assert.ok(fs.existsSync(path.join(reports, 'bible-lexical-ambiguities.json')));
    assert.ok(html.includes('/assets/js/bible-original.js'));
  } finally { fs.rmSync(temp, { recursive: true }); }
});
