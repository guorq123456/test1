# Refutation of the Parity Conjecture for Independence Polynomials of Generalized Petersen Graphs (arXiv:2601.03293, Conjecture 4.1)

**Slug:** `pandey-parity` · **Status:** verified kill (Gate 4 passed 2026-06-11; Gate 5 this document, 2026-06-11)

---

## Abstract (~120 words)

We refute, in both directions, Conjecture 4.1 of R. Pandey, *Parity-Dependent
Real-Rootedness in Independence Polynomials of Generalized Petersen Graphs*
(arXiv:2601.03293, Jan 2026), which asserts that I(GP(n,k),x) is real-rooted
if and only if k is even. GP(9,2) has k even but I(GP(9,2),x) = 1 + 18x +
126x² + 438x³ + 801x⁴ + 747x⁵ + 303x⁶ + 27x⁷, which has exactly 5 real roots
(exact Sturm count); GP(7,3) and GP(3,1) have k odd but real-rooted
independence polynomials. Moreover GP(7,2) ≅ GP(7,3), so the conjectured
predicate is not isomorphism-invariant. All verdicts are exact-arithmetic
(integer recursion, Sturm chains over ℚ), cross-checked by an independent
Rust brute force, and upheld by a hostile Codex referee. An exhaustive exact
scan finds eleven violations with 3 ≤ n ≤ 14.

---

## 1. Result

> **Result.** Conjecture 4.1 ("Parity Conjecture") of arXiv:2601.03293 is **false in both
> directions**, and its predicate is **not isomorphism-invariant** (hence not well-posed as
> a property of the underlying graph).
>
> Verbatim conjecture (frozen 2026-06-11 from the source):
> *"For all integers n ≥ 2k+1, the independence polynomial I(GP(n,k),x) has only real
> roots if and only if k is even."*
>
> - **"if" direction false:** GP(9,2) has k = 2 even, n = 9 ≥ 2k+1 = 5, but
>   I(GP(9,2),x) is **not** real-rooted.
> - **"only if" direction false:** GP(7,3) has k = 3 odd, n = 7 ≥ 2k+1 = 7, but
>   I(GP(7,3),x) **is** real-rooted. A second, minimal witness: GP(3,1) (the triangular
>   prism), k = 1 odd, with real-rooted I = 1 + 6x + 6x².
> - **Not isomorphism-invariant:** GP(7,2) ≅ GP(7,3) (explicit isomorphism below), with
>   k even on one side and odd on the other; the conjecture therefore assigns
>   contradictory predictions to a single graph.

### Provenance (frozen statement)

- Source: R. Pandey, *Parity-Dependent Real-Rootedness in Independence Polynomials of
  Generalized Petersen Graphs*, arXiv:2601.03293, submitted 2026-01-05 (v1, sole version
  as of 2026-06-11).
- URLs (accessed 2026-06-11): https://arxiv.org/abs/2601.03293 ,
  https://arxiv.org/html/2601.03293v1
- Definition 2.1 (verbatim conventions used throughout): for integers n ≥ 3 and
  1 ≤ k < n/2, GP(n,k) has vertices u₀…u_{n−1}, v₀…v_{n−1}; edges uᵢu_{i+1} (outer
  cycle), vᵢv_{i+k} (inner chords), uᵢvᵢ (spokes), indices mod n. I(G,x) = Σ iₖ(G)xᵏ
  with iₖ the number of independent sets of size k.
- Author's stated validation (verbatim): computations "for all k ∈ {1,2,3,4} and for
  20 ≤ n ≤ 30", roots "verified to numerical precision 10⁻¹⁰". The paper contains no
  gcd/connectivity/large-n escape hatch and never mentions the classical
  kk′ ≡ ±1 (mod n) isomorphism or any case with n < 20. The failure mode was
  **insufficient parameter coverage** (no case with n < 20 or k > 4 was tested), not
  numerical tolerance: in the tested window the even-k cases examined may genuinely be
  real-rooted, consistent with our scan pattern.

## 2. Status before this work

