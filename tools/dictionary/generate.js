const fs = require('node:fs');
const path = require('node:path');
const c = require('./core');
function generate({ check = false } = {}) {
  const source = c.read(c.SOURCE);
  const products = [
    [c.DERIVED, c.serialize(c.flatten(source))],
    [path.join(c.ROOT, 'src/_data/dict_form_index_nt-lxx_greek-pt.json'), c.serialize(c.buildFormIndex(source))],
  ];
  for (const [file, content] of products) {
    if (check) {
      if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== content) {
        throw new Error(`Arquivo derivado desatualizado: ${file}`);
      }
    } else c.writeIfChanged(file, content);
  }
}
if (require.main === module) {
  generate({ check: process.argv.includes('--check') });
  const source = c.read(c.SOURCE);
  const total = c.records(source).length;
  const forms = Object.keys(c.buildFormIndex(source)).length;
  console.log(`${total} flexões preservadas; ${forms} formas no derivado; ${total - forms} análises adicionais no léxico e no índice.`);
}
module.exports = generate;
