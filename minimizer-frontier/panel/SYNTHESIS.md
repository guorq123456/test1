**On your question, whether running this with Opus would change the results much (in short):**

- **On whether an exact rule is found or which conclusions hold: probably not much.** Every verdict in this explore comes from the exact verifier (`pnu.excess`), SAT/MaxSAT or exhaustive enumeration, so correctness does not depend on the model. Many lenses produced model-independent impossibility results, for example:
  - "walk rule + any tie-break" is UNSAT at ν=9, which two lenses found independently;
  - the Guenin route is blocked by odd-K5 minors;
  - no modular weighted sum works;
  - no 1-bit uniform recursion works past ν=11.

  A stronger model hits the same walls.
- **Where the model does matter: which hypotheses get tried, and how good the structural insight is.** The most valuable outputs this time came from that:
  - Theorem A, the rising-edge selector framework, the hereditary relations, and the 3-level minimizer;
  - R_A, the best near-rule (0,0,0,0,20,36), which came out of the "rising-edge selection" reformulation.

  In this run the model also made mistakes, and the verifiers caught two of them:
  - it presented the recursive lens's fitted table as an exact rule;
  - it labelled the shape criterion PROVED when the claim was false as stated.

  A stronger model might make fewer such mistakes, but the conclusions would not change.
- **Bigger levers than switching models:**
  - more compute, to finish the SAT runs that did not complete (the unconstrained ν≤15 pyramid search ran 30 CPU-minutes without an answer);
  - testing every candidate at the unseen ν=15 and 17;
  - running adversarial verification on the 7 lenses that never received it.
- **One caveat:** I don't know which model each panel subagent used, so this comparison has no controlled experiment behind it.

The full English report requested by the workflow follows.

---

# Panel synthesis: Open Problem 1 (σ = w = 2), 10 lenses

**Verification status.** Only 3 of the 10 lenses received adversarial verification: literature, recursive and theory. The other 7 (arithmetic, datamining, edgeview, runs, synthesis-search, repair, otherparams) have empty `verdicts`. Their claims rest on their own scripts and are marked [unverified] below.

## 1. Exact rules that survived verification

**None.** No exact rule survived.

The only lens that claimed one was **recursive**: a "2-bit state-passing pyramid", a 256-entry table PHI, with h_ν = first bit of g_ν. g_ν(W) = PHI[g_{ν−2} of the three contiguous (ν−2)-sub-windows, w_0, w_{ν−1}].

- Both verifiers refuted it, and both match the lead's independent check exactly. The profile for ν = 3..17 is **0,0,0,0,0,0, 264, 2324**: exact only on ν ≤ 13, which is the range SAT fitted it on.
- 136 of the 256 entries are used through ν = 13. ν = 15 needs 132 distinct keys, of which only 10 are new.
- Fixing the used entries, the extension to ν = 15 is UNSAT. A verifier reports that 94 of the 7710 length-17 cycles already have ≥2 mono steps using only fixed entries.
- The lens's own logs show that tables fitted on ν ≤ 11 all have excess **148 at ν = 13**.
- Conclusion: it is a fitted table, not a rule. The 1024-entry variant (adding w_1, w_{ν−2}) behaves the same: exact to 13, UNSAT when extended to 15.
- Its structural value is reported in §4.

Every other lens explicitly reports `exact_rule_found: false`.

## 2. Literature (verifier-confirmed claims only)

Both verifiers confirmed the literature lens (refuted: false, twice).

- **Max-cut of de Bruijn graphs is studied in only one paper, in the opposite regime.**
  - The paper: Flin, Raevskaya, Stimpert, Suomela, Yang, "2-Coloring Cycles in One Round" (arXiv:2603.04235, 2026).
  - DB_normal(n) has words of fixed length 3 over an alphabet of size n → ∞.
  - Exact values are known only for p_normal(2) = 0.25 and p_normal(4) ≈ 0.2422; there are SDP bounds 0.23879 ≤ p\* < 0.24118.
  - DB_normal(2) = B(2,3): "only 4 out of 16 edges are monochromatic", which equals the k=2 optimum of 10/16 charged.
  - Nothing in the literature treats max-cut, odd-cycle transversal, edge bipartization or frustration index of B(2,n) as n grows. The problem is therefore not known under another name. Proving it would be a new theorem about de Bruijn graphs.
