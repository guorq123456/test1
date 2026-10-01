# RESULTS — master catalog of verified results in this repository

Last updated: **2026-06-12**. Companion files: [`verify_all.py`](verify_all.py)
(runs every mechanical check below and prints a PASS/FAIL table) and
[`VALIDATION.md`](VALIDATION.md) (a guide for an outside mathematician: what each
check does and does not establish). The verification doctrine these results
were produced under is summarized in [`VALIDATION.md`](VALIDATION.md).

**One command verifies everything:**

```
git clone https://github.com/demonstrandum-research/artifacts.git
cd artifacts
python verify_all.py            # default battery; --full adds long redundant layers
python verify_all.py --strict   # SKIPs (e.g. Lean absent) become failures: full zero-trust mode
```

A SKIP means the corresponding result was **not** verified on that machine (the
summary says so explicitly); use `--strict` if you require every check to run.

Fresh runs on the build machine (Ryzen 9 9950X3D, Windows 11, Python 3.11,
2026-06-12): default battery **33 checks, 33 PASS, 0 FAIL, 0 SKIP in 681 s
(11.3 min, machine under concurrent load; 4-7 min idle)**; `--full` battery
**36 checks, 36 PASS, 0 FAIL, 0 SKIP in 1546 s (25.8 min)** (the extra time is
dominated by the redundant exact-cyclotomic Sun layer, ~9-17 min depending on
load, and the n = 8 Elizalde–Luo ground truth, ~4 min). Lean checks are skipped with
a message if `lake` is absent; Rust checkers are rebuilt via cargo only if the
prebuilt binaries are missing. Timings assume the in-tree Rust binaries and the
Lean build cache are present; a from-scratch Lean+mathlib build adds hours on
first run.

**Verification grades** used below:

| grade | meaning |
|---|---|
| **kernel** | the entire claim is a Lean 4 theorem checked by the Lean kernel; axiom audit shows only `propext`, `Classical.choice`, `Quot.sound` (standard mathlib axioms), no `sorry`, no `native_decide` |
| **dual-checker** | the certificate is accepted by ≥ 2 independently written checkers (different agents, ideally different languages), validated by mutation testing where applicable |
| **audit-panel** | acceptance rests on one banked runnable checker plus adversarial audits / clean-room recomputations by independent agents and a different model family (recorded in logs), and/or on a human-readable proof audited by multiple hostile panels with exhaustive machine verification of every lemma |

All results were produced under the doctrine of `FRAMEWORK.md` §1: no claim is
accepted on an LLM's word; the unit of progress is an artifact on disk plus a
checker that accepts it; statements are frozen verbatim from the authoritative
source before any attack.

---

## Contents

