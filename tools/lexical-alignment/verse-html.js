const { createHash } = require('node:crypto');
const { parseFragment, serialize, defaultTreeAdapter: tree } = require('parse5');

const WORD = /[\p{L}\p{N}][\p{L}\p{M}\p{N}]*(?:['’\-‐‑][\p{L}\p{N}][\p{L}\p{M}\p{N}]*)*/gu;
const OMITTED = new Set(['script', 'style', 'template', 'rt']);
const INTERACTIVE = new Set(['a', 'button', 'input', 'select', 'textarea', 'summary']);
const BREAKS = new Set(['br', 'hr', 'p', 'div', 'li', 'blockquote']);

function normalizePortuguese(value) {
  return value.normalize('NFC').toLocaleLowerCase('pt').replace(/’/g, "'").replace(/[‐‑]/g, '-');
}

function words(text) {
  return [...text.matchAll(WORD)].map(match => ({
    text: match[0],
    key: normalizePortuguese(match[0]),
    start: match.index,
    end: match.index + match[0].length,
  }));
}

function readVerse(html) {
  const fragment = parseFragment(html);
  const segments = [];
  let text = '';

  function visit(node, interactive = false) {
    const attributes = new Map((node.attrs || []).map(attr => [attr.name, attr.value]));
    if (OMITTED.has(node.tagName) || attributes.has('hidden') ||
        attributes.get('aria-hidden') === 'true' || attributes.has('data-lexical-note') ||
        ['doc-footnote', 'doc-noteref'].includes(attributes.get('role'))) return;
    if (node.nodeName === '#text') {
      segments.push({ node, interactive, start: text.length, end: text.length + node.value.length });
      text += node.value;
      return;
    }
    const boundary = BREAKS.has(node.tagName);
    if (boundary) text += ' ';
    const protectedContent = interactive || INTERACTIVE.has(node.tagName) ||
      attributes.has('tabindex') || attributes.has('contenteditable') ||
      ['button', 'link'].includes(attributes.get('role')) ||
      attributes.get('class')?.split(/\s+/).includes('tooltip');
    for (const child of node.childNodes || []) visit(child, protectedContent);
    if (boundary) text += ' ';
  }

  visit(fragment);
  const additions = [...text.matchAll(/\[[^\[\]]+\]/g)];
  const tokens = words(text).map((word, index) => ({
    ...word,
    position: index + 1,
    editorial: additions.some(match => word.start > match.index && word.end < match.index + match[0].length),
    segments: segments.filter(segment => word.start < segment.end && word.end > segment.start),
  }));
  const signature = 'v1:' + createHash('sha256').update(JSON.stringify(
    tokens.map(token => [token.key, token.editorial]),
  )).digest('hex');
  return { fragment, tokens, text: text.trim(), signature };
}

function element(tag, attributes) {
  return tree.createElement(tag, 'http://www.w3.org/1999/xhtml',
    Object.entries(attributes).map(([name, value]) => ({ name, value })));
}

function renderVerse(html, verse, results, prefix) {
  const contentIds = new Map();
  const edits = new Map();
  for (const [index, result] of results.entries()) {
    if (!result.association.length || result.renderingBlocked) continue;
    const token = verse.tokens[index];
    const key = JSON.stringify(result.association.map(entry => [entry.form, entry.strong, entry.flexion]));
    if (!contentIds.has(key)) {
      contentIds.set(key, { id: prefix + '-lex-' + (contentIds.size + 1), entries: result.association });
    }
    const { id } = contentIds.get(key);
    token.segments.forEach((segment, segmentIndex) => {
      const ranges = edits.get(segment.node) || [];
      ranges.push({
        start: Math.max(token.start, segment.start) - segment.start,
        end: Math.min(token.end, segment.end) - segment.start,
        id,
        label: token.segments.length > 1 ? token.text : '',
        primary: segmentIndex === 0,
      });
      edits.set(segment.node, ranges);
    });
  }
  if (!edits.size) return { body: html, details: '' };

  for (const [node, ranges] of edits) {
    const parent = node.parentNode;
    let offset = 0;
    for (const range of ranges) {
      tree.insertTextBefore(parent, node.value.slice(offset, range.start), node);
      const attributes = { class: 'lexical-trigger', 'data-lexical-content': range.id };
      if (range.primary) {
        attributes.type = 'button';
        attributes['aria-describedby'] = range.id;
        if (range.label) attributes['aria-label'] = range.label;
      }
      const trigger = element(range.primary ? 'button' : 'span', attributes);
      tree.insertText(trigger, node.value.slice(range.start, range.end));
      tree.insertBefore(parent, trigger, node);
      offset = range.end;
    }
    tree.insertTextBefore(parent, node.value.slice(offset), node);
    tree.detachNode(node);
  }

  const details = tree.createDocumentFragment();
  for (const { id, entries } of contentIds.values()) {
    const tooltip = element('span', { id, hidden: '', 'data-pagefind-ignore': 'all' });
    for (const entry of entries) {
      const row = element('span', { class: 'lexical-tooltip-entry' });
      const greek = element('strong', { lang: 'grc' });
      tree.insertText(greek, entry.form);
      tree.appendChild(row, greek);
      for (const field of [entry.transliteration, entry.morphology, entry.meaning]) {
        if (field) tree.insertText(row, ' · ' + field);
      }
      tree.appendChild(tooltip, row);
    }
    tree.appendChild(details, tooltip);
  }
  return { body: serialize(verse.fragment), details: serialize(details) };
}

module.exports = { normalizePortuguese, words, readVerse, renderVerse };