- **Tightness of g′ for σ = w = 2 is purely computational.**
  - Kille et al. 2024, Bioinformatics, ILP with 1 ≤ w,k ≤ 12, 12 h, 128 threads: "Additionally, when σ = 2 and w = 2, the minimum density was equal to g′σ(w,k)."
  - Their Conjecture 1 covers only k ≡ 1 (mod w).
  - The mod-minimizer is optimal only as σ → ∞, and "does not quite match the lower bound for practical values of σ".
  - Open Problem 1 appears verbatim in Groot Koerkamp's survey.
- **Shur–Tziony–Orenstein 2026 (bioRxiv), Table A1, w = 2.**
  - Forward-scheme optima: 6, 10, 20, 37, 74, 143, 286, 1118, 4412 for k = 1–7, 9, 11. A verifier recomputed every value as equal to `bound_charged`.
  - Minimizers are worse by exactly one charged window at k = 2, 4, 6 (11/38/144 vs 10/37/143).
  - Caveat from verifier 2: this is *not* independent corroboration. The forward column comes from Kille et al.'s ILP.
- **Shur 2025 (arXiv:2506.05277), Theorem 11:** the minimum density of a (2,2,w)-minimizer is (2^w+w+5)/2^(w+2). This is the only closed-form optimum in the area. It concerns minimizers in the dual regime (k fixed, w varying).
- **No 2025–2026 paper** proves or constructs anything for σ = w = 2, or for k ≡ 1 (mod w) at finite σ.
- **Not verified:**
  - the Lempel D-morphism / Alhakim–Akinwande statement, which the lens itself flagged as a search summary;
  - HRSS17 was confirmed by verifier 2 only.

## 3. Theory: state of the existence-proof attempt

Theory lens verdicts were split. Verifier 1 refuted on a strict rule: a step labelled PROVED is false as stated. Verifier 2 did not refute. Both confirm the core results.

**Proved and verified: Theorem A.**
- For odd ν: h ∈ P(ν) ⟺ h∘Δ is an optimal colouring of B(2,ν+1), where Δ is the adjacent-XOR map.
- Identity: **excess(h,ν) = 2·mono(h) − N(ν+2)**. This was checked at ν = 3..11 and 3..9 by the two verifiers, with 0 failures.
- Corollaries:
  - P(ν) ⟺ **maxcut(B(2,ν)) = 2^{ν+1} − N(ν+2)/2**.
  - The even-weight necklaces alone partition E(B(2,ν)), so the odd-weight constraints are redundant.
  - Unified conjecture: maxcut(B(2,n)) = 2^{n+1} − N(n+1) for even n, and 2^{n+1} − N(n+2)/2 for odd n.
  - CP-SAT gives 2, 4, 12, 24, 54, 108, 226 for n = 1..7, all matching.
  - The datamining lens derived the same equivalence independently [unverified there].

**Shape criterion: false as stated.**
- The claim was 2^n parity constraints characterising bipartiteness of E−D.
- It actually characterises "E−D is a cut". It coincides with bipartiteness only when D is a transversal (one edge per necklace).
- Counterexamples: 218/300 (n=4) and 245/300 (n=6) for non-transversal D, plus an explicit n=2 counterexample.
- The count formula (49 at n=4, 5 at n=2) and the rank 2^n+1 survive.
- The side remark "Z_τ = walk of 1_τ0^n" is false; it holds for only 5/16 of τ at n=4.

**The polyhedral route is blocked.**
- B(2,6) and B(2,8) with all edges odd contain odd-K5 minors (verified at n=6 and n=8). By Guenin's theorem they are not weakly bipartite, so "maxcut = |E| − τ\*_odd" cannot be used in general.
- n=4 was actually proved odd-K5-free (q12b.out), although the summary says "undecided".
- What remains is the necessary fractional statement τ\*_odd(B(2,n)) = N(n+1). It holds for n ≤ 6 by LP. Its certificate cannot depend only on an edge's linear periods (infeasible at n = 4, 6, 8).

**Inductions from n−2 to n all fail by n = 8.**
- Restriction: 0–3/40 at n = 8.
- Extension: 24/60 sampled solutions are non-extendable; the verifier's uniform sample gives 5/30.
- Line-graph sub-selection: 0/59 at n = 8, 0/20 at n = 10.
- The nearest solution differs from the lifted colouring in 3–7/64 (n=6) and 7–14/256 (n=8) words, i.e. corrections are non-local.

