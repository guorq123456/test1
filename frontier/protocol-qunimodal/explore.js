export const meta = {
  name: 'qunimodal-explore',
  description: 'Step 2: independent explorers, one path each, no shared conclusions, fit-box only',
  phases: [{ title: 'Explore', detail: 'each explorer follows exactly one path; failure is reported with numbers' }],
}
// args: { lit: string, paths: [{id, title, instructions, prior?}] }
const OUT = {
  type: 'object',
  properties: {
    path_id: { type: 'string' },
    stayed_on_path: { type: 'boolean' },
    outcome: { type: 'string', enum: ['RULE', 'PROOF', 'NONEXISTENCE_EVIDENCE', 'COUNTEREXAMPLE', 'FAILED'] },
    candidates_tried_total: { type: 'integer', description: 'All candidate rules/approaches/objects tried, including discarded ones' },
    candidates_file: { type: 'string', description: 'File listing every candidate tried (including discarded) with its fit-box error count' },
    rules: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, rule_file: { type: 'string', description: 'Python file defining predict(r,a,b)->bool and optionally domain(r,a)->bool' },
      description_text: { type: 'string', description: 'Plain-text description of the rule sufficient to reimplement it without the code' },
      fit_range: { type: 'string' }, free_parameters: { type: 'integer' }, fit_errors: { type: 'integer' } },
      required: ['name', 'rule_file', 'description_text', 'fit_range', 'free_parameters', 'fit_errors'] } },
    numeric_claims: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, script: { type: 'string', description: 'rerunnable script that produces the number' }, range: { type: 'string' } },
      required: ['claim', 'script', 'range'] } },
    proofs: { type: 'array', items: { type: 'object', properties: {
      statement: { type: 'string' }, proof_file: { type: 'string', description: 'step-by-step proof, numbered lemmas, each step checkable' } },
      required: ['statement', 'proof_file'] } },
    failure_report: { type: 'string', description: 'If the path did not work: where it broke, with numbers. Empty otherwise.' },
  },
  required: ['path_id', 'stayed_on_path', 'outcome', 'candidates_tried_total', 'candidates_file', 'rules', 'numeric_claims', 'proofs', 'failure_report'],
}
const COMMON = (p) => `You are an independent explorer on ONE assigned path of a research problem. Other explorers work on other paths; you will not see their results and must not try to find them.

PROBLEM. For integers r>=2, k>=1, a_1..a_k>=1, b>=1 let P(q) = [a_1]_q ... [a_k]_q * [b]_{q^r}, with [n]_q = 1+q+...+q^{n-1} and [b]_{q^r} = 1+q^r+...+q^{r(b-1)}. Unimodal means weakly: c_0<=...<=c_m>=...>=c_N. Determine exactly for which parameters P is unimodal. Origin: arXiv:2605.12822 Conjecture 5.4 (if r|a_i for some i, or b<=1+sum floor(a_i/r), then unimodal; and for k<=3 or r<=3 the condition is also necessary). The necessity clause for r=3 is known to be false: (1+q)^6(1+q^3) is unimodal.

LITERATURE (step 0 findings, for context only):
${args.lit}

HARD RULES.
- FIT BOX: you may compute P (or anything derived from specific parameter values) ONLY for r in {2,...,6}, k<=8, every a_i<=12, b<=60. Computing any instance outside this box is forbidden, including "just to check". If your path needs larger instances, say so in the failure report instead.
- Work only inside /tmp/claude-0/qu/explore/${p.id}/ (create it). Do not read other folders under /tmp/claude-0/qu/explore/ or anything under /root/. A ground-truth checker you may use (within the box) is /tmp/claude-0/qu/tools/uni (stdin lines "r k a1..ak b", prints 1/0) and /tmp/claude-0/qu/tools/uni_ref.py.
- Follow ONLY your assigned path. Do not switch to another approach to have something to report. If the path does not work, stop and report FAILED with numbers (what you tried, how many candidates, how badly they failed).
- Every numeric statement must come from a rerunnable script you name. Record every candidate you tried (including discarded ones) in a candidates file with its error count in the fit box, and report the total.
- Any rule you propose must be a Python file defining predict(r, a, b) -> bool (a is a sorted list) and, if the rule only claims part of the parameter space, domain(r, a) -> bool. Also give a plain-text description sufficient to reimplement it, the fit range, and the number of free parameters you fitted. Do NOT test it outside the fit box; the coordinator will test it on hidden data.
- Universal claims are conjectures unless you write a step-by-step proof (numbered lemmas, every step checkable) in a file.
Python 3 with numpy, sympy, mpmath, networkx, z3, python-sat; PARI/GP; gcc.

YOUR PATH: ${p.title}
${p.instructions}
${p.prior ?? ''}`
phase('Explore')
const res = await parallel(args.paths.map(p => () => agent(COMMON(p), { label: `explore:${p.id}`, phase: 'Explore', schema: OUT })))
return res.filter(Boolean)
