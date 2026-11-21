const crypto = require('node:crypto');
const identity = (reference, type, start, text, tokens) => 'r-' + crypto.createHash('sha256').update(JSON.stringify([reference, type, start, text, tokens])).digest('hex').slice(0, 24);
const key = item => JSON.stringify([item.start, item.text, item.tokens]);

function occurrenceRelations(reference, proposal, approved) {
  const compatible = approved && approved.text === proposal.text && JSON.stringify(approved.greek) === JSON.stringify(proposal.greek);
  const approvedByKey = new Map((compatible ? approved.segments : []).map(segment => [key(segment), segment]));
  const candidates = new Map(proposal.candidates.map(candidate => [key(candidate), { ...candidate }]));
  if (compatible) for (const segment of approved.segments) {
    if (!candidates.has(key(segment))) candidates.set(key(segment), { start: segment.start, text: segment.text, tokens: segment.tokens, evidence: [], priority: 'alta' });
  }
  const relations = [...candidates.values()].map(candidate => {
    const { start, text, tokens } = candidate;
    const accepted = approvedByKey.has(key(candidate));
    return { id: identity(reference, 'VINCULO', start, text, tokens), reference, type: 'VINCULO', start, text, tokens,
      status: accepted ? 'APROVADA' : candidate.review === 'RESULTADO_PARCIAL' ? 'PENDENTE' : 'PROPOSTA',
      evidence: [...(candidate.evidence || []), ...(accepted ? [{ kind: 'arquivo-aprovado', reference }] : [])],
      priority: candidate.priority, reason: accepted ? 'Vínculo já cadastrado no arquivo aprovado e válido para o texto atual.' :
        candidate.review === 'RESULTADO_PARCIAL' ? 'Geração parcial: não inferir unicidade.' : 'Proposta ainda não conferida.', conflicts: [] };
  }).sort((a, b) => a.start - b.start || b.text.length - a.text.length || a.id.localeCompare(b.id));
  for (let i = 0; i < relations.length; i++) for (let j = i + 1; j < relations.length; j++) {
    const a = relations[i], b = relations[j];
    if (!(a.start < b.start + b.text.length && b.start < a.start + a.text.length) && !a.tokens.some(token => b.tokens.includes(token))) continue;
    if (a.status === 'APROVADA' && b.status === 'APROVADA') throw Error(`${reference}: vínculos aprovados se sobrepõem ou disputam o mesmo token.`);
    a.conflicts.push(b.id); b.conflicts.push(a.id);
    for (const item of [a, b]) if (item.status !== 'APROVADA') {
      item.status = 'PENDENTE';
      item.reason = a.status === 'APROVADA' || b.status === 'APROVADA' ? 'Conflita com vínculo já aprovado.' : 'Mais de um candidato disputa este trecho ou token grego.';
    }
  }
  const notes = [];
  for (const item of compatible ? approved.unlinkedPortuguese || [] : []) {
    notes.push({ id: identity(reference, 'PORTUGUES_SEM_VINCULO_DIRETO', item.start, item.text, []), reference,
      type: 'PORTUGUES_SEM_VINCULO_DIRETO', start: item.start, text: item.text, tokens: [], status: 'APROVADA', reason: item.reason });
  }
  for (const item of compatible ? approved.untranslatedTokens || [] : []) {
    notes.push({ id: identity(reference, 'GREGO_SEM_VINCULO_DIRETO', null, null, [item.position]), reference,
      type: 'GREGO_SEM_VINCULO_DIRETO', start: null, text: null, tokens: [item.position], status: 'APROVADA', reason: item.reason });
  }
  for (const note of notes) {
    note.conflicts = [];
    for (const relation of relations) {
      const overlap = note.start !== null ? note.start < relation.start + relation.text.length && relation.start < note.start + note.text.length : relation.tokens.some(token => note.tokens.includes(token));
      if (!overlap) continue;
      if (relation.status === 'APROVADA') throw Error(`${reference}: vínculo aprovado contradiz nota aprovada de ausência de vínculo.`);
      relation.status = 'PENDENTE';
      relation.reason = 'Conflita com nota aprovada de ausência de vínculo direto.';
      relation.conflicts.push(note.id);
      note.conflicts.push(relation.id);
    }
  }
  for (const item of proposal.unmatchedPortuguese) {
    if (relations.some(relation => item.start >= relation.start && item.start + item.text.length <= relation.start + relation.text.length) || notes.some(note => note.start === item.start && note.text === item.text)) continue;
    notes.push({ id: identity(reference, 'PORTUGUES_SEM_CANDIDATO', item.start, item.text, []), reference,
      type: 'PORTUGUES_SEM_CANDIDATO', start: item.start, text: item.text, tokens: [], status: 'PENDENTE', reason: item.reason });
  }
  for (const item of proposal.unmatchedGreek) {
    if (relations.some(relation => relation.tokens.includes(item.position)) || notes.some(note => note.tokens.includes(item.position))) continue;
    notes.push({ id: identity(reference, 'GREGO_SEM_CANDIDATO', null, null, [item.position]), reference,
      type: 'GREGO_SEM_CANDIDATO', start: null, text: null, tokens: [item.position], status: 'PENDENTE', reason: 'Token grego sem candidato português.' });
  }
  const issues = [...proposal.issues];
  if (approved && !compatible) issues.push('Arquivo aprovado difere do texto ou grego atual: nenhuma aprovação foi transferida para estas propostas.');
  return { reference, text: proposal.text, greek: proposal.greek, relations, notes, issues,
    ...(proposal.evaluation ? { evaluation: proposal.evaluation } : {}) };
}
module.exports = { occurrenceRelations, identity };
