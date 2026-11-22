// Caixa é uma chave de consulta; diacríticos, espaços e formas originais ficam intactos.
const greekCaseKey = value => String(value).toLowerCase().normalize('NFC');

function buildCaseDictIndex(dict, formIndex = {}) {
  const index = new Map();
  for (const [form, entry] of Object.entries(dict)) {
    const key = greekCaseKey(form);
    if (!index.has(key)) index.set(key, []);
    const references = formIndex[form] || [{ strongs: entry.strongs, flexao: null }];
    for (const reference of references) {
      index.get(key).push({ entry, reference: { ...reference, grego: form } });
    }
  }
  return index;
}

module.exports = { greekCaseKey, buildCaseDictIndex };