1. [IRIS Conjecture 6.1 refuted](#1-iris-conjecture-61-nuevamirada--refuted) — dual-checker
2. [Borsuk Conjecture 3 (arXiv:2508.20009) disproved in Lean](#2-discrete-borsuk-conjecture-3-of-arxiv250820009--disproved-kernel-checked) — kernel
3. [Graffiti Conjecture 143 refuted](#3-graffiti-conjecture-143-refuted) — dual-checker
4. [Graffiti Conjecture 154 refuted](#4-graffiti-conjecture-154-refuted-std-dev-reading) — dual-checker
5. [TxGraffiti/Davila Conjecture 9 refuted](#5-txgraffitidavila-conjecture-9-refuted) — dual-checker
6. [Pandey parity conjecture refuted](#6-pandey-parity-conjecture-refuted-both-directions) — dual-checker
7. [Solubilizer Conjecture A.1 refuted](#7-solubilizer-conjecture-a1-refuted) — dual-checker
8. [Solubilizer Conjecture A.13 refuted](#8-solubilizer-conjecture-a13-refuted) — audit-panel
9. [Solubilizer Conjecture A.16 refuted](#9-solubilizer-conjecture-a16-refuted) — audit-panel
10. [Sun Conjecture 4.6 refuted](#10-sun-conjecture-46-arxiv210807723-refuted) — dual-checker
11. [Koch–Narayan Conjecture 1 refuted](#11-kochnarayan-conjecture-1-refuted) — dual-checker
12. [C(13) ≥ 36 record (no 5 on a sphere)](#12-c13--36-for-the-no-5-on-a-sphere-grid-problem) — dual-checker
13. [Elizalde–Luo {1132, 3312} conjecture proved in Lean 4](#13-elizaldeluo-1132-3312-conjecture--proved-kernel-checked) — kernel

---

## 1. IRIS Conjecture 6.1 ("NuevaMirada") — REFUTED

**Grade: dual-checker** (Python + Rust, independently written; 33-mutant mutation
suite; independent census re-derivation; Codex hostile referee).

**Exact claim.** Conjecture 6.1 of the IRIS paper (Davila, De Loera, Eddy, Fang,
Lu, Yang; ICML 2025 Workshop on AI for Math, OpenReview id `v6Ulp3U1ZT`) —
verbatim from the camera-ready PDF:

> *"If P is a simple 3-polytope with face vector (p3, p4, . . . , pm), such that
> sum_{k>=7} pk >= 3, then p6 >= 39/20 + p3/2 - p5/4 - sum_{k>=7} pk."*

is **false as printed**. There are exactly 5 counterexamples with 10 faces and
none with fewer; the census of counterexamples among all simple 3-polytopes with
≤ 16 faces totals 17,490. The cleanest minimal counterexample has face vector
p3 = 4, p5 = 3, p7 = 3 (p6 = 0 against a conjectured bound of 1/5).

**Prior status.** Open: the paper presents Section 6 as "formally stating several
open conjectures"; the OpenReview forum carries no comments or errata
(last modified 25 Jul 2025); dated openness sweeps 2026-06-11 (selection and
write-up time) found nothing. Full query log: `problems/p0-iris/WRITEUP.md` §6.

**Artifacts.**
- Certificate: `problems\p0-iris\certificates\cex10.txt` (5 lines, plantri ascii
  rotation systems of planar triangulations whose duals are the violating polytopes)
- Checker A (Python, stdlib only): `problems\p0-iris\verification\checker_py\verify_counterexample.py`
- Checker B (Rust, independent): `problems\p0-iris\verification\checker_rs\`
- Mutation suite: `problems\p0-iris\verification\mutation_work\run_mutation.py`,
  report `verification\mutation_report.md`
- Independent census re-derivation (plantri 5.8, OEIS A000109 cross-check):
  `problems\p0-iris\verification\rederivation\counts.log`
- Write-up: `problems\p0-iris\WRITEUP.md`

**Verification commands** (from `problems\p0-iris\`):

```
python verification\checker_py\verify_counterexample.py "10 bcdefghi,aigc,abgjfed,ace,adcf,aecjg,afjcbih,agi,ahgb,cgf"
  -> expect line "*** COUNTEREXAMPLE CONFIRMED: violates Conjecture 6.1 ***"
     (string is the acceptance signal — this checker exits 0 even on rejection;
      repeat for each of the 5 lines of certificates\cex10.txt)

verification\checker_rs\target\release\checker_rs.exe certificates\cex10.txt
  -> expect exit 0 and 5 x "COUNTEREXAMPLE CONFIRMED", final line
     "All 5 certificate(s) confirmed: ..."
     (rebuild if needed: cargo build --release --manifest-path verification\checker_rs\Cargo.toml)

python verification\mutation_work\run_mutation.py
  -> expect "violations: none" and "originals ok: True" (33/33 mutants rejected by BOTH checkers)
```

**What this does not show.** Barnette's 1969 theorem is untouched; the
integer-rounded weakening p6 ≥ floor(RHS) survives the census to 16 faces;
nothing is claimed for ≥ 17 faces or for the paper's other conjectures.
(`WRITEUP.md` §7.)

---

## 2. Discrete Borsuk: Conjecture 3 of arXiv:2508.20009 — DISPROVED (kernel-checked)

**Grade: kernel** (Lean 4.30.0 + mathlib; clean axiom audit; faithfulness review
against the paper's own LaTeX source, hostile Codex pass on all nine probe points).

**Exact claim.** Conjecture 3 of Brose, De Loera, López-Campos, Torres, *"On
Lattice Diameter Segments and A Discrete Borsuk Partition Problem"*
(arXiv:2508.20009 v1, 27 Aug 2025) — verbatim from the arXiv LaTeX source
(`paper/sections/Borsuk.tex` line 76):

> *"Let S ⊂ Z^d be a bounded set. Then β_Z(S) = 2^d if and only if conv(S) is
> unimodularly equivalent to a d-cube [0,m]^d for any m ∈ N."*

is **false as stated** (refuted at d = 2, which refutes the all-dimensions
statement). Witness: S_A = {(0,0), (1,0), (0,1), (3,5)} — all pairwise
differences primitive ⇒ lattice diameter 1 ⇒ β_Z(S_A) = 4 = 2²; but
|conv(S_A) ∩ Z²| = 7, unimodular equivalence preserves lattice-point counts, and
|[0,m]² ∩ Z²| = (m+1)² ≠ 7 for all m. The Lean theorems
(`Borsuk.witnessA_kills_conjecture3`, `Borsuk.conjecture3_counterexample`,
`Borsuk.conjecture3_false`) formalize exactly this, against frozen definitions
documented line-by-line against the paper's LaTeX (`lean/Borsuk/Defs.lean`).

**Prior status.** Open: arXiv:2508.20009 was still v1-only as of 2026-06-11; the
conjecture is posed in §4.2 of the paper with no published resolution found.
Provenance and faithfulness ledger: `problems/p3-moonshot/borsuk/STATUS.md` §4.

**Artifacts.**
- Lean project: `problems\p3-moonshot\borsuk\lean\` (7 library files, zero
  `sorry`/`admit`/`axiom`/`native_decide`/`unsafe`)
- Axiom audit script: `lean\scripts\CheckAxioms.lean`
- Frozen paper source: `problems\p3-moonshot\borsuk\paper\` (arXiv tarball)
- Status/faithfulness report: `problems\p3-moonshot\borsuk\STATUS.md`

**Verification commands** (needs elan/lake; `%USERPROFILE%\.elan\bin` on PATH):

```
cd problems\p3-moonshot\borsuk\lean
lake build
  -> expect "Build completed successfully (8483 jobs)", exit 0
     (~18 s incremental on the build machine; a first-ever build fetches/compiles
      mathlib and can take hours — the toolchain is pinned by lean-toolchain)
lake env lean scripts\CheckAxioms.lean
  -> expect every theorem to report at most
     [propext, Classical.choice, Quot.sound]; in particular NO "sorryAx";
     'Borsuk.conjecture3_false' must appear.
```

**What this does not show.** The kill is the d = 2 instance of the printed iff
(which suffices, since the conjecture quantifies over all d). The "full-set"
repair S = conv(S) ∩ Z^d (an unstated hypothesis the authors may have intended)
is *not* refuted by this witness — designed follow-up witnesses B/C
(STATUS.md §6) were stretch goals and are **not** claimed.

---

## 3. Graffiti Conjecture 143 — REFUTED

**Grade: dual-checker** (one checker with two independent exact routes — sympy
isolation and pure-stdlib Berkowitz/Sturm — that must both certify; plus the
orchestrator's independent rebuild `verify_kills.py` §[143] and a Codex
hostile-referee recomputation; 10-mutant suite).

**Exact claim.** Graffiti Conjecture 143 (S. Fajtlowicz, "Written on the Wall",
July 2004 compilation) — verbatim from the frozen, glyph-decoded source
(`problems\p2-factory\kills\graffiti-143\PROVENANCE.md`, from `wow-july2004.pdf`):

> *"143. variance of positive eigenvalues ≤ size / average distance."*

is **false** for connected graphs, under both standard readings of "average
distance" (2W/n² and 2W/(n(n−1))). Smallest certified counterexample:
dumbbell(7,12,20), n = 39 (both readings); dumbbell(6,12,19), n = 37
(distinct-pairs reading). All margins certified by exact rational interval
arithmetic (width ≤ 2⁻⁷⁰), no floats on the accept path.

**Prior status.** Open per Roucairol–Cazenave (ECAI 2025, arXiv:2409.18626, still
v1): table row `143 O 100` — searched to size 100 by 8 algorithms, no
counterexample. Kill-check 2026-06-11: 9 documented queries, all empty
(`WRITEUP.md` §6 and `hardening-results.json`).

**Artifacts** (in `problems\p2-factory\kills\graffiti-143\`):
`certificate_g143.json` (5 dumbbell instances), `checker_g143.py`,
`mutation_tests.py`, `PROVENANCE.md`, `wow-july2004.pdf`, `WRITEUP.md`.

**Verification commands** (from the kill directory):

```
python checker_g143.py certificate_g143.json   -> expect "CHECKER VERDICT: ACCEPT", exit 0  (~15 s)
python mutation_tests.py                       -> expect "MUTATION TESTS: ALL KILLED", exit 0
python ..\..\verify_kills.py                   -> expect [143] VERDICT ... PASS  (independent rebuild)
```

**What this does not show.** No general minimality below n = 37; the n = 90
instance in the certificate is float-corroborated only; the reading dependence
("average distance", "variance") is fully disclosed in the write-up — both
mainstream readings are killed.

---

## 4. Graffiti Conjecture 154 — REFUTED (std-dev reading)

**Grade: dual-checker** (Checker A `check_graffiti154.py` clean-room Python;
Checker B `codex_referee_audit.py` written independently by the hostile Codex
referee, different model family; orchestrator rebuild `verify_kills.py` §[154];
six mutation tests).

**Exact claim.** Graffiti Conjecture 154 — verbatim (WoW July 2004,
glyph-decoded; frozen in `PROVENANCE.txt`):

> *"154. deviation of eigenvalues <= n / average distance."*

is **false** for connected graphs under the standard-deviation reading of
"deviation" (the reading of Favaron–Mahéo–Saclé 1993 and of the only known
machine formalization), under both average-distance conventions. Since the
adjacency spectrum has mean 0 and population std dev exactly √(2m/n), violation
reduces to the integer inequality 8mW² > n⁵(n−1)² (resp. > n⁷). Counterexamples:
lollipop(48,70) (n = 118, distinct-pairs), lollipop(50,70) (n = 120) and
lollipop(72,72) (n = 144, both conventions, 11% margin).

**Prior status.** Open per Roucairol–Cazenave table row `154 O 50` (searched to
size 50, 8 algorithms); WoW lists 154 among conjectures that survived the
1990–91 BDF attack. First violations start at n = 118, beyond every prior search
horizon. Kill-check 2026-06-11: 6 documented queries, clean (`WRITEUP.md` §7).

**Artifacts** (in `problems\p2-factory\kills\graffiti-154\`): `certificate.json`,
`check_graffiti154.py`, `codex_referee_audit.py`, `CODEX_VERDICT.txt`,
`PROVENANCE.txt`, archived sources (`wow-july2004.pdf`, `bdf1995.pdf`,
R–C papers + their `calc.rs` formalization), `WRITEUP.md`.

**Verification commands:**

```
python check_graffiti154.py      -> expect "OVERALL: ALL CHECKS PASS ...", exit 0  (~25-90 s)
python codex_referee_audit.py    -> Checker B; expect exit 0 with
                                    "violating lollipops with n<=117: [] count=0" and the
                                    first violators at n=118 listed (asserts internally on failure)
```

7-line stranger-check (from the write-up, integer-only): compute m, W of
lollipop(72,72) by hand-rolled BFS and test 8·m·W² > 144⁷. Expect
1,411,182,313,113,600 > 1,283,918,464,548,864.

**What this does not show.** The kill is claimed ONLY under the std-dev reading;
under the mean-absolute-deviation reading these instances provably do **not**
violate the inequality (proved exactly via Sturm/Koolen–Moulton in the checker).
Minimality only within the lollipop family.

---

## 5. TxGraffiti/Davila Conjecture 9 — REFUTED

**Grade: dual-checker** (clean-room Python checker; independent Rust checker with
different algorithm; 8-mutant suite; orchestrator rebuild; Codex referee).

**Exact claim.** Conjecture 9 of R. Davila, *Another conjecture of TxGraffiti
concerning zero forcing and domination in graphs* (arXiv:2406.19231v2) —
verbatim from the frozen source:

> *"**Conjecture 9** (TxGraffiti – Open). If G is a connected, cubic, and
> diamond-free graph, then Z(G) ≤ γ(G) + 2, and this bound is sharp."*

is **false**. G14 — two disjoint K₃,₃'s, one edge subdivided in each, the
subdivision vertices joined by a bridge (n = 14, m = 21) — is connected, cubic,
triangle-free (hence diamond-free under both readings), with γ = 4 and
Z = 7 = γ + 3, both exhaustively certified. A chain family extends the failure:
Z − γ = 3, 3, 4, 5 at n = 14, 22, 30, 38 (exact).

**Prior status.** Open: arXiv:2406.19231 still v2 (18 Nov 2024); the paper proves
the claw-free sibling and poses the diamond-free analogue as its central open
question. Kill-check 2026-06-11: 11 documented queries incl. OpenAlex/Semantic
Scholar citation graphs and Davila's own 2025/2026 retrospectives, all clean.

**Artifacts** (in `problems\p2-factory\kills\davila-conj9\`):
`certificate_g14.json`, `certificate_chain_family.json`, `checker_conj9.py`,
`rust_check\` (Rust, independent), `mutation_tests.py`, chain-family edge lists,
`source_2406.19231v2.html` (frozen source), `WRITEUP.md`, `VERIFICATION_LOG.md`.

**Verification commands:**

```
python checker_conj9.py        -> expect "... => Z = gamma + 3  [REFUTES Conjecture 9]"
                                  and "rebuild is isomorphic to record graph", exit 0
python mutation_tests.py       -> expect "MUTATION TESTING PASSED: all 8 corruptions rejected."
rust_check\target\release\rust_check.exe chain_indep_k2.edges gamma 3   -> NONE
rust_check\target\release\rust_check.exe chain_indep_k2.edges zf 6     -> NONE
rust_check\target\release\rust_check.exe chain_indep_k2.edges zffind 7 -> WITNESS 0 1 3 4 7 8 11
```

**What this does not show.** Unbounded Z − γ on this class is conjectured from
the k ≤ 8 data, NOT proven (the general-k lower bound Z ≥ 3k+1 is missing).
Nothing about the proven claw-free theorem.

---

## 6. Pandey parity conjecture — REFUTED (both directions)

**Grade: dual-checker** (clean-room exact Python checker with built-in
`--selftest` mutations; independent Rust brute force; Codex referee).

**Exact claim.** Conjecture 4.1 of R. Pandey, *Parity-Dependent Real-Rootedness
in Independence Polynomials of Generalized Petersen Graphs* (arXiv:2601.03293,
v1, Jan 2026) — verbatim:

> *"For all integers n ≥ 2k+1, the independence polynomial I(GP(n,k),x) has only
> real roots if and only if k is even."*

is **false in both directions**: GP(9,2) (k even) has
I = 1 + 18x + 126x² + 438x³ + 801x⁴ + 747x⁵ + 303x⁶ + 27x⁷ with exactly 5 real
roots (exact Sturm count — not real-rooted); GP(7,3) and GP(3,1) (k odd) are
real-rooted. Moreover GP(7,2) ≅ GP(7,3) (explicit isomorphism), so the predicate
is not even isomorphism-invariant. Exhaustive exact scan 3 ≤ n ≤ 14: exactly 11
violating pairs.

**Prior status.** Open: arXiv:2601.03293 still v1; OpenAlex cited_by_count = 0;
author's repo has no issues. Kill-check 2026-06-11: 10 documented probes, clean.

**Artifacts** (in `problems\p2-factory\kills\pandey-parity\`): `certificate.json`,
`check_pandey_parity.py`, `bf_gp.rs` + `bf_gp.exe` (Rust brute force),
`run.log`, `rust_bruteforce.log`, `WRITEUP.md`.

**Verification commands:**

```
python check_pandey_parity.py --selftest   -> expect "ALL CHECKS PASSED", exit 0
python check_pandey_parity.py              -> expect "ALL CHECKS PASSED", exit 0
bf_gp.exe                                  -> independent Rust brute force; expect rows
                                              "GP(9,2): [1, 18, 126, 438, 801, 747, 303, 27]",
                                              "GP(7,3): [1, 14, 70, 154, 147, 49]", "GP(3,1): [1, 6, 6]"
                                              (rebuild: rustc -O -o bf_gp.exe bf_gp.rs)
```

**What this does not show.** Nothing against the author's tested window
(k ≤ 4, 20 ≤ n ≤ 30 — the violations sit outside it); log-concavity claims of
the same paper are not addressed.

---

## 7. Solubilizer Conjecture A.1 — REFUTED

**Grade: dual-checker** (clean-room Python checker; orchestrator's
`verify_kills.py` §[A.1] as an independent second implementation via a different
algorithmic route; Codex recomputation as a third route; 13-mutant suite).

**Exact claim.** Conjecture A.1 of arXiv:2412.16177 ("Mining Math Conjectures
from LLMs: A Pruning Approach", NeurIPS 2024 MATH-AI workshop) — verbatim from
the arXiv v1 source (main.tex lines 445–447):

> *"Let G be a non-solvable group. For any two elements x, y ∈ G, if
> Sol_G(x) ∩ Sol_G(y) is non-empty, then Sol_G(x) ∩ Sol_G(y) contains a
> non-trivial normal subgroup of G."*

is **false** at the very first non-solvable group: G = A5,
x = y = (0 1 2 3 4) (and the distinct pair (x, x²)): Sol_G(x) = N_A5(⟨x⟩) = D10
(order 10), non-empty, and contains no non-trivial normal subgroup since A5 is
simple.

**Prior status.** Stated Dec 2024 (single version v1), presented as having
survived GAP search to order 10⁶. Kill-check 2026-06-11: 8 probes, clean.
Known caveat (disclosed): the ingredient Sol_A5(5-cycle) = D10 is implicit in
the prior solubilizer literature (arXiv:2309.09104), but no published refutation
of the printed conjecture exists.

**Artifacts** (in `problems\p2-factory\kills\solubilizer-a1\`):
`certificate_a1_a5.json`, `check_a1_refutation.py`, `mutation_test.py`,
`verification_log.txt` (incl. Codex verdict), `WRITEUP.md`.

**Verification commands:**

```
python check_a1_refutation.py  -> expect "ACCEPT: Conjecture A.1 of arXiv:2412.16177v1 is REFUTED ...", exit 0
python mutation_test.py        -> expect "MUTATION SUITE: all 13 mutants rejected, pristine accepted."
python ..\..\verify_kills.py   -> expect [A.1] ... REFUTED: PASS
```

**What this does not show.** The charitable variant "normal in the
intersection" (instead of normal in G) is NOT refuted; weight is modest (an
LLM-generated conjecture from a workshop paper appendix).

---

## 8. Solubilizer Conjecture A.13 — REFUTED

**Grade: audit-panel** (one banked clean-room checker + 7-mutant suite; the
second independent check is Codex's recomputation in a different representation,
recorded verbatim in `VERIFICATION.log`; no second on-disk checker).

**Exact claim.** Conjecture A.13 of arXiv:2412.16177 — verbatim (PDF p. 60,
appendix A.5.6):

> *"Let G be a non-solvable group. For any element x in G, if SolG(x) is a
> proper subgroup of G, then the intersection of SolG(x) with all of its
> conjugates in G is always contained in the hypercenter of G."*

is **false**. G = A5 × S3 (order 360), x = ((0 1 2 3 4), id):
Sol_G(x) = D10 × S3 is proper (order 60), its normal core is 1 × S3 (order 6),
but the hypercenter of G is trivial (Z(G) = 1). The sweep shows A.13 fails at
all 144 applicable x in this G; the mechanism (the solvable radical lies in
every solubilizer) kills A.13 in any non-solvable G with nontrivial solvable
radical and trivial hypercenter.

**Prior status.** Stated Dec 2024; listed by the authors among conjectures whose
checking "code was unable to be run" — never machine-validated. Kill-check
2026-06-11: 9 probes, clean.

**Artifacts** (in `problems\p2-factory\kills\solubilizer-a13\`):
`certificate_a13.json`, `checker_a13.py`, `mutation_test.py` (+ logs),
`paper-2412.16177v1.pdf` (frozen), `WRITEUP.md`.

**Verification commands:**

```
python checker_a13.py --verify certificate_a13.json
   -> expect "certificate certificate_a13.json matches independent recomputation" then "ACCEPT", exit 0 (~5-15 s)
python mutation_test.py
   -> expect "MUTATION TEST: PASS (all mutants rejected)", exit 0 (~45 s)
```

**What this does not show.** Modest weight (LLM-generated conjecture); both
quantifier readings of "its conjugates" are proven equivalent in the checker,
so no reading escape exists; novelty evidence is web-search-based, not proof.

---

## 9. Solubilizer Conjecture A.16 — REFUTED

**Grade: audit-panel** (one banked 32-check clean-room checker + 6-mutant suite
with positive control; second check is Codex's independent recomputation,
different model family; `verify_kills.py` has no A.16 section).

**Exact claim.** Conjecture A.16 of arXiv:2412.16177 — verbatim (PDF p. 13,
appendix A.5.6):

> *"Let G be a non-solvable group. For any element x in G, if SolG(x) is a
> proper subgroup of G, then the intersection of SolG(x) with its normalizer in
> G is always metabelian."*

is **false**. G = A5 × S4 (order 1440), x = ((0 1 2 3 4), id): brute force over
all 1440 elements gives Sol_G(x) = D10 × S4, proper and self-normalizing; the
intersection is D10 × S4 itself with derived series of orders 240, 60, 4, 1 —
derived length 3, not metabelian. Template generalizes:
(simple) × (solvable of derived length ≥ 3).

**Prior status.** Stated Dec 2024; never machine-validated by the authors.
Kill-check 2026-06-11: 6 probes, clean; nearest literature (Mousavi
arXiv:2501.11486) is a different divisibility statement.

**Artifacts** (in `problems\p2-factory\kills\solubilizer-a16\`):
`certificate.json`, `checker.py`, `mutation_tests.py` (+ logs), frozen paper
snapshots (`paper.pdf`, `paper.html`, extracted texts), `WRITEUP.md`.

**Verification commands:**

```
python checker.py          -> expect "All checks passed." and the VERDICT line, exit 0 (~5-20 s)
python mutation_tests.py   -> expect "ALL MUTATION TESTS PASSED", exit 0
```

**What this does not show.** No claim about a simple-group restriction of the
conjecture; no minimality claim for the witness; "metabelian" in its standard
sense (the paper defines no other).

---

## 10. Sun Conjecture 4.6 (arXiv:2108.07723) — REFUTED

**Grade: dual-checker** (four algorithmically independent exact layers across
five implementations — Gray-code Ryser/C + CRT, exact cyclotomic/Python,
CRT-uniqueness/C with disjoint primes, subset-DP/Python — plus mpmath Glynn and
three Codex recomputation audits).

**Exact claim.** Conjecture 4.6 of Zhi-Wei Sun, *Arithmetic properties of some
permanents* (arXiv:2108.07723v7) — verbatim from the TeX source (conjecture
environment at `paper.tex` line 1109):

> *"(i) If n>1 is odd and composite, then s_n ≡ 0 (mod n).
> (ii) Let p be an odd prime. Then s_p < 0 ⟺ p ≡ 5 (mod 12), and
> s′_p < 0 ⟺ p ≡ 7 (mod 8)."*

(s_n, s′_p are the integer-normalized sin/csc permanents of Theorem 1.6) is
**false**: part (ii) fails at p = 29, the first prime beyond Sun's published
table, on both clauses simultaneously — s_29 = 1,053,859 > 0 although
29 ≡ 5 (mod 12), and s′_29 = −4,806,838,304 < 0 although 29 ≡ 5 (mod 8) ≢ 7.
Further failures at p = 41, 53 (mod-12 clause) and p = 61 (mod-8 clause). Every
computed value satisfies Sun's *proven* congruences s_p ≡ (−1)^((p+1)/2),
s′_p ≡ 1 (mod p).

**Prior status.** Open: posed 2021, statement unchanged through v7 (2022),
still latest as of 2026-06-12; Sun's published data stop at p = 23; neither
sequence is in OEIS (rechecked via the OEIS JSON API). 10 kill-check queries
2026-06-12, all clean — incl. disambiguation from the Gao–Guo determinant line
and from "Conjecture 4.6" of *other* Sun papers.

**Artifacts.**
- Kill bundle: `problems\p2-factory\kills\sun-46\` (`kill-certificate.json`,
  `verification-certificate.json`, `snippet_check.py`, `WRITEUP.md`)
- Attack + clean-room side: `problems\p2-factory\attacks\sun-46\`
  (`mycheck_2026-06-12.py` exact subset-DP layer;
  `independent\independent_checker.py` exact cyclotomic layer;
  `independent\crt_verify.py` + `perm_modq.c` CRT-uniqueness proof of all 38
  values; original logs preserved next to each script)

**Verification commands:**

```
cd problems\p2-factory\kills\sun-46
python snippet_check.py            -> expect "-239 -6 -7094142" then "1053859 -4806838304"  (~1 s, float sanity)

cd problems\p2-factory\attacks\sun-46
python mycheck_2026-06-12.py       -> expect "all 19 reproduced exactly.", both clauses "-> VIOLATED",
                                      final VERDICT "... Conjecture 4.6 as stated ... is FALSE", exit 0  (~10-75 s)
python independent\independent_checker.py 29
                                   -> expect published values + kill pair reproduced exactly  (minutes; in verify_all --full)
```

**What this does not show.** Part (i) is NOT refuted — it was tested for all 15
odd composites n ≤ 65 and held every time; it remains open. No replacement sign
law is claimed; values certified only for p ≤ 61 / odd composite n ≤ 65.

---

## 11. Koch–Narayan Conjecture 1 — REFUTED

**Grade: dual-checker** (two clean-room Python checkers by different agents —
same language, a disclosed deviation from the different-language ideal; plus the
attacker's C filter and Codex's own recomputation; 10-mutant suite).

**Exact claim.** Conjecture 1 of G. Koch and D. Narayan, *Maximal bipartite
graphs with a unique minimum dominating set* (arXiv:2511.01719 v1) — verbatim
from the arXiv LaTeX source (`PaperDraft.tex` lines 145–148):

> *"Let G be a bipartite graph without isolated vertices with order n and
> dominating number γ. Let G have a unique minimum dominating set. If γ ≥ 2 and
> n ≥ 3γ, then the size of G, s(G), is bounded above by m(n,γ) = ..."* (full
> formula in the write-up; the printed Φ has a sign typo — both readings refuted)

is **false**. Smallest counterexample (unique up to isomorphism by exhaustive
`geng` sweep): n = 13, γ = 4, s = 22 > 21 = m(13,4), with unique minimum
dominating set {0,1,8,9} certified by enumeration of all 1092 subsets of size
≤ 4. Five further certificates cover γ = 4, 5, 6 up to n = 20; an explicit
"unbalanced-split" family yields 26 verified violations.

**Prior status.** Open: arXiv:2511.01719 still v1, zero citing papers (Semantic
Scholar, 2026-06-12); the paper proves only γ = 2 and n = 3γ. 6 kill-check
queries 2026-06-12, clean.

**Artifacts** (in `problems\p2-factory\kills\koch-narayan\`): six certificate
JSONs (`certificate_13_4.json` primary), `independent\cleanroom_check.py`,
`independent\indy_check.py`, `independent\mutation_tests.py`, `domfilter.c` +
`sweep.log` (exhaustive sweep), `paper.tar.gz` + `PaperDraft.tex` (frozen
source), `WRITEUP.md`.

**Verification commands:**

```
python independent\cleanroom_check.py   -> expect "OVERALL VERDICT: KILL CONFIRMED.", exit 0
python independent\indy_check.py        -> expect "OVERALL: KILL CONFIRMED.", exit 0
python independent\mutation_tests.py    -> expect "MUTATION TESTS: ALL KILLED ...", exit 0
```

**What this does not show.** The γ = 3 strip is NOT refuted (clean through
n = 15 and the mechanism gains nothing there); sweep-dependent claims (truth for
n ≤ 12, minimality/uniqueness of n = 13) rest on a single C implementation and
are flagged attacker-level; "failure for every γ ≥ 4" is certified only at
γ = 4, 5, 6.

---

## 12. C(13) ≥ 36 for the "no 5 on a sphere" grid problem

**Grade: dual-checker** (three independent routes — Python cofactor, Python
Bareiss, Rust crate with 28 unit tests — plus a fourth from-scratch checker
written by the hostile Codex referee, banked and runnable; 7-mutant suite;
official-record convention anchor).

**Exact claim.** For AlphaEvolve repository-of-problems #60 (arXiv:2511.02864,
Problem 6.60) — verbatim from the official problem page (fetched live
2026-06-12, archived with sha256 in `verification\provenance\`):

> *"For n a natural number, let C(n) denote the size of the largest subset of
> [n]^3 = {1,...,n}^3 such that no 5 points lie on a sphere or a plane. Obtain
> upper and lower bounds for C(n) that are as strong as possible."*

we establish **C(13) ≥ 36** via an explicit centrally symmetric 36-point subset
of {0,...,12}³ (18 antipodal pairs on pairwise distinct central shells).
Validity = all C(36,5) = 376,992 lifted 5×5 determinants
[x, y, z, x²+y²+z², 1] are nonzero (exact integers; min |det| = 2). The same
checkers accept all six official AlphaEvolve record sets (n = 7..12) — the
comparison is under the convention that produced the prior records.

**Prior status.** The paper and official repository list lower bounds only to
n = 12 ("C_6.60(12) >= 33", Nov 2025); nothing published for n = 13; inherited
baseline C(13) ≥ C(12) ≥ 33. 16 documented searches on 2026-06-12 plus Codex's
independent sweep: no public claim of C(13) ≥ 34 (or even C(12) ≥ 34) anywhere.

**Artifacts** (in `problems\p1-records\no-5-on-a-sphere-grid\`):
`certificates\record36_centralsym.json` (sha256 `333d36ec...`, byte-identical to
the discovering run's output), 14 supporting 34/35-point certificates,
`code\check_cert.py` (Route A), `verification\gate45_fresh_verify.py` (Route B +
full battery), `code\core\` (Route C, Rust),
`verification\codex_hostile_no5sphere_check.py` (Codex's checker),
`verification\provenance\` (live-fetched problem page/status.json, hashed),
`PROBLEM.md`, `WRITEUP.md`.

**Verification commands** (from the problem directory):

```
python code\check_cert.py certificates\record36_centralsym.json 13
  -> expect "VALID m=36 n=13", exit 0   (~2 s)
python verification\gate45_fresh_verify.py
  -> expect "GATE-4/5 FRESH VERIFICATION PASSED", exit 0  (~70 s; needs code\core\target\release\no5core.exe,
     cargo build --release in code\core if absent)
python verification\codex_hostile_no5sphere_check.py
  -> expect JSON with "tested_5_subsets": 376992, "min_abs_det": 2, "central_symmetry": true
```

**What this does not show.** C(13) = 36 is NOT claimed (lower bound only; best
upper bound remains the trivial 52); 36 is not claimed maximal even empirically;
nothing for other n; priority is "no public claim found", not a guarantee
against unpublished concurrent work.

---

## 13. Elizalde–Luo {1132, 3312} conjecture — PROVED (kernel-checked)

**Grade: kernel** (Lean 4.30.0 + mathlib; the full general-n theorem
`elizalde_luo_1132_3312` is accepted by the Lean kernel — no `sorry`, no
`admit`, no `native_decide`; the axiom audit reports only `propext`,
`Classical.choice`, `Quot.sound`). The finite ground truth (n ≤ 8, three
independent implementations) and the lemma-level exhaustive checks were the
first-line evidence; the theorem for all n is now discharged by the kernel
proof in `lean/` (see `lean/STATUS.md` for the full green-gate table). Two
complete written proofs — a recurrence/structural count and an explicit
bijection onto a ternary language, sharing one triple-audited core and each
vetted by independent hostile panels with clean-room re-verification — informed
the formalization; the bijection proof is the one carried into Lean.

**Exact claim.** The {1132, 3312} entry of Table 4 ("Further research") of
S. Elizalde and A. Luo, *Pattern avoidance in nonnesting permutations*
(arXiv:2412.00336; DMTCS 27:1, Permutation Patterns 2024, paper #13,
DOI 10.46298/dmtcs.14885) — verbatim from the published LaTeX
(`src/formatted.tex` line 1614, with the preamble "All the conjectures have
been checked for n up to 8"):

> *"{1132,3312} & 3^n−3·2^{n−1}+1 & A168583"*

i.e. the number of nonnesting permutations of the multiset {1,1,2,2,...,n,n}
avoiding both 1132 and 3312 (under the paper's biconditional containment
convention, pinned verbatim in `DEFINITIONS.md`) equals **3ⁿ − 3·2ⁿ⁻¹ + 1 for
all n ≥ 1**. This is a **theorem**, formalized in Lean 4 and accepted by the
kernel (`lean/`, `elizalde_luo_1132_3312`). Two complete, independently audited
written proofs (a recurrence/structural count and an explicit bijection onto a
ternary language), both built on the same audited core (FIFO normal form;
sign-word coordinates for prefix-extremal labelings; the characterization of
avoiders by arc-sign constraints), informed the formalization.

**Prior status.** Conjectured in the published paper (2025), verified by the
authors only to n = 8; OEIS A168583 cross-reference; no proof in the literature
as of the June 2026 campaign (paper checked at DOI; conjecture table unchanged).

**Artifacts** (in `problems\p3-moonshot\elizalde-luo\`):
- `final-results.json` — the triage + two audit verdicts per pick (sound/sound,
  zero fatal findings; verbatim panel reports)
- Proof drafts: `drafts\recurrence-structural.md` (primary),
  `drafts\bijection.md` (secondary, independent endgame); three further
  audited-sound drafts (`dyck-sign.md`, `transfer-matrix.md`,
  `kernel-cluster.md`, `generating-tree.md`)
- Pinned conventions + verbatim source quotes: `DEFINITIONS.md`; published LaTeX
  at `src\formatted.tex`
- Ground truth: `data\enumerator.py` (Python, with literal-definition validation
  layers V1–V5), `data\enumerator.rs` (Rust), `data\codex_foil\enumerate_cleanroom.py`
  (clean-room, different model family), `data\counts.json`,
  `data\validation.json`, `data\refined_stats.json`
- Audit harnesses (clean-room, per panel): `work\audit_logician\`,
  `work\audit_comb2\`, `work\audit-comp\`, `work\audit_bij_comb\`,
  `work\audit-comp-bij\`; independent avoider lists `explore\avoiders_n*.txt`

**Verification commands** (the ground-truth and lemma checks in the verify
battery; the general-n theorem is the kernel-checked Lean proof in `lean/` —
build/re-check instructions in `lean/STATUS.md` and the README Lean-projects
section):

```
cd problems\p3-moonshot\elizalde-luo\data
python enumerator.py 7      -> expect V1/V2 "OK" and "match=True" for n=1..7, exit 0  (~45 s)
python enumerator.py 8      -> same through n=8 = the paper's full stated range  (~4 min; verify_all --full)
python codex_foil\enumerate_cleanroom.py
                            -> expect JSON with avoider_counts 1,4,16,58,196,634 for n=1..6
cd ..\work
python triage_spotcheck.py  -> expect "ALL SPOT CHECKS PASSED", exit 0  (~15 s; clean-room spot-audit:
                               Theorem A on all 2,162,160 (shape,perm) pairs at n=7, per-shape counts, bijection)
```

Exhaustive lemma-level verification (what the audits ran, banked under `work\`):
Theorem A checked on ALL 2,162,160 (shape, permutation) pairs at n = 7 and all
57,657,600 pairs at n = 8 (Codex clean-room Rust harness, 0 mismatches); shape
classification and per-shape count formula exhaustive to n = 13; summation
identity exact to n = 60; end-to-end bijection on all 85,514 avoiders n ≤ 10.

**What this does not show.** The kernel proof establishes the counting formula
under the definitions pinned in `DEFINITIONS.md` / `lean\ElizaldeLuo\Defs.lean`;
faithfulness of those definitions to the published paper is the irreducible
human step (re-checked against the source LaTeX in a hostile audit, recorded in
`lean\STATUS.md`). Priority is evidence, not proof: no proof appeared in the
literature as of the June 2026 campaign, but concurrent unpublished work can
never be excluded. The result has not yet been journal-refereed.

---

## Cross-cutting caveats (claim calibration)

1. **Openness/priority is evidence, not proof.** Every "status before this work"
   rests on dated, documented searches (recorded per result); concurrent
   unpublished work can never be excluded.
2. **Statement faithfulness is the irreducible human step.** Checkers verify
   objects against *transcribed* statements. Each result freezes the source
   statement verbatim (paths above); a skeptic must read the ~30–600-line
   checker against that quote. See VALIDATION.md.
3. **Three results carry disclosed deviations** from the strict dual-checker
   ideal: solubilizer A.13/A.16 (second check = Codex recomputation, logged but
   the second implementation is not banked as a script) and koch-narayan (both
   clean-room checkers are Python).
4. **Weight varies.** The Graffiti and Sun kills refute long-standing
   human-curated conjectures; the IRIS/TxGraffiti/solubilizer/Pandey kills
   refute machine-generated conjectures from 2024–2026 papers (modest,
   erratum-note scale — stated plainly in each write-up); the C(13) record and
   the Elizalde–Luo theorem are standalone positive results.
