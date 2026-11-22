// Diagnóstico somente leitura das falhas existentes; não executa build/gerador.
// Uso: node tools/audit/diagnose_tests.js [caminho-do-log-npm]
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { Liquid } = require('liquidjs');

const ROOT = path.resolve(__dirname, '../..');
const read = relative => JSON.parse(fs.readFileSync(path.join(ROOT, relative), 'utf8'));
const hash = relative => crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT, relative))).digest('hex');
const SOURCE = 'src/_data/nt/dict_lex_nt-lxx_greek-pt.json';
const DERIVED = 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json';
const BACKUP = 'tools/backups/dictionary-migration/dict_flex_nt-lxx_greek-pt.json';
const HISTORY = 'tools/dictionary/simplification.json';
const LOADER = 'src/_data/nt/index.js';
const canonical = v => Array.isArray(v) ? v.map(canonical) :
  v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(k => [k, canonical(v[k])])) : v;

function loadBooks(dictionary) {
  const filename = path.join(ROOT, LOADER);
  const sandbox = { module: { exports: {} }, __dirname: path.dirname(filename), process,
    require(name) {
      if (name !== 'fs') return require('node:module').createRequire(filename)(name);
      return { ...fs,
        readFileSync(file, ...args) {
          return path.resolve(file) === path.join(ROOT, DERIVED) ? JSON.stringify(dictionary) : fs.readFileSync(file, ...args);
        },
        writeFileSync(file) {
          // Suprimir exclusivamente o log criado pelo loader. Qualquer outra
          // tentativa de escrita falha, em vez de modificar dados de produção.
          assert.equal(path.resolve(file), path.join(ROOT, 'nt-missing-lemmas.log'));
        },
      };
    },
  };
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), sandbox, { filename });
  return JSON.parse(JSON.stringify(sandbox.module.exports()));
}

function historicalProjection(original) {
  // Oráculo independente, equivalente à organização por Strong dos testes.
  const groups = {};
  for (const entry of Object.values(original)) (groups[entry.strongs] ||= []).push({
    ...entry, ocorrencias_lxx: entry.ocorrencias_lxx ?? 0,
  });
  const projection = {};
  for (const entries of Object.values(groups)) for (const entry of entries) {
    if (!Object.hasOwn(projection, entry.grego)) projection[entry.grego] = entry;
  }
  return projection;
}

function changes(before, after) {
  const result = [];
  for (const [book, chapters] of Object.entries(before)) chapters.forEach((chapter, ci) =>
    chapter.verses.forEach((verse, vi) => verse.tokens.forEach((token, ti) => {
      const next = after[book][ci].verses[vi].tokens[ti];
      const fields = {};
      for (const field of new Set([...Object.keys(token), ...Object.keys(next)])) {
        if (JSON.stringify(token[field]) !== JSON.stringify(next[field])) {
          fields[field] = { antes: token[field] ?? null, depois: next[field] ?? null };
        }
      }
      if (Object.keys(fields).length) result.push({ livro: book, capitulo: chapter.number,
        versiculo: verse.number, posicao: ti + 1, forma: token.lemma, campos: fields });
    })));
  return result;
}

function historicalArchive(relative, expected) {
  // Recuperabilidade comprovada em memória, sem recriar fonte/backup.
  try {
    const commits = execFileSync('git', ['log', '--all', '--format=%H', '--', relative],
      { cwd: ROOT, encoding: 'utf8' }).trim().split('\n').filter(Boolean);
    for (const commit of commits) {
      let blob;
      try {
        blob = execFileSync('git', ['show', `${commit}:${relative}`],
          { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 8 * 1024 * 1024 });
      } catch { continue; }
      const sha = crypto.createHash('sha256').update(blob).digest('hex');
      if (sha === expected) return { recuperavel: true, commit, caminho: relative, sha256: sha, bytes: blob.length };
    }
    return { recuperavel: false, motivo: 'Nenhum blob no histórico consultado coincide com o baseline.' };
  } catch (error) { return { recuperavel: null, motivo: error.message }; }
}

