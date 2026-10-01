export const meta = {
  name: 'qunimodal-synthesize',
  description: 'Step 5: synthesis by a fresh non-explorer, then default-reject review of its proof',
  phases: [
    { title: 'Synthesize', detail: 'fresh synthesizer gets only constraints, conjectures, failures' },
    { title: 'Review synthesis', detail: 'proof review of the synthesizer output' },
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
const passed = args.passed
phase('Synthesize')
const SYN = { type: 'object', properties: {
  strongest_conjecture: { type: 'string' }, answer_shape: { type: 'string' },
  rule_file: { type: 'string', description: 'Python predict(r,a,b)/domain(r,a) implementing the conjecture' },
  decision_tools_considered: { type: 'string', description: 'Existing decision/proof procedures for this kind of statement, whether applicable, what was tried' },
  proof_file: { type: 'string' }, proof_status: { type: 'string', enum: ['PROOF_COMPLETE', 'PARTIAL', 'NONE'] },
  nonexistence: { type: 'string', description: 'If evidence points to some answer shape not existing: the non-existence statement and its proof or status' },
  necessary_constraints: { type: 'array', items: { type: 'object', properties: { constraint: { type: 'string' }, basis: { type: 'string', enum: ['已证明', '有限范围计算', '反例'] }, independence_witness: { type: 'string', description: 'A candidate satisfying all other constraints but violating this one, or "可能冗余"' }, type: { type: 'string', enum: ['可行', '必要'] } }, required: ['constraint', 'basis', 'independence_witness', 'type'] } },
}, required: ['strongest_conjecture', 'answer_shape', 'rule_file', 'decision_tools_considered', 'proof_file', 'proof_status', 'nonexistence', 'necessary_constraints'] }
const syn = await agent(`You are the synthesizer. You did not take part in exploration. You receive only: necessary constraints, conjectures, and failure records.
PROBLEM: ${args.problem}
REVIEWED-AND-PASSED results (constraints): ${JSON.stringify(passed)}
CONJECTURES/RULES with hidden-holdout results: ${args.holdout_summary}
FAILURE RECORDS (paths that did not work, with numbers): ${args.failures}
LITERATURE (proven facts): ${JSON.stringify(args.lit_items)}
Tasks:
1. Write the strongest conjecture compatible with ALL constraints, and its answer shape (closed form / finite-state / asymptotic / non-existence). Implement it as a Python predict(r,a,b) (+domain) file.
2. Before proving, check whether an existing decision or proof procedure covers this kind of statement (e.g. parametric lattice-point counting / Barvinok quasi-polynomials, Presburger arithmetic, Zeilberger-type creative telescoping, Walnut for automatic sequences, cylindrical algebraic decomposition) and say concretely whether it applies.
3. Attempt a proof, written step by step with numbered lemmas. If the evidence points to 'some answer shape does not exist', state that non-existence as a theorem and try to prove it.
4. List necessary constraints with basis (已证明/有限范围计算/反例), an independence witness (candidate satisfying the others but violating this one) or '可能冗余', and label each 可行 or 必要.
You may compute freely (no box restriction). Work in /tmp/claude-0/qu/synth/r${args.round}/. ${ENV}`, { label: 'synthesize', phase: 'Synthesize', schema: SYN })

phase('Review synthesis')
let synRev = null
if (syn && syn.proof_status !== 'NONE') synRev = await agent(`DEFAULT: REJECT. Referee the synthesizer's proof step by step; try to break every lemma by brute force; formalize what you can.
PROBLEM: ${args.problem}
STATEMENT: ${syn.strongest_conjecture}
PROOF FILE: ${syn.proof_file}
Work in /tmp/claude-0/qu/review/r${args.round}/synth-proof/. ${ENV}`, { label: 'review-synth-proof', phase: 'Review synthesis', schema: PRF, model: REV_MODEL })
return { synthesis: syn, synthesis_review: synRev }