**Most promising reduction, and where it breaks.** Theorem A plus the necklace-graph matching formulation (edgeview, [unverified]): P(ν) ⟺ a perfect matching of the bipartite necklace graph G_m whose complement in B(2,ν) is bipartite.
- It breaks at the **global** bipartiteness condition. Valid matchings are pinned down only by cyclic-word parity constraints up to length m+1 (6285 → 8 matchings at m=7). The cycle space needs walks of length up to n+4.
- Counting cannot close the gap: constraint bits exceed choice bits for n ≥ 8 (197 vs ~181), yet true counts dwarf the heuristic (26920 vs 46 at n=6). So the correlations matter, and nobody has identified them.

## 4. Best near-optimal rules and structural facts

**Excess profiles for ν = 3, 5, 7, 9, 11, 13 (excluding the fitted pyramid):**

| Rule | Lens | Excess | Status |
|---|---|---|---|
| **R_A**: rising-edge selector, deepest valley → majority → max(a,b) → majority → rise sum → majority → nearest centre | runs | **0,0,0,0,20,36** (odd-k charged: 0,0,0,0,10,18) | [unverified]; not tested at ν = 15, 17 |
| core rule + phase law + span walk | datamining | 0,0,0,8,36,116 | [unverified] |
| walk + synthesized size-3 tie-break | synthesis-search | 0,0,0,12,152,1296 | overfit: worse than plain walk from ν = 11 |
| 1-bit recursive closed form: h = MAJ(a,¬b,c), except a=1, c=0, w_0 = w_{ν−1} → b | recursive | 0,0,0,16,96,456 | interpretable; first rule exact past ν = 5 |
| previous reference (span tie-break) | PROBLEM.md | 0,4,4,20,64,176 | baseline |

Caveat on R_A: its stages were chosen because they remained SAT-feasible through ν = 13. It needs held-out evaluation at ν = 15 and 17 before being called a near-rule, given what happened to the pyramid.

**Structural facts any exact rule must satisfy** (V = verifier-confirmed; U = unverified lens script):

1. (V) excess = 2·mono(h) − N(ν+2). P(ν) is a max-cut statement, and only even-weight necklace constraints matter.
2. (V) No odd-K5-free polyhedral shortcut exists for n = 6, 8. Forced-out edges exist (exactly 8 at n=6, all reversal-closed). There are no forced-in edges besides the loops.
3. (U, datamining) **Forced core.** Classify each transition at position i by w_i ⊕ (i mod 2). If all transitions share a class, h equals that class.
   - This is exactly the forced set for ν ≤ 7: 8, 24, 66 windows, which is 2F(ν+2)−2.
   - It is contained in the exact SAT backbone 208, 562, 1568 at ν = 9, 11, 13.
4. (U, datamining) **Phase law.** Mixed windows with all transitions at odd positions share a free bit a; those with all transitions at even positions take 1−a. Hence every walk-negation-antisymmetric rule must err there.
5. (U, runs) **Four-class theorem.** Up to output and input complement, every solution is a *rising-edge selector*: h(W) = parity of the index of some "01" edge, and h(1^a0^b) = a mod 2.
   - The classes split solutions exactly 4/4/4/4 at ν=5 and 6272×4 at ν=7. SAT finds none outside them at ν = 9, 11, 13.
   - Consequences: pure run-length rules are impossible; exactly one jump of odd length per cycle is needed; "deepest valley" and "max min(a,b)" are the only per-edge scores that remain feasible to ν = 13.
6. (U, otherparams) **Minimizer form.**
   - Every P(ν) solution for ν ≤ 7 is a minimizer on (ν−1)-mers, with *opposite* ties at 0^ν and 1^ν. Equal ties are UNSAT for ν ≤ 13.
   - **3 rank levels suffice** (a proper 3-colouring λ of B(2,ν−1)), SAT for ν = 3..13; 2 levels are UNSAT. λ can be rc-invariant (ν ≤ 11).
   - This contradicts PROBLEM.md §4's "11 vs 10 gap" only for non-uniform ties at the constant windows. That is not a standard minimizer, so it does not contradict Shur et al.
7. (U, repair) **Hereditary chain.** An rc-anti chain h_3..h_13 exists with h(00W) = h(W11) = h_{ν−2}(W) and h(0W1) = 1 − h_{ν−2}(W). It fixes half the windows recursively. Adding W00 together with W11, or any 01/10 prefix or suffix relation, is infeasible by ν = 9.
8. (U, recursive) **Glitch bound.** A P(ν) solution evaluated on cycles of length ν+4 has ≤3 mono steps, and ≤5 on length ν+6. This is checked on all P(5)/P(7) solutions and on the pyramid's own levels.
   - 1-bit uniform recursions die at ν = 11 for every context tried.
   - The 2-bit state fits more data than any closed form, exact on ν ≤ 13. That suggests the recursion needs carried state, either more than 2 bits or growing with ν. It does not establish that a finite-state rule exists.
