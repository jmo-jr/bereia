#!/usr/bin/env node

/**
 * Atualiza o campo `traducao` de cada entrada em src/_data/greeknt_dict.json
 * usando as definições em português do dicionário de Strong (src/_data/strongsg.js).
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'src', '_data');
const STRONGS_FILE = path.join(DATA_DIR, 'strongsg.js');
const GREEK_DICT_FILE = path.join(DATA_DIR, 'greeknt_dict.json');

const STRONGS_ANCHOR = 'var strongsGreekDictionary';

const TRANSLATION_OVERRIDES = {
  G243: 'outro; diferente',
  G262: 'amarantino; que não murcha',
  G474: 'arremessar contra; confrontar',
  G503: 'encarar de frente',
  G512: 'inútil; sem proveito',
  G536: 'primícias; oferta inaugural',
  G645: 'arrancar; desembainhar; afastar',
  G648: 'destelhar; descobrir',
  G692: 'ocioso; inútil; sem frutos',
  G772: 'sem força; fraco; enfermo',
  G888: 'sem valor; desprezível',
  G889: 'tornar inútil; arruinar',
  G971: 'forçar; sofrer violência',
  G973: 'pessoa violenta; vigoroso',
  G1023: 'braço; força',
  G1411: 'poder; capacidade; milagre',
  G1750: 'envolver; enrolar',
  G1825: 'despertar por completo; ressuscitar',
  G1840: 'ser plenamente capaz',
  G1849: 'autoridade; poder delegado; domínio',
  G1874: 'escutar atentamente',
  G1911: 'lançar sobre; aplicar; impor',
  G1952: 'ficar sem; faltar',
  G2051: 'contender; discutir',
  G2081: 'interiormente; desde dentro',
  G2297: 'maravilhoso; milagre',
  G2420: 'sacerdócio; ofício sagrado',
  G2461: 'tropa de cavalaria',
  G2478: 'forte; poderoso; vigoroso',
  G2479: 'força; vigor',
  G2480: 'ser forte; prevalecer',
  G2521: 'sentar-se; permanecer',
  G2556: 'mau; prejudicial; perverso',
  G2673: 'anular; tornar ineficaz',
  G2867: 'caiar; branquear',
  G2873: 'trabalho árduo; fadiga',
  G2902: 'segurar firme; dominar',
  G2998: 'extrair pedra; trabalhar em pedreira',
  G3006: 'liso; nivelado',
  G3699: 'onde quer que',
  G3720: 'matinal; do amanhecer',
  G3730: 'ímpeto; impulso inicial',
  G3798: 'tardio; entardecer',
  G3849: 'forçar; constranger',
  G4016: 'vestir; envolver; cercar',
  G4068: 'vangloriar-se',
  G4264: 'impulsionar adiante; incitar',
  G4287: 'designado previamente; prazo marcado',
  G4399: 'antecipar; chegar antes',
  G4435: 'punho fechado; esfregar com as mãos',
  G4469: 'insulto vazio; cabeça-oca',
  G4470: 'trapo; pedaço de pano',
  G4516: 'Roma; vigor',
  G4710: 'diligência; empenho; pressa',
  G4764: 'luxo; voluptuosidade',
  G4766: 'estender; forrar; preparar leito',
  G4988: 'Sóstenes',
  G5078: 'arte; ofício; habilidade',
  G5107: 'tal como este; tão grande',
  G5548: 'ungir; consagrar com óleo',
  G5594: 'refrescar; resfriar; soprar',
  G5624: 'útil; proveitoso; vantajoso',
};

const readFile = filename => fs.readFileSync(filename, 'utf8');

const normaliseIndentTokens = content =>
  content.replace(/(\r?\n)((?:\\t)+)/g, (match, newline, tabs) => `${newline}${'\t'.repeat(tabs.length / 2)}`);

const extractJsonObject = (content, anchor) => {
  const anchorIndex = content.indexOf(anchor);
  if (anchorIndex === -1) {
    throw new Error(`Anchor \"${anchor}\" not found in source file.`);
  }

  let start = content.indexOf('{', anchorIndex);
  if (start === -1) {
    throw new Error('Could not find opening brace for dictionary object.');
  }

  const end = content.indexOf('};', start);
  if (end === -1) {
    throw new Error('Could not locate closing brace for dictionary object.');
  }

  return content.slice(start, end + 1);
};

const normaliseSpaces = text =>
  text
    .replace(/--/g, ' ')
    .replace(/\\s+/g, ' ')
    .replace(/\\s*([,:;])\\s*/g, '$1 ')
    .trim();

const pickTranslation = (base = {}) => {
  const candidates = [base.kjv_def, base.strongs_def, base.lemma, base.translit];

  for (const candidate of candidates) {
    if (typeof candidate !== 'string') {
      continue;
    }

    const trimmed = candidate.trim();
    if (trimmed) {
      return normaliseSpaces(trimmed);
    }
  }

  return '';
};

const loadStrongsDictionary = () => {
  const content = readFile(STRONGS_FILE);
  const objectSource = extractJsonObject(content, STRONGS_ANCHOR);
  return JSON.parse(objectSource);
};

const updateTranslations = () => {
  const strongsDict = loadStrongsDictionary();
  const greekDict = JSON.parse(normaliseIndentTokens(readFile(GREEK_DICT_FILE)));

  let updated = 0;
  const missing = [];

  for (const [entryKey, entryValue] of Object.entries(greekDict)) {
    if (!entryValue || typeof entryValue !== 'object') {
      continue;
    }

    const strongsNumber = typeof entryValue.strongs === 'string' ? entryValue.strongs.trim() : '';
    const greekWord = entryValue.grego || entryKey;

    if (!strongsNumber) {
      missing.push({ entryKey, reason: 'missing_strongs' });
      continue;
    }

    const strongsKey = `G${strongsNumber}`;
    const strongsEntry = strongsDict[strongsKey];

    if (!strongsEntry) {
      missing.push({ entryKey, greekWord, strongsKey, reason: 'strongs_not_found' });
      continue;
    }

    const translation = TRANSLATION_OVERRIDES[strongsKey] || pickTranslation(strongsEntry);
    const strongsDefinition =
      strongsEntry && typeof strongsEntry.strongs_def === 'string'
        ? normaliseSpaces(strongsEntry.strongs_def)
        : '';
    const verbeteValue = strongsDefinition ? `G${strongsNumber}: ${strongsDefinition}` : null;

    if (!translation) {
      missing.push({ entryKey, greekWord, strongsKey, reason: 'translation_not_found' });
      continue;
    }

    if (entryValue.traducao !== translation) {
      entryValue.traducao = translation;
      updated += 1;
    }

    if (verbeteValue && entryValue.verbete !== verbeteValue) {
      entryValue.verbete = verbeteValue;
      updated += 1;
    }
  }

  fs.writeFileSync(GREEK_DICT_FILE, `${JSON.stringify(greekDict, null, '\t')}\n`);

  return { updated, missing };
};

const main = () => {
  const { updated, missing } = updateTranslations();

  console.log(`Atualizações aplicadas: ${updated}`);

  if (missing.length > 0) {
    console.warn('Entradas sem atualização:', missing.slice(0, 10));
    if (missing.length > 10) {
      console.warn(`... e mais ${missing.length - 10} entradas.`);
    }
  }
};

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