async function diagnose(log) {
  const tracked = [SOURCE, DERIVED, BACKUP, HISTORY, LOADER, 'tools/dictionary/baseline.json',
    'src/_data/atChapterPages.js', 'src/_includes/page.liquid', 'src/_includes/toolBar.liquid',
    'tests/dictionary/integrity.test.js', 'tests/dictionary/interlinear.test.js',
    'tests/dictionary/lxx-pages.test.js', 'tools/audit/diagnose_tests.js', '.eleventy.js', 'package.json',
    ...fs.readdirSync(path.join(ROOT, 'src/interlinear/nt')).filter(f => f.endsWith('.json')).sort().map(f => 'src/interlinear/nt/' + f)];
  const manifest = Object.fromEntries(tracked.filter(p => fs.existsSync(path.join(ROOT, p))).map(p => [p, hash(p)]));
  const original = read(BACKUP);
  const actual = changes(loadBooks(original), loadBooks(historicalProjection(original)));
  const recorded = read(HISTORY).alteracoes_nos_tokens;
  const actualSet = new Set(actual.map(r => JSON.stringify(canonical(r))));
  const recordedSet = new Set(recorded.map(r => JSON.stringify(canonical(r))));
  const additional = actual.filter(r => !recordedSet.has(JSON.stringify(canonical(r))));
  const missing = recorded.filter(r => !actualSet.has(JSON.stringify(canonical(r))));
  const engine = new Liquid({ extname: '.liquid', root: path.join(ROOT, 'src/_includes') });
  engine.registerFilter('url', value => value);
  const page = fs.readFileSync(path.join(ROOT, 'src/_includes/page.liquid'), 'utf8');
  const toolbar = page.slice(page.indexOf('{% assign interlinearBooks'), page.indexOf('<div class="content-wrapper">'));
  const rendered = await engine.parseAndRender(toolbar, {
    ntBooks: [{ name: 'Mateus', permalink: '/interlinear/mt/', chapters: 28 }],
    atBooks: [{ name: 'Gênesis', permalink: '/interlinear/gn/', chapterNumbers: [1, 2], chapters: 2 }],
    bookChapter: 1, page: { url: '/interlinear/gn/1/' }, bookName: 'Gênesis', entry: { lxx: true },
  });
  const archive = 'src/_data/archive/strongsg.js';
  const expectedArchive = read('tools/dictionary/baseline.json').lexical_archive_sha256;
  const chapters = fs.readFileSync(path.join(ROOT, 'src/_data/atChapterPages.js'), 'utf8');
  const issues = [
    { teste: 'integrity.test.js', causa: 'Fonte histórica ausente, lida no topo do módulo; demais verificações desse arquivo nem chegam a executar.',
      evidencia: { arquivo: archive, existe: fs.existsSync(path.join(ROOT, archive)),
        sha256_esperado: expectedArchive, historico_git: historicalArchive(archive, expectedArchive) },
      proposta: 'Fonte original recuperável em memória pelo Git quando historico_git.recuperavel=true. Restaurar somente na etapa de manutenção autorizada; não fabricar substituto nem alterar baseline.' },
    { teste: 'interlinear.test.js: diferenças históricas', causa: 'Reexecução com o TM atual diverge do relatório histórico congelado.',
      evidencia: { diferencas_recalculadas: actual.length, diferencas_historicas: recorded.length,
        adicionais: additional, ausentes_ou_modificadas: missing },
      proposta: 'Preservar o histórico. Na futura manutenção dos testes, reproduzir com o snapshot original do TM e testar o estado atual separadamente; não atualizar simplification.json para fazer passar.' },
    { teste: 'interlinear.test.js: Eleventy', causa: 'Processo de renderização atingiu o limite de heap do Node, segundo o log da execução.',
      evidencia: { heap_esgotado_no_log: log.includes('heap out of memory'),
        script_build: read('package.json').scripts.build,
        limite_configurado_no_teste: 'O spawn herda process.env e não define heap próprio; o comando npm test não inclui o limite de 4096 do build.' },
      proposta: 'Isolar o caso de Mateus 8 com dependências mínimas e orçamento de memória explícito. Não repetir quatro builds integrais para validar a consulta lexical.' },
    { teste: 'lxx-pages.test.js: título', causa: 'Texto esperado no teste não coincide com o título atual; o título móvel antigo está comentado.',
      evidencia: { expectativa_presente: /LXX Interlinear Analítico/.test(rendered),
        titulos_atuais: [...rendered.matchAll(/<h2[^>]*>(.*?)<\/h2>/gs)].map(m => m[1].trim()) },
      proposta: 'Revisar o contrato do título e testar o elemento ativo. Não modificar a interface só para satisfazer texto histórico.' },
    { teste: 'lxx-pages.test.js: navegação', causa: 'Teste espera null no limite do livro; implementação aponta para o índice com #/.',
      evidencia: { usa_indice_no_limite: chapters.includes('`${book.permalink}#/`'), expectativa: null, exemplo_atual: '/interlinear/gn/#/' },
      proposta: 'Definir o contrato de navegação separadamente da auditoria lexical. Verificar se #/ é destino válido antes de propor uma correção.' },
  ];
  for (const [p, expected] of Object.entries(manifest)) assert.equal(hash(p), expected, `Fonte mudou: ${p}`);
  return { schema_version: 1, fontes_sha256: manifest,
    resultado_log: { passou: Number(log.match(/^# pass (\d+)$/m)?.[1] || 0),
      falhou: Number(log.match(/^# fail (\d+)$/m)?.[1] || 0) },
    problemas: issues, dados_modificados: false };
}

async function main() {
  const logPath = path.resolve(ROOT, process.argv[2] || 'reports/audit/tm/npm-test.log');
  const log = fs.readFileSync(logPath, 'utf8');
  if (!/^# fail \d+$/m.test(log)) throw new Error('Log de testes incompleto. Aguarde o término de npm test.');
  const report = await diagnose(log);
  report.log_sha256 = crypto.createHash('sha256').update(log).digest('hex');
  const output = path.join(ROOT, 'reports/audit/triagem');
  fs.mkdirSync(output, { recursive: true });
  const save = (name, text) => {
    const file = path.join(output, name);
    if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== text) fs.writeFileSync(file, text, 'utf8');
  };
  save('diagnostico-testes.json', JSON.stringify(report, null, 2) + '\n');
  save('diagnostico-testes.md', ['# Diagnóstico dos testes existentes', '',
    `Execução registrada: ${report.resultado_log.passou} testes passaram; ${report.resultado_log.falhou} falharam.`, '',
    ...report.problemas.flatMap(p => [`## ${p.teste}`, '', p.causa, '',
      `Evidência: ${JSON.stringify(p.evidencia)}`, '', `Proposta: ${p.proposta}`, '']),
    'Diagnóstico somente leitura. Nenhum teste, baseline, relatório histórico ou arquivo de produção alterado.', ''].join('\n'));
  console.log(JSON.stringify({ resultado: report.resultado_log, problemas: issuesSummary(report) }, null, 2));
}
const issuesSummary = report => report.problemas.map(p => ({ teste: p.teste, causa: p.causa }));
if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode = 1; });
module.exports = { diagnose, historicalProjection, changes };