9. (U, synthesis-search + repair, independently) **The walk rule cannot be fixed by tie-breaking.**
   - Fixing it on unique-extrema windows is UNSAT at ν = 9 and 11. The certificate is 3 windows of 00011011011 with arcs 5, 3, 3, all odd.
   - The tie-breaking excess floor is ≥8 at ν=9 and ≥20 at ν=11.
   - Odd-arc lemma: three windows of an odd cyclic word whose pairwise arcs are all odd cannot all share h. This is a cheap screen for any candidate rule.
10. (U, arithmetic) **Seam-block law and non-locality.**
    - Flipping s_p moves the seam by an even distance, and the swept block contains both or neither of p+1, p+2. Zero violations.
    - The seam moves in about 2/3 of single-bit flips, so content-arithmetic anchors are ruled out.
    - No exact solution factors through any F(c·w mod M) at ν=5 for M ≤ 16, or through mod-m moments at ν=7.
11. (U, edgeview) **Single-run law and forced necklaces.**
    - For 0^a1^b the missing character is the 2nd or 2nd-to-last element of the odd run, never its centre for runs of length ≥5.
    - Exactly 6 forced necklaces exist at every m.
    - Greene–Kleitman / SCD matchings are excluded.
    - Palindromic representatives fail at m = 7.
12. (U, several lenses) **rc-anti-invariance is feasible but not necessary.** Only 8/16 P(5) and 448/25088 P(7) solutions have it, so PROBLEM.md's "must be rc-anti-invariant" is wrong as a necessary condition.
    - End-bit swap symmetry is feasible for ν = 5..13, but not together with rc-anti for ν ≥ 9.
    - Forbidding (dropped 0, added 1) mono steps is feasible for ν = 5..13.

## 5. Next steps (ranked) and coverage gaps

1. **Run held-out tests and adversarial verification on R_A, then attack its residue.**
   - It is the best rule (excess 20 and 36 at ν = 11, 13) and has had no verification and no test at ν = 15 or 17.
   - Its failures are confined to words with 3–6 rising edges that tie exactly (e.g. 0000100001001).
   - It is also cheap to check R_A against facts 3, 4 and 9 at ν = 11, 13.
2. **Stack the individually feasible constraints in one SAT model at ν ≤ 13, then 15:**
   - rising-edge class R with the deepest-valley/majority filter (fact 5);
   - the hereditary chain (fact 7);
   - the forced core and phase law (facts 3–4);
   - optionally an rc-invariant 3-level λ (fact 6).

   Each is SAT to 13 on its own. Joint feasibility would shrink the free set to a small residue and give a recursion that is not table-based. Infeasibility would identify which structural view is wrong.
3. **Settle the state-recursion question with more compute, using held-out ν.**
   - Run the unconstrained 2-bit pyramid at ν ≤ 15, unresolved after 30 CPU-minutes, and a 3-bit variant.
   - Always test at ν = 17 without having fitted on it.
   - UNSAT for fixed bit-width would mean the state must grow with ν. That is a sharp negative for finite-automaton constructions, and relevant to a Shur-style regular-language proof.

**What the panel did not cover:**
- Adversarial verification of 7 of 10 lenses.
- Held-out testing above ν = 13 for every rule except the pyramid.
- The Champarnaud–Hansel–Perrin minimum unavoidable set as a candidate D (named, untested).
- GF(2)-algebraic or LFSR / shift-register constructions; the arithmetic lens covered only mod-m integer sums.
- A regular-language or transfer-matrix proof in the style of Shur 2025.
- The existence direction through the fractional statement τ\*_odd = N(n+1) beyond n = 6 (the n = 8 LP did not finish).
- Probabilistic or entropy-compression existence arguments that exploit the correlation structure.
- Cross-lens consistency checks, e.g. whether the four-class theorem, the minimizer form and the hereditary chain hold simultaneously in one solution.
- The general k ≡ 1 (mod w) part of Open Problem 1. The otherparams lens only sampled σ ∈ {3,4} and w ∈ {3,4} at small k, and (2,4,5) got no optimum within 600 s.
- Unrestricted odd-k solutions that are not complement-invariant (the remaining 53840 − 16 at k′ = 5).

Key file: /home/user/test1/minimizer-frontier/PROBLEM.md. The lens scripts are under /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-*/; R_A is in lens-runs/best_rule.py and the fitted pyramid in lens-recursive/rule_state2_exact13.py.