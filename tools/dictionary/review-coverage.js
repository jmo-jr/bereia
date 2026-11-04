const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '../..');
const SOURCE = path.join(ROOT, 'src/_data/dict_lex_nt-lxx_greek-pt.json');
const REVIEWS = path.join(ROOT, 'tools/dictionary/reviews');
const OUTPUT = path.join(ROOT, 'tools/dictionary/review-coverage.json');

const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');

function textualStrongKeys(source) {
  // Some manually maintained top-level groups use one tab instead of two spaces.
  // Nested objects are more deeply indented, so this still selects only Strong keys.
  return [...source.matchAll(/^(?:  |\t)"([^"]+)": \{$/gm)].map(match => match[1]);
}

function flexions(source) {
  const lexicon = JSON.parse(source);
  const rows = [];
  for (const strongs of textualStrongKeys(source)) {
    const homographs = new Map();
    lexicon[strongs].flexoes.forEach((flexion, flexao) => {
      const homografo = homographs.get(flexion.grego) || 0;
      homographs.set(flexion.grego, homografo + 1);
      rows.push({
        strongs,
        flexao,
        grego: flexion.grego,
        homografo,
        abrev_morf: flexion.abrev_morf,
        morfologia: flexion.morfologia,
      });
    });
  }
  return rows;
}

function parseReference(reference) {
  const match = reference.match(/^(.*?)\/flexoes\[(\d+)\]\s+([\s\S]+)$/);
  assert(match, `Referência de revisão inválida: ${reference}`);
  return { strongs: match[1], flexao: Number(match[2]), grego: match[3] };
}

function reportRange(file, report) {
  if (report.inicio && report.fim) {
    return {
      file,
      inicio: { strongs: String(report.inicio.strongs), flexao: report.inicio.flexao, grego: report.inicio.grego },
      fim: { strongs: String(report.fim.strongs), flexao: report.fim.flexao, grego: report.fim.grego },
      quantidade: report.flexoes_revisadas,
      listaExplicita: Array.isArray(report.intervalo),
    };
  }
  assert(report.intervalo && !Array.isArray(report.intervalo), `Intervalo ausente: ${file}`);
  return {
    file,
    inicio: parseReference(report.intervalo.inicio),
    fim: parseReference(report.intervalo.fim),
    quantidade: report.intervalo.quantidade,
    listaExplicita: false,
  };
}

function locate(rows, reference) {
  return rows.findIndex(row => row.strongs === reference.strongs
    && row.flexao === reference.flexao && row.grego === reference.grego);
}

function stableKey(row) {
  return JSON.stringify([row.strongs, row.grego, row.homografo]);
}

function buildManifest() {
  const source = fs.readFileSync(SOURCE, 'utf8');
  const rows = flexions(source);
  const reportFiles = fs.readdirSync(REVIEWS).filter(file => file.endsWith('.json')).sort();
  const ranges = reportFiles.map(file => reportRange(file,
    JSON.parse(fs.readFileSync(path.join(REVIEWS, file), 'utf8'))));

  for (const range of ranges) {
    range.inicio_posicao = locate(rows, range.inicio);
    range.fim_posicao = locate(rows, range.fim);
    assert(range.inicio_posicao >= 0, `Início não localizado: ${range.file}`);
    assert(range.fim_posicao >= range.inicio_posicao, `Fim não localizado: ${range.file}`);
    range.quantidade_atual = range.fim_posicao - range.inicio_posicao + 1;
  }
  ranges.sort((a, b) => a.inicio_posicao - b.inicio_posicao);

  const coveredBy = new Array(rows.length).fill(null);
  for (const range of ranges) {
    for (let index = range.inicio_posicao; index <= range.fim_posicao; index++) {
      assert(!coveredBy[index], `Relatórios sobrepostos: ${coveredBy[index]} e ${range.file}`);
      coveredBy[index] = range.file;
    }
  }

  const entries = rows.map((row, position) => ({
    ...row,
    identidade: sha256(stableKey(row)).slice(0, 16),
    status: coveredBy[position] ? 'revisada' : 'fora_da_passagem',
    ...(coveredBy[position] ? { relatorio: coveredBy[position] } : {}),
  }));
  const reviewed = entries.filter(entry => entry.status === 'revisada').length;
  const divergences = ranges.filter(range => range.quantidade !== range.quantidade_atual).map(range => ({
    relatorio: range.file,
    quantidade_registrada: range.quantidade,
    quantidade_no_intervalo_atual: range.quantidade_atual,
    diferenca: range.quantidade_atual - range.quantidade,
  }));

  return {
    versao: 1,
    fonte: path.relative(ROOT, SOURCE),
    fonte_sha256: sha256(source),
    criterio_identidade: ['strongs literal', 'grego exato', 'ordinal do homografo no grupo'],
    observacao: 'flexao, abrev_morf e morfologia são snapshots auxiliares e não compõem a identidade estável.',
    resumo: {
      flexoes_na_fonte: entries.length,
      revisadas_por_intervalo: reviewed,
      fora_da_passagem: entries.length - reviewed,
      relatorios: ranges.length,
      divergencias_de_contagem: divergences.length,
    },
    cobertura: {
      inicio: ranges[0].inicio,
      fim: ranges.at(-1).fim,
      intervalos_contiguos: ranges.every((range, index) => index === 0
        || range.inicio_posicao === ranges[index - 1].fim_posicao + 1),
    },
    divergencias_de_contagem: divergences,
    entradas: entries,
  };
}

function compare(manifest, current) {
  const previous = new Map(manifest.entradas.map(entry => [stableKey(entry), entry]));
  const present = new Map(current.entradas.map(entry => [stableKey(entry), entry]));
  const missing = [...previous].filter(([key]) => !present.has(key)).map(([, entry]) => entry);
  const added = [...present].filter(([key]) => !previous.has(key)).map(([, entry]) => entry);
  const morphologyChanged = [...previous].flatMap(([key, entry]) => {
    const now = present.get(key);
    return now && (now.abrev_morf !== entry.abrev_morf || now.morfologia !== entry.morfologia)
      ? [{ identidade: entry.identidade, strongs: entry.strongs, grego: entry.grego,
        antes: [entry.abrev_morf, entry.morfologia], depois: [now.abrev_morf, now.morfologia] }]
      : [];
  });
  return { removidas_ou_nao_localizadas: missing, novas: added, morfologia_alterada: morphologyChanged };
}

const check = process.argv.includes('--check');
const current = buildManifest();
if (check) {
  assert(fs.existsSync(OUTPUT), 'Manifesto de cobertura ausente');
  const saved = JSON.parse(fs.readFileSync(OUTPUT, 'utf8'));
  const differences = compare(saved, current);
  const count = Object.values(differences).reduce((sum, values) => sum + values.length, 0);
  if (count) {
    console.error(JSON.stringify(differences, null, 2));
    process.exitCode = 1;
  } else {
    console.log(`Cobertura preservada: ${saved.resumo.revisadas_por_intervalo} revisadas; ${saved.resumo.fora_da_passagem} fora da passagem.`);
  }
} else {
  fs.writeFileSync(OUTPUT, JSON.stringify(current, null, 2) + '\n', 'utf8');
  console.log(`Manifesto criado: ${current.resumo.revisadas_por_intervalo} revisadas; ${current.resumo.fora_da_passagem} fora da passagem; ${current.resumo.divergencias_de_contagem} divergências de contagem.`);
}
