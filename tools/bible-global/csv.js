const hazardous = /^[=+\-@\t\r\n']/u;
const safe = value => { const text = String(value ?? ''); return hazardous.test(text) ? "'" + text : text; };
const restore = value => value.startsWith("'") && hazardous.test(value.slice(1)) ? value.slice(1) : value;
function encode(rows) {
  return '\uFEFF' + rows.map(row => row.map(value => '"' + safe(value).replaceAll('"', '""') + '"').join(';')).join('\r\n') + '\r\n';
}
function parse(input, delimiter = ';') {
  const text = input.replace(/^\uFEFF/u, ''), rows = [];
  let row = [], cell = '', quoted = false, endedQuote = false;
  const pushCell = () => { row.push(restore(cell)); cell = ''; endedQuote = false; };
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') { cell += '"'; i++; } else { quoted = false; endedQuote = true; }
      } else cell += char;
      continue;
    }
    if (char === delimiter) pushCell();
    else if (char === '\r' || char === '\n') {
      if (char === '\r' && text[i + 1] === '\n') i++;
      pushCell();
      if (row.some(value => value !== '')) rows.push(row);
      row = [];
    } else if (char === '"' && !cell && !endedQuote) quoted = true;
    else {
      if (endedQuote || char === '"') throw Error('CSV inválido: texto fora das aspas ou aspas não escapadas.');
      cell += char;
    }
  }
  if (quoted) throw Error('CSV inválido: aspas não fechadas.');
  if (cell || row.length || endedQuote) { pushCell(); if (row.some(value => value !== '')) rows.push(row); }
  return rows;
}
module.exports = { encode, parse };
