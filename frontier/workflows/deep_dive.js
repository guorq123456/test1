export const meta = {
  name: 'deep-dive-theorems',
  description: 'For each candidate identity: rigorous proof + computation, then independent adversarial verification and literature novelty check, with one repair round',
  phases: [
    { title: 'Prove', detail: 'prover writes a complete proof and extends computations' },
    { title: 'Check', detail: 'independent verifier (own code, hunts gaps) and novelty searcher in parallel' },
    { title: 'Repair', detail: 'fix gaps the verifier found, then re-verify once' },
  ],
}

const ENV = `Environment: Linux container, 4 CPU cores shared with several other agents (keep heavy jobs under ~10 minutes), 15 GB RAM. Python 3.11 with sympy, numpy, scipy, mpmath, gmpy2, numba, networkx, python-sat, z3; PARI/GP at /usr/bin/gp; gcc and Rust. Local OEIS snapshot (Oct 1 2026): terms in /tmp/claude-0/oeis/stripped.gz, names in /tmp/claude-0/oeis/names.gz, full entries for many sequences at /tmp/claude-0/oeis/oeisdata/seq/<A123>/<A123456>.seq; any entry can be printed with: git -C /tmp/claude-0/oeis/oeisdata show HEAD:seq/A200/A200881.seq (fetches on demand). Earlier triage scratch code is under /tmp/claude-0/oeis/work/triage*/ (grep for the A-numbers). Network: https://oeis.org, https://arxiv.org and https://export.arxiv.org/api/query work via curl; you can load WebSearch/WebFetch via ToolSearch if available.`

const PROOF = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    theorem: { type: 'string', description: 'Precise statement of what is proved (all definitions, offsets, ranges).' },
    proof_path: { type: 'string', description: 'Path of a markdown file containing the complete, self-contained proof.' },
    proof_summary: { type: 'string', description: 'The key idea of the proof in a few sentences.' },
    computations: { type: 'string', description: 'What was computed independently and to what range; mismatches if any.' },
    status: { type: 'string', enum: ['PROVED', 'PROVED_CONDITIONAL', 'NUMERICAL_ONLY', 'REFUTED', 'FAILED'] },
    whats_new: { type: 'string', description: 'Exactly what this adds relative to the current OEIS entries (which claims there are labeled conjecture/empirical, what links are missing).' },
  },
  required: ['id', 'theorem', 'proof_path', 'proof_summary', 'computations', 'status', 'whats_new'],
}
const VER = {
  type: 'object',
  properties: {
    independent_computation: { type: 'string', description: 'Your own implementation from the OEIS definitions: method, range, agreement.' },
    gaps: { type: 'array', items: { type: 'string' }, description: 'Each concrete gap/error in the proof, with location.' },
    verdict: { type: 'string', enum: ['SOUND', 'FIXABLE_GAPS', 'WRONG'] },
    details: { type: 'string' },
  },
  required: ['independent_computation', 'gaps', 'verdict', 'details'],
}
const NOV = {
  type: 'object',
  properties: {
    searches: { type: 'string', description: 'What you searched (OEIS full-text search for the A-numbers/terms/keywords, arXiv, web) and where.' },
    prior_art: { type: 'string', description: 'Any prior statement of this identity/bijection/result, with exact quotes and links; or none found.' },
    verdict: { type: 'string', enum: ['NEW', 'PARTIALLY_KNOWN', 'KNOWN'] },
    details: { type: 'string' },
  },
  required: ['searches', 'prior_art', 'verdict', 'details'],
}

const proverPrompt = t => `You are a research mathematician. Below is a candidate identity between OEIS sequences discovered by a coincidence search plus a quick triage. Your job: produce a COMPLETE, RIGOROUS, self-contained proof (or a refutation), and independently extend the computational evidence.

Target: ${t.title}
OEIS pairs: ${t.pairs}
Claim: ${t.claim}
Notes from triage: ${t.notes}

Steps:
1. Read the full OEIS entries involved (exact definitions, offsets, existing formulas/comments, what is labeled conjecture or empirical).
2. Implement each sequence directly from its OEIS definition (brute force where feasible) and confirm you reproduce the stored terms; extend beyond the stored data.
3. Write the proof in ${'`'}/tmp/claude-0/deep/${t.id}/proof.md${'`'}: theorem statement with offsets, all lemmas with proofs, every inequality with explicit constants, and how finitely many small cases are checked by computation (name the script). No hand-waving: someone will try hard to break it.
4. If the claim is false, find and verify the first counterexample instead.

${ENV} Work in /tmp/claude-0/deep/${t.id}/.`