Open: conjecture posed January 2026 in arXiv:2601.03293; no citing work and no published
or preprint refutation found at selection time (2026-06-11) or at the Gate-5 re-check
(also 2026-06-11; see §6). OpenAlex records `cited_by_count = 0` for
DOI 10.48550/arXiv.2601.03293.

## 3. The counterexamples (inline)

All coefficient lists are exact integers, low degree first. "Real roots" is the exact
count of distinct real roots of the (verified squarefree) polynomial by Sturm's theorem
over ℚ — no floating point enters any verdict.

**(a) GP(9,2) — kills the "if" direction.** k = 2 even, 18 vertices, 27 edges.

    I(GP(9,2), x) = 1 + 18x + 126x² + 438x³ + 801x⁴ + 747x⁵ + 303x⁶ + 27x⁷

Degree 7, squarefree, exactly **5** distinct real roots ⇒ **not real-rooted**.
(Informational numeric location of the conjugate pair: −0.856549 ± 0.055540i; the
verdict itself is exact.)

**(b) GP(7,3) — kills the "only if" direction.** k = 3 odd, n = 7 ≥ 2·3+1.

    I(GP(7,3), x) = 1 + 14x + 70x² + 154x³ + 147x⁴ + 49x⁵

Degree 5, squarefree, exactly **5** distinct real roots ⇒ **real-rooted**.

**(c) GP(3,1) — second "only if" violation, minimal.** The triangular prism, k = 1 odd:
I = 1 + 6x + 6x², real-rooted (it is claw-free, so real-rootedness also follows from
Chudnovsky–Seymour).

**(d) GP(7,2) ≅ GP(7,3) — the predicate is not isomorphism-invariant.** Since
2·3 ≡ −1 (mod 7), the classical map

    u_j ↦ v′_{3j mod 7},   v_j ↦ u′_{3j mod 7}

is an isomorphism GP(7,2) → GP(7,3): it is verified vertex-by-vertex as a bijection on
all 14 vertices carrying all 21 edges bijectively onto all 21 edges. Consistently,
I(GP(7,2)) = I(GP(7,3)) = [1, 14, 70, 154, 147, 49]. One side has k even, the other
k odd, so the conjectured biconditional assigns contradictory predictions to one and the
same graph: the parameter-pair statement, though syntactically well-defined, is not an
isomorphism-invariant characterization of a graph property.

The full edge lists of GP(9,2) and GP(7,3), the isomorphism map, and all coefficients
are stored in `certificate.json`.

## 4. Artifact

