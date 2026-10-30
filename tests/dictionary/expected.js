// Independent oracle: original values, authorized LXX defaults and Greek keys.
// Does not call the migration/flattening implementation.
function expectedRecords(original) {
  return Object.values(original).map(entry => ({ ...entry,
    ocorrencias_lxx: Object.hasOwn(entry, 'ocorrencias_lxx') ? entry.ocorrencias_lxx : 0,
  }));
}
function expectedProjection(original) {
  const groups = {};
  for (const entry of expectedRecords(original)) (groups[entry.strongs] ||= []).push(entry);
  const dictionary = {};
  for (const group of Object.values(groups)) {
    for (const entry of group) {
      if (!Object.hasOwn(dictionary, entry.grego)) dictionary[entry.grego] = entry;
    }
  }
  return dictionary;
}
const canonical = value => Array.isArray(value) ? value.map(canonical) :
  value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
function bag(rows) {
  const counts = new Map();
  for (const row of rows) {
    const key = JSON.stringify(canonical(row));
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return counts;
}
module.exports = { expectedRecords, expectedProjection, bag };
