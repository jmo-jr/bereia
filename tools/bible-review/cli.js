const path = require('node:path');
const { exportReview, importReview } = require('./review');
function run(argv) {
  const mode = argv.shift(), options = {};
  if (!['export', 'import'].includes(mode)) throw Error('Use export ou import.');
  for (let index = 0; index < argv.length; index++) {
    const arg = argv[index];
    if (arg === '--help') {
      console.log('Exportar: npm run bible:review:export -- [--book jo] [--chapter 2] [--source reports/bible-occurrence-relations] [--out reports/bible-review]\nValidar: npm run bible:review:import -- --file reports/bible-review/jo/2.csv\nAplicar decisões: repita a importação com --apply.'); return;
    }
    if (arg === '--apply' && mode === 'import') { options.apply = true; continue; }
    const allowed = mode === 'export' ? ['--book', '--chapter', '--source', '--out'] : ['--file'];
    if (!allowed.includes(arg)) throw Error(`Opção desconhecida: ${arg}.`);
    const value = argv[++index];
    if (!value || value.startsWith('--')) throw Error(`Falta valor para ${arg}.`);
    const name = { '--book': 'book', '--chapter': 'chapter', '--source': 'sourceDir', '--out': 'outDir', '--file': 'file' }[arg];
    options[name] = name === 'chapter' ? Number(value) : name === 'book' ? value.toLowerCase() : path.resolve(value);
  }
  if (options.chapter !== undefined && (!options.book || !Number.isSafeInteger(options.chapter) || options.chapter < 1)) throw Error('--chapter requer --book e inteiro positivo.');
  const result = mode === 'export' ? exportReview(options) : importReview(options);
  console.log(JSON.stringify(result, null, 2));
}
if (require.main === module) { try { run(process.argv.slice(2)); } catch (error) { console.error(error.message); process.exitCode = 1; } }
module.exports = { run };