All files in `C:\Users\jacks\source\repos\maths\problems\p2-factory\kills\pandey-parity\`:

| File | Role |
|---|---|
| `certificate.json` | Frozen provenance, edge lists, coefficients, Sturm counts, isomorphism map, full 42-row scan table for 3 ≤ n ≤ 14 |
| `check_pandey_parity.py` | Clean-room checker (pure Python 3, stdlib only, exact arithmetic); `--selftest` runs unit + mutation tests |
| `bf_gp.rs` / `bf_gp.exe` | Independent Rust brute force: enumerates all 2^(2n) subsets for every legal GP(n,k), 3 ≤ n ≤ 14 |
| `rust_bruteforce.log` | Rust output; agrees with Python on every coefficient of all 42 polynomials |
| `gen_certificate.py` | Certificate generator (provenance of `certificate.json`) |
| `run.log` | Full passing checker run (selftest + statement + scan + verdict, exit 0) |

## 5. Verification

**Checker A — clean-room Python (this kill's Gate-4 agent).**
`check_pandey_parity.py` was written from scratch (the discovery scripts were never
opened). It (1) builds GP(n,k) from Definition 2.1; (2) computes I(G,x) by the exact
integer recursion I(G) = I(G−v) + x·I(G−N[v]) memoized on bitmasks; (3) cross-checks
GP(9,2), GP(7,3), GP(3,1) by pure-Python enumeration of all 2^18 / 2^14 / 2^6 subsets;
(4) decides real-rootedness exactly via the squarefree part p/gcd(p,p′) and a Sturm
chain over ℚ (real-rooted iff distinct-real-root count equals squarefree degree;
multiplicities are handled correctly since p and its squarefree part have identical root
sets — in fact all 42 polynomials are squarefree); (5) verifies the GP(7,2) ≅ GP(7,3)
isomorphism edge-by-edge; (6) rescans all 42 legal pairs 3 ≤ n ≤ 14 and compares every
field against `certificate.json`, exiting nonzero on any mismatch.

To verify (under a minute):

    cd problems\p2-factory\kills\pandey-parity
    python check_pandey_parity.py --selftest    # unit + mutation tests
    python check_pandey_parity.py               # full check vs certificate.json; exit 0

**Checker B — independent language/algorithm (Rust).** `bf_gp.rs` shares no code or
algorithm with Checker A: it brute-forces every subset of vertices (2^(2n) per graph)
for all 42 graphs. Rebuild and diff:

    rustc -O bf_gp.rs && .\bf_gp.exe            # compare with rust_bruteforce.log

**Mutation testing.** Tampered coefficients, a tampered scan-table verdict, a corrupted
isomorphism map (both a swapped image and a non-bijective map), and a dropped violation
were each injected; every corruption is rejected (exit 1). The selftest embeds known
real-rooted/non-real-rooted polynomials and a literature anchor,
I(Petersen) = I(GP(5,2)) = [1, 10, 30, 30, 5].

**Orchestrator smoke test.** `problems\p2-factory\verify_kills.py` (section 5,
"Pandey parity") independently rebuilds GP(9,2) and GP(7,3) by a third recursion,
re-derives both coefficient lists, and confirms the real/non-real verdicts numerically
(numpy roots) — a deliberately different, floating-point sanity layer on top of the
exact checkers.

**Codex cross-examination (hostile referee, GPT-5.5, full shell+network, 2026-06-11).**
All five audit tasks passed: statement fidelity ("Conjecture 4.1 is exactly the all-n
parity statement. I found no textual gcd/proper/large-n escape hatch"); independent
recomputation with its own code plus SymPy exact Sturm (reproduced both key polynomials,
spot-checked GP(12,2) 9/9 and GP(10,4) 8/8 real, independently rescanned 3 ≤ n ≤ 14 and
got exactly the claimed violation list); isomorphism verification; checker audit ("no
load-bearing bug", fuzzed Sturm verdicts against SymPy with 0 discrepancies); and a
prior-art kill-check (none found). Verdict verbatim: "Uphold the refutation. Both
directions of Conjecture 4.1 fail exactly under the paper's own definitions. … the
parameter-pair statement is syntactically well-defined, yet it is not an
isomorphism-invariant characterization of a graph property. That is a serious
mathematical defect, and GP(7,2) ≅ GP(7,3) is a clean witness." Codex's one hardening
finding (load-bearing `assert`s disabled under `python -O`) was fixed — checks now raise
unconditionally and the selftest refuses to run under `-O` — and the full run was
re-verified (exit 0) afterwards.

## 6. Openness re-check (fresh kill-check, 2026-06-11)

Queries run today and their results:

1. Web search `arXiv 2601.03293 generalized Petersen independence polynomial` — only the
   paper itself and unrelated independence-number/domination papers. No refutation.
2. Web search `"independence polynomial" "generalized Petersen" real roots counterexample
   conjecture 2026` — the conjecture is described as open; no counterexample literature.
3. Web search `Pandey "parity conjecture" independence polynomial real-rooted refuted` —
   explicit result: "the search results do not contain information about this conjecture
   being refuted".
4. Web search `"GP(9,2)" OR "GP(7,3)" independence polynomial real-rooted counterexample`
   — nothing relevant beyond the source paper.
5. Web search `"Parity-Dependent Real-Rootedness" cited OR refutation OR disproof OR
   counterexample` — no citing or refuting work.
6. OpenAlex API for DOI 10.48550/arXiv.2601.03293 — `cited_by_count = 0`.
7. arXiv abstract page — still **v1 only**, no replacement, comment, or withdrawal; the
   conjecture is still stated in the abstract.
8. arXiv API full-text query `all:"generalized Petersen" AND all:"independence
   polynomial"`, sorted by submission date descending — the **only** entry returned is
   2601.03293v1 itself; no follow-up or refutation preprint exists on arXiv.
