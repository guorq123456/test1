export const meta = {
  name: 'qunimodal-review',
  description: 'Step 4: default-reject review by a different model (reimplementers, proof referees, literature recheck)',
  phases: [
    { title: 'Review', detail: 'numeric/rule: 2 reimplementers (description-only, problem-only); proofs: lemma-by-lemma; literature recheck' },
  ],
}
// args: { problem, claims:[{id, kind:'rule'|'numeric'|'proof', description, statement, numbers, files}], lit_items, failures, holdout_summary, round }
const REV_MODEL = 'fable'
const NUM = { type: 'object', properties: {
  reproduced: { type: 'boolean', description: 'Your independent implementation reproduces every number/prediction claimed, in the claimed range' },
  own_numbers: { type: 'string' },
  new_instances_tested: { type: 'string', description: 'Out-of-range instances YOU chose and tested, how many, results' },
  new_instances_ok: { type: 'boolean' },
  verdict: { type: 'string', enum: ['PASS', 'REJECT'] },
  reasons: { type: 'string' } }, required: ['reproduced', 'own_numbers', 'new_instances_tested', 'new_instances_ok', 'verdict', 'reasons'] }
const PRF = { type: 'object', properties: {
  steps_checked: { type: 'string', description: 'Each step/lemma with OK or the problem found' },
  lemma_counterexample_attempts: { type: 'string', description: 'For each lemma: what you tried to break it with (brute force ranges), results' },
  formalization: { type: 'string', description: 'What was formalized (Lean/z3/exhaustive certificate) or why not possible here' },
  verdict: { type: 'string', enum: ['ACCEPT', 'REJECT'] },
  reasons: { type: 'string' } }, required: ['steps_checked', 'lemma_counterexample_attempts', 'formalization', 'verdict', 'reasons'] }
const LIT = { type: 'object', properties: {
  search_log: { type: 'array', items: { type: 'object', properties: { query: { type: 'string' }, source: { type: 'string' }, result: { type: 'string', enum: ['找到', '未找到'] }, note: { type: 'string' } }, required: ['query', 'source', 'result', 'note'] } },
  item_checks: { type: 'string', description: 'For each literature item given: did you open the source, is the quote verbatim, is the classification right' },
  new_items: { type: 'string', description: 'Relevant sources missed by step 0, with verbatim quotes and links' },
  verdict: { type: 'string', enum: ['CONFIRMED', 'CORRECTED'] } }, required: ['search_log', 'item_checks', 'new_items', 'verdict'] }
const ENV = 'Linux, 4 cores shared, Python3 (numpy, sympy, z3, python-sat), PARI/GP, gcc. Network for arXiv/web via curl; WebSearch/WebFetch via ToolSearch if available. Do NOT read anything under /root/ and do not read the original explorer folders unless the instructions allow it.'
phase('Review')
const reviews = await parallel(args.claims.flatMap(c => {
  const dir = `/tmp/claude-0/qu/review/r${args.round}/${c.id}`
  if (c.kind === 'proof') return [() => agent(`DEFAULT: REJECT. You are a referee checking a proof step by step. Accept only if every step holds.
PROBLEM CONTEXT: ${args.problem}
CLAIMED STATEMENT: ${c.statement}
PROOF FILE (read it fully): ${c.files}
Tasks: check every step; for EACH lemma, try to construct a counterexample by brute force over as large a range as feasible; check that the proof's finite/computational parts are actually rerunnable and cover what is claimed. Formalize what you can (z3 for bounded lemmas, exhaustive certificates); say what could not be formalized and why. Numerical agreement is NOT proof. Work in ${dir}-proof/. ${ENV}`, { label: `proof:${c.id}`, phase: 'Review', schema: PRF, model: REV_MODEL }).then(v => ({ id: c.id, kind: 'proof', v }))]
  return [
    () => agent(`DEFAULT: REJECT. Reimplement from a TEXT DESCRIPTION ONLY and check a claimed result.
TEXT DESCRIPTION (this is all you get about how it was produced): ${c.description}
CLAIMED NUMBERS / PREDICTIONS TO REPRODUCE: ${c.numbers}
Write your own code from this description (do not look for anyone else's code). Reproduce the claimed numbers in the claimed range. Then choose and test NEW instances outside that range (larger k, larger a_i, other r), using your own ground-truth computation of unimodality. PASS only if everything reproduces and your new instances show no mismatch. Work in ${dir}-A/. ${ENV}`, { label: `revA:${c.id}`, phase: 'Review', schema: NUM, model: REV_MODEL }).then(v => ({ id: c.id, kind: 'A', v })),
    () => agent(`DEFAULT: REJECT. Check a claim starting ONLY from the original problem.
ORIGINAL PROBLEM: ${args.problem}
CLAIM (mathematical statement): ${c.statement}
CLAIMED NUMBERS TO REPRODUCE: ${c.numbers}
Implement the ground truth (coefficients of P and weak unimodality) yourself from the problem statement, implement the claim from its mathematical statement, reproduce the claimed numbers, then test NEW instances outside the claimed range that you choose. PASS only if everything reproduces and there is no mismatch. Work in ${dir}-B/. ${ENV}`, { label: `revB:${c.id}`, phase: 'Review', schema: NUM, model: REV_MODEL }).then(v => ({ id: c.id, kind: 'B', v })),
  ]
}).concat(args.with_lit ? [() => agent(`DEFAULT: assume the literature report is incomplete or wrong. Re-check it by the same standard: at least 8 phrasings including adjacent-field translations; every query logged as 找到/未找到; never write that something is confirmed unsolved; any 'already known' claim must quote the source verbatim and compare definitions/parameters/conditions item by item; partial matches are 文献连线 with differences; cite original text and links, not memory.
PROBLEM: ${args.problem}
STEP-0 ITEMS TO RECHECK (JSON): ${JSON.stringify(args.lit_items)}
Work in /tmp/claude-0/qu/review/r1/lit/. ${ENV}`, { label: 'lit-recheck', phase: 'Review', schema: LIT, model: REV_MODEL }).then(v => ({ id: 'literature', kind: 'lit', v }))] : []))
const R = reviews.filter(Boolean)
const passed = args.claims.filter(c => {
  const mine = R.filter(x => x.id === c.id)
  if (c.kind === 'proof') return mine.some(x => x.v?.verdict === 'ACCEPT')
  return mine.length === 2 && mine.every(x => x.v?.verdict === 'PASS' && x.v?.reproduced && x.v?.new_instances_ok)
})
log(`passed review: ${passed.map(c => c.id).join(', ') || 'none'}`)

return { reviews: R, passed: passed.map(c => c.id) }
