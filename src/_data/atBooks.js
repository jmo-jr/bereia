const fs = require('node:fs');
const path = require('node:path');

const names = {
  gn: 'Gênesis', ex: 'Êxodo', lv: 'Levítico', nm: 'Números', dt: 'Deuteronômio',
  js: 'Josué', jz: 'Juízes', rt: 'Rute', '1sm': '1 Samuel', '2sm': '2 Samuel',
  '1rs': '1 Reis', '2rs': '2 Reis', '1cr': '1 Crônicas', '2cr': '2 Crônicas',
  '1esd': '1 Esdras', '2esd': '2 Esdras', ed: 'Esdras', ne: 'Neemias',
  est: 'Ester', jdt: 'Judite', tb: 'Tobias', '1mc': '1 Macabeus',
  '2mc': '2 Macabeus', '3mc': '3 Macabeus', '4mc': '4 Macabeus',
  jo: 'Jó', sl: 'Salmos', pv: 'Provérbios', ec: 'Eclesiastes', ct: 'Cantares',
  sb: 'Sabedoria', eclo: 'Eclesiástico', is: 'Isaías', jr: 'Jeremias',
  lm: 'Lamentações', br: 'Baruc', ez: 'Ezequiel', dn: 'Daniel',
  os: 'Oseias', jl: 'Joel', am: 'Amós', ob: 'Obadias', jn: 'Jonas',
  mq: 'Miqueias', na: 'Naum', hc: 'Habacuque', sf: 'Sofonias',
  ag: 'Ageu', zc: 'Zacarias', ml: 'Malaquias', odes: 'Odes',
  'sl-sal': 'Salmos de Salomão', 'ep-jr': 'Epístola de Jeremias',
  sus: 'Susana', 'sus-th': 'Susana (Teodócio)', bel: 'Bel e o Dragão',
  'bel-th': 'Bel e o Dragão (Teodócio)', 'dn-th': 'Daniel (Teodócio)',
  'or-mn': 'Oração de Manassés', 'tb-ba': 'Tobias (BA)', 'tb-s': 'Tobias (S)',
  'js-a': 'Josué (A)', 'js-b': 'Josué (B)', 'jz-a': 'Juízes (A)', 'jz-b': 'Juízes (B)',
};

module.exports = () => {
  const directory = path.join(__dirname, '../interlinear/at');
  if (!fs.existsSync(directory)) return [];
  const ntSlugs = new Set(require('./ntBooks.json').map(book => book.permalink.split('/').filter(Boolean).pop()));
  return fs.readdirSync(directory).filter(file => file.endsWith('.json')).map(file => {
    const id = path.basename(file, '.json');
    const slug = id === 'jo' ? 'jó' : id;
    if (ntSlugs.has(slug)) throw new Error(`Endereço da LXX em conflito com o NT: ${slug}`);
    const chapters = JSON.parse(fs.readFileSync(path.join(directory, file), 'utf8'));
    const name = names[id] || id;
    return { id, name, heading: name, slug, permalink: `/interlinear/${slug}/`, chapters: chapters.length, chapterNumbers: chapters.map(chapter => chapter.chapter) };
  }).sort((a, b) => {
    const order = Object.keys(names);
    const index = id => order.includes(id) ? order.indexOf(id) : order.length;
    return index(a.id) - index(b.id) || a.id.localeCompare(b.id);
  });
};
