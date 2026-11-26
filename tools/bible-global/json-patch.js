// Locate JSON values without reserializing unrelated entries, keys or whitespace.
function ranges(text) {
  let cursor = 0;
  const found = new Map();
  const space = () => { while (/\s/u.test(text[cursor] || '') && cursor < text.length) cursor++; };
  function string() {
    const start = cursor++;
    while (cursor < text.length) {
      if (text[cursor] === '\\') cursor += 2;
      else if (text[cursor++] === '"') return JSON.parse(text.slice(start, cursor));
    }
    throw Error('JSON inválido.');
  }
  function value(parts) {
    space(); const start = cursor, children = [];
    if (text[cursor] === '{') {
      cursor++; space();
      while (text[cursor] !== '}') {
        const name = string(); space(); if (text[cursor++] !== ':') throw Error('JSON inválido.');
        value([...parts, name]); children.push(name); space();
        if (text[cursor] !== ',') break;
        cursor++; space();
      }
      if (text[cursor++] !== '}') throw Error('JSON inválido.');
    } else if (text[cursor] === '[') {
      cursor++; space(); let i = 0;
      while (text[cursor] !== ']') {
        value([...parts, String(i++)]); space(); if (text[cursor] !== ',') break; cursor++; space();
      }
      if (text[cursor++] !== ']') throw Error('JSON inválido.');
    } else if (text[cursor] === '"') string();
    else { while (cursor < text.length && !/[\s,}\]]/u.test(text[cursor])) cursor++; }
    if (cursor === start) throw Error('JSON inválido.');
    found.set(JSON.stringify(parts), { start, end: cursor, children });
  }
  JSON.parse(text); value([]); return found;
}
function setValue(raw, parts, data) {
  const map = ranges(raw), existing = map.get(JSON.stringify(parts));
  const newline = raw.includes('\r\n') ? '\r\n' : '\n';
  const indentation = offset => /^\s*/u.exec(raw.slice(raw.lastIndexOf('\n', offset) + 1, offset))[0];
  const format = (value, indent) => JSON.stringify(value, null, 2).replace(/\n/gu, newline + indent);
  if (existing) {
    const old = JSON.parse(raw.slice(existing.start, existing.end));
    if (JSON.stringify(old) === JSON.stringify(data)) return raw;
    return raw.slice(0, existing.start) + format(data, indentation(existing.start)) + raw.slice(existing.end);
  }
  const parentParts = parts.slice(0, -1), parent = map.get(JSON.stringify(parentParts));
  if (!parent || raw[parent.start] !== '{') throw Error('Caminho JSON não encontrado.');
  const indent = indentation(parent.start), childIndent = indent + '  ';
  const addition = JSON.stringify(parts.at(-1)) + ': ' + format(data, childIndent);
  if (!parent.children.length) return raw.slice(0, parent.start + 1) + newline + childIndent + addition + newline + indent + raw.slice(parent.end - 1);
  const last = map.get(JSON.stringify([...parentParts, parent.children.at(-1)]));
  return raw.slice(0, last.end) + ',' + newline + childIndent + addition + raw.slice(last.end);
}
module.exports = { ranges, setValue };