const verifierPrompt = (t, p, round) => `You are an adversarial referee. A colleague claims the following about OEIS sequences. Try hard to REFUTE it. Default to finding problems; a proof is SOUND only if every step holds.

Target: ${t.title}
Pairs: ${t.pairs}
Claimed theorem: ${p.theorem}
Claimed status: ${p.status}
Proof file: ${p.proof_path} (read it in full)
Their computations: ${p.computations}

Do both: (a) write your OWN implementation of the sequences directly from the OEIS definitions (do not reuse their code; only look at it afterwards to diagnose disagreements) and check the identity on as large a range as feasible; (b) check every step of the proof: definitions/offsets match OEIS exactly, lemmas really hold (test them by brute force on small cases), inequalities have correct constants, the finite check covers exactly the cases the argument leaves open. List each concrete gap.
${round > 1 ? 'This is a re-check after the author repaired earlier gaps; check the repairs especially carefully.' : ''}
${ENV} Work in /tmp/claude-0/deep/${t.id}/verify${round}/ (create it).`

const noveltyPrompt = (t, p) => `Determine whether the following result is ALREADY KNOWN anywhere (OEIS entries other than the two in question, papers, arXiv, books, MathOverflow, websites).

Target: ${t.title}
Pairs: ${t.pairs}
Result: ${p.theorem}
Key idea: ${p.proof_summary}

Search thoroughly: OEIS full-text search (https://oeis.org/search?q=...&fmt=text for the A-numbers, for distinctive runs of terms, and for keywords), any sequence that cross-references both, arXiv and web searches for the key objects (e.g. the bijection or the inequality used). Report exact quotes and links for anything relevant. Classify NEW only if nothing states this identity or an equivalent statement that makes it immediate.
${ENV}`

const repairPrompt = (t, p, v) => `Your proof of the result below was refereed and gaps were found. Repair every gap (or, if the result is false, say so and give the counterexample). Update the proof file in place and summarize.

Target: ${t.title}
Theorem: ${p.theorem}
Proof file: ${p.proof_path}
Referee verdict: ${v.verdict}
Referee gaps:
- ${v.gaps.join('\n- ')}
Referee details: ${v.details}
Referee's independent computation: ${v.independent_computation}

${ENV} Work in /tmp/claude-0/deep/${t.id}/.`

const results = await pipeline(
  args,
  t => agent(proverPrompt(t), { label: `prove:${t.id}`, phase: 'Prove', schema: PROOF }),
  (p, t) => {
    if (!p) return null
    return parallel([
      () => agent(verifierPrompt(t, p, 1), { label: `verify:${t.id}`, phase: 'Check', schema: VER }),
      () => agent(noveltyPrompt(t, p), { label: `novelty:${t.id}`, phase: 'Check', schema: NOV }),
    ]).then(([v, nov]) => ({ t, p, v, nov }))
  },
  async r => {
    if (!r || !r.v || r.v.verdict !== 'FIXABLE_GAPS') return r
    const p2 = await agent(repairPrompt(r.t, r.p, r.v), { label: `repair:${r.t.id}`, phase: 'Repair', schema: PROOF })
    if (!p2) return r
    const v2 = await agent(verifierPrompt(r.t, p2, 2), { label: `reverify:${r.t.id}`, phase: 'Repair', schema: VER })
    return { ...r, p2, v2 }
  },
)
return results.filter(Boolean).map(r => ({ id: r.t.id, prove: r.p, verify: r.v, novelty: r.nov, repair: r.p2 ?? null, reverify: r.v2 ?? null }))
