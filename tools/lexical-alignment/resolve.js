const { normalizePortuguese, words } = require('./verse-html');

function append(map, key, value) {
  if (!map.has(key)) map.set(key, []);
  map.get(key).push(value);
}

// Case and grave/acute variation. Keep breathings, iota subscripts and the
// dictionary's markers that distinguish otherwise identical spellings.
function comparableGreek(value) {
  return value.normalize('NFD').toLowerCase().replace(/\u0300/g, '\u0301').normalize('NFC');
}

function broadGreek(value) {
  return comparableGreek(value).normalize('NFD').replace(/\p{M}/gu, '');
}

function glosses(value) {
  if (typeof value !== 'string') return [];
  return value.split(/[,;\n]+/).flatMap(part => {
    const trimmed = part.trim();
    if (!trimmed.includes('/')) return [trimmed];
    // Slash joins simple lexical alternatives such as "e/também". Mixed
    // phrases can contain nested alternatives and require editorial review.
    const options = trimmed.split('/').map(option => option.trim());
    return options.every(option => option && !/\s/u.test(option)) ? options : [];
  }).map(part => part.trim())
    .filter(part => /^[\p{L}\p{M}\p{N}\s'’\-‐‑]+$/u.test(part))
    .map(part => words(part).map(word => word.key)).filter(parts => parts.length);
}

function createLexicon(dictionary, formIndex, { allowVariant = () => true } = {}) {
  const exact = new Map();
  const variants = new Map();
  const broad = new Map();
  const registered = new Set();

  for (const [form, references] of Object.entries(formIndex)) {
    for (const { strongs, flexao } of references) {
      const group = dictionary[strongs];
      const flex = group.flexoes[flexao];
      const key = form.normalize('NFC');
      const phrases = new Map();
      const preferred = glosses(flex.pt);
      const meaning = flex.verbete ?? group.verbete ?? '';
      for (const field of [flex.pt, flex.traducao]) {
        for (const phrase of glosses(field)) {
          phrases.set(phrase.join(' '), phrase);
          registered.add(phrase.join(' '));
        }
      }
      const entry = {
        form, strong: strongs, flexion: flexao, lemma: group.lema,
        transliteration: flex.transliteracao,
        morphologyCode: flex.abrev_morf,
        morphology: flex.morfologia || flex.abrev_morf,
        meaning,
        phrases: [...phrases.values()],
        preferred,
        lexicalHints: glosses(meaning.replace(/^G\d+\s*:\s*/u, '')),
      };
      append(exact, key, entry);
      append(variants, comparableGreek(key), entry);
      append(broad, broadGreek(key), entry);
    }
  }

  function forVerse(tokens) {
    const present = new Map();
    const suggestions = [];
    const unidentified = [];
    for (const [index, token] of tokens.entries()) {
      const form = token.lemma.normalize('NFC');
      const directly = exact.get(form);
      const available = directly ?? (allowVariant(form) ? variants.get(comparableGreek(form)) : undefined) ?? [];
      const entries = available.filter(entry =>
        (token.strongs === undefined || String(token.strongs) === entry.strong) &&
        (token.abrev_morf === undefined || token.abrev_morf === entry.morphologyCode));
      if (!entries.length) {
        unidentified.push({ form, position: index + 1 });
        if (allowVariant(form)) {
          for (const entry of broad.get(broadGreek(form)) || []) {
            if (allowVariant(entry.form)) {
              suggestions.push({ ...entry, form, dictionaryForm: entry.form,
                identity: JSON.stringify([form, entry.strong, entry.flexion]) });
            }
          }
        }
      }
      for (const entry of entries) {
        const spelling = allowVariant(form) ? comparableGreek(form) : form;
        const key = JSON.stringify([spelling, entry.strong, entry.morphologyCode, entry.morphology,
          entry.meaning, entry.phrases, entry.preferred]);
        if (!present.has(key)) {
          present.set(key, { ...entry, form, observedForms: new Set(), dictionaryForm: entry.form, identity: key });
        }
        present.get(key).observedForms.add(form);
      }
    }
    return { entries: [...present.values()], suggestions, unidentified };
  }

  return { forVerse, registered };
}

function phraseMatches(tokens, start, phrase) {
  return phrase.every((part, offset) => {
    const token = tokens[start + offset];
    return token && !token.editorial && token.key === part;
  });
}

function matchPhrases(tokens, entries, field = 'phrases') {
  const first = new Map();
  const matches = tokens.map(() => new Map());
  for (const entry of entries) {
    for (const phrase of entry[field]) append(first, phrase[0], { phrase, entry });
  }
  for (const [start, token] of tokens.entries()) {
    for (const { phrase, entry } of first.get(token.key) || []) {
      if (phraseMatches(tokens, start, phrase)) {
        for (let index = start; index < start + phrase.length; index += 1) {
          matches[index].set(entry.identity, entry);
        }
      }
    }
  }
  return matches.map(match => [...match.values()]);
}

function indexExceptions(data, book, chapter, numbers, duplicateKeys = []) {
  const references = new Map();
  const issues = duplicateKeys.map(key => ({ key, reason: 'duplicate_json_key' }));
  if (issues.length) return { references, issues };
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { references, issues: [{ reason: 'invalid_exception_file' }] };
  }
  for (const [word, forms] of Object.entries(data)) {
    const key = normalizePortuguese(word);
    if (words(word).length !== 1 || words(word)[0].key !== key ||
        !forms || typeof forms !== 'object' || Array.isArray(forms)) {
      issues.push({ word, reason: 'invalid_exception_word' });
      continue;
    }
    for (const [form, refs] of Object.entries(forms)) {
      if (!form || !/\p{Script=Greek}/u.test(form) || !Array.isArray(refs) || !refs.length) {
        issues.push({ word, form, reason: 'invalid_exception_form' });
        continue;
      }
      for (const reference of refs) {
        const match = typeof reference === 'string' && /^([\p{L}\p{N}]+) ([1-9]\d*):([1-9]\d*):([1-9]\d*)$/u.exec(reference);
        if (!match || !match.slice(2).every(number => Number.isSafeInteger(Number(number)))) {
          issues.push({ word, form, reference, reason: 'invalid_reference_format' });
          continue;
        }
        if (match[1] !== book || Number(match[2]) !== chapter || !numbers.has(Number(match[3]))) {
          issues.push({ word, form, reference, reason: 'unknown_reference' });
          continue;
        }
        const group = references.get(reference) || { word, key, forms: [], valid: true };
        const normalizedForm = form.normalize('NFC');
        if (group.key !== key || group.forms.includes(normalizedForm)) {
          group.valid = false;
          issues.push({ word, form, reference, reason: group.key !== key ? 'conflicting_words' : 'duplicate_reference' });
        } else {
          group.forms.push(normalizedForm);
        }
        references.set(reference, group);
      }
    }
  }
  return { references, issues };
}

function resolveException(exception, token, entries, candidates, signature, approvedSignature, automatic) {
  if (!exception.valid) return { reason: 'invalid_exception' };
  if (token.editorial || exception.key !== token.key) return { reason: 'reference_word_changed' };
  if (signature !== approvedSignature) {
    return { reason: approvedSignature ? 'reference_outdated' : 'reference_unverified' };
  }
  const analysis = [];
  for (const form of exception.forms) {
    const matching = entries.filter(entry => entry.observedForms.has(form));
    if (matching.length !== 1) {
      return { reason: matching.length ? 'greek_homograph' : 'greek_form_not_identified' };
    }
    analysis.push({ ...matching[0], form });
  }
  if (analysis.length === 1 && !candidates.some(entry => entry.identity === analysis[0].identity)) {
    return { reason: 'review_lexical_equivalence' };
  }
  return {
    analysis,
    reason: automatic && analysis.length === 1 ? 'redundant_exception' : 'validated_exception',
  };
}

function resolveVerse(verse, greekTokens, lexicon, references, exceptions, approvedSignature,
  isGrammatical = () => false) {
  const { entries, suggestions, unidentified } = lexicon.forVerse(greekTokens);
  const matches = matchPhrases(verse.tokens, entries);
  const preferred = matchPhrases(verse.tokens, entries, 'preferred');
  const results = verse.tokens.map((token, index) => {
    const reference = references + ':' + token.position;
    const matchedForms = new Set(matches[index].flatMap(entry => [...entry.observedForms]));
    const candidates = entries.filter(entry => [...entry.observedForms].some(form => matchedForms.has(form)));
    const grammaticalAlternative = isGrammatical(token.key) && !preferred[index].length;
    const automatic = candidates.length === 1 && !grammaticalAlternative;
    const exception = exceptions.get(reference);
    const result = {
      word: token.text,
      key: token.key,
      reference,
      position: token.position,
      candidates,
      association: [],
      renderingBlocked: token.segments.some(segment => segment.interactive),
      status: 'pending_lexical_review',
      reason: lexicon.registered.has(token.key) ? 'no_registered_match_in_verse' : 'word_not_registered',
    };
    if (exception) {
      result.exception = exception.forms;
      const decision = resolveException(
        exception, token, entries, candidates, verse.signature, approvedSignature, automatic,
      );
      result.reason = decision.reason;
      result.status = decision.analysis ? 'resolved_by_exception' : 'exception_requires_review';
      result.association = decision.analysis || [];
    } else if (token.editorial) {
      result.status = 'no_greek_equivalent';
      result.reason = 'marked_editorial_insertion';
    } else if (candidates.length === 1) {
      if (!automatic) {
        result.reason = 'grammatical_alternative_needs_context';
        result.suggestions = candidates.map(entry => ({ ...entry, evidence: 'traducao' }));
      } else {
        result.status = 'resolved_automatically';
        result.reason = 'unique_flexion_equivalence';
        result.association = candidates;
      }
    } else if (candidates.length > 1) {
      result.status = 'unresolved_ambiguity';
      result.reason = new Set(candidates.map(entry => entry.form)).size < candidates.length ?
        'greek_homograph' : 'competing_greek_forms';
    }
    return result;
  });

  const spellingHints = matchPhrases(verse.tokens, suggestions);
  const meaningHints = matchPhrases(verse.tokens, entries, 'lexicalHints');
  for (const [index, result] of results.entries()) {
    if (result.status !== 'pending_lexical_review' &&
        result.reason !== 'review_lexical_equivalence') continue;
    const hints = [
      ...(result.suggestions || []),
      ...spellingHints[index].map(entry => ({ ...entry, evidence: 'unverified_spelling' })),
      ...meaningHints[index].map(entry => ({ ...entry, evidence: 'verbete' })),
    ];
    result.suggestions = [...new Map(hints.reverse().map(entry => [entry.identity, entry])).values()];
    if (!result.candidates.length && spellingHints[index].length && result.status === 'pending_lexical_review') {
      result.reason = 'unverified_greek_flexion';
    }
  }
  return { results, unidentified };
}

module.exports = { createLexicon, indexExceptions, resolveVerse };