9. Author's code repository `github.com/Rohan-Pandey1729/polynomial-independence` —
   0 issues open or closed (no one has reported a counterexample there).
10. Semantic Scholar API — HTTP 429 (rate-limited, twice); superseded by the OpenAlex
    citation count above.

**Conclusion: no prior or concurrent refutation found as of 2026-06-11.** (Phrased per
doctrine as "none found", not "none exists".)

## 7. Extension findings

Full exact scan of **every** legal GP(n,k) with 3 ≤ n ≤ 14, 1 ≤ k < n/2 (42 graphs;
complete coefficient/Sturm table in `certificate.json → scan_table`). The violations of
Conjecture 4.1 are exactly:

    (3,1), (7,3), (9,2), (9,4), (10,2), (11,2), (11,4), (13,4), (14,2), (14,4), (14,6)

- All violations with 9 ≤ n ≤ 14 are "if"-direction failures (k even, not real-rooted),
  with exact real-root counts: GP(9,2) 5/7, GP(9,4) 5/7, GP(10,2) 6/8, GP(11,2) 6/8,
  GP(11,4) 7/9, GP(13,4) 7/11, GP(14,2) 9/11, GP(14,4) 9/11, GP(14,6) 10/12.
- All 42 independence polynomials are squarefree.
- The same classical map (2·4 ≡ −1 mod 9) gives GP(9,2) ≅ GP(9,4), and consistently both
  appear in the violation list, as they must.
- The even-k cases that do *not* violate — e.g. GP(12,2) (9/9 real), GP(12,4), GP(13,2)
  (10/10), GP(13,6), GP(10,4) (8/8) — are genuinely real-rooted, which is consistent
  with the author having observed only real roots in the window 20 ≤ n ≤ 30, k ≤ 4 he
  tested.

## 8. What this does not show

- It does **not** show that real-rootedness of I(GP(n,k),x) lacks structure — only that
  parity of k is not the criterion. Some isomorphism-invariant reformulation (or a
  restriction, e.g. to k even with extra congruence conditions on n) might still hold;
  our scan data (11 violations and 31 conforming cases in n ≤ 14) neither proposes nor
  rules out such a refinement.
- It does **not** contradict the author's computations: we found no even-k
  counterexample inside his tested window 20 ≤ n ≤ 30, k ∈ {1,2,3,4} (which we did not
  exhaustively scan); the defect was insufficient parameter coverage, not (so far as we
  can tell) numerical error.
- It says nothing about the paper's other content (transfer-matrix computations, root
  accumulation curves for odd k, log-concavity observations); only Conjecture 4.1 is
  refuted. Note log-concavity is weaker than real-rootedness and is not addressed here.
- The scan is exhaustive only for 3 ≤ n ≤ 14; the density of violations for larger n is
  not established.
- "No prior refutation found as of 2026-06-11" is a statement about our searches (§6),
  not a proof that none exists.

## 9. Publication grouping

**Publication grouping:** best bundled with the **two Graffiti spectral kills**
(`graffiti-143`, `graffiti-154`) as a "counterexamples to conjectures on roots/spectra
of graph polynomials" note — all three refute real-spectrum/root-location claims for
graph-associated polynomials via small explicit graphs with exact-arithmetic
certificates. A workable alternative is the **two TxGraffiti-family kills**
(`davila-conj9` records) under a "small counterexamples to recent computer-era graph
conjectures" framing; the **three solubilizer kills** (`solubilizer-a1/-a13/-a16`) are
group-theoretic and do not fit. This kill also stands alone if needed: single
conjecture, single paper, both directions plus a well-posedness defect.
