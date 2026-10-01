# Shared problem statement for the exploration agents

Read this fully before doing anything. Work ONLY inside your own scratch directory
(given in your prompt). Do not modify files under `/home/user/test1`. Python 3.11 with
`numpy`, `python-sat` (pysat, CaDiCaL) and `ortools` is installed system-wide.
Helper modules live in `/home/user/test1/minimizer-frontier/` — add it to `sys.path`.

## 0. Origin

Open Problem 1 of Groot Koerkamp's survey "Low Density Minimizers" (curiouscoding.nl/posts/minimizers/):
prove that the forward-scheme density lower bound g'_σ(w,k) of Kille et al. 2024
("A near-tight lower bound on the density of forward sampling schemes", Bioinformatics 41(1))
is tight when k ≡ 1 (mod w), and also when σ = w = 2. We attack σ = w = 2.
ILP/SAT shows tightness for every k ≤ 15 (odd k directly, even k via P(ν) below). Nobody has a
construction or a proof. The goal is a closed-form rule, a recursive construction, or an existence
proof. A rule that is only *near* optimal is a result too, if its excess is reported honestly.

## 1. Setting (σ = w = 2)

- Window = n consecutive bits, n = k+1. Scheme f : {0,1}^n → {0,1} (which of the two k-mers to pick).
  With w = 2 every local scheme is automatically forward.
- Context = n+1 bits e = e_0…e_n; prefix window pre = e_0…e_{n−1}, suffix window suf = e_1…e_n.
  Context is *uncharged* iff f(pre) = 1 and f(suf) = 0; otherwise charged.
  density = (#charged contexts)/2^{n+1}.
- de Bruijn graph B(2,n): vertices = n-bit windows, edges = (n+1)-bit contexts (pre → suf).
  "Necklace cycle" = rotation class of an (n+1)-bit cyclic word; these cycles partition the edge set.
  Period p | n+1 gives a cycle of length p (p = 1 for 0…0 and 1…1 = self-loops).

### 1a. Odd k (n = k+1 even, m = n+1 odd) — all necklace cycles are odd

Lower bound g_2(2,k) = 2^{-(n+1)} Σ_{p | m} M_2(p)·(p+1)/2, M_2(p) = number of binary aperiodic necklaces of length p.
**Theorem (reformulation).** f is optimal (density = g_2) ⟺ viewing f as a 2-colouring c of the vertices of B(2,n),
every necklace cycle of length p > 1 has **exactly one monochromatic edge** (an odd cycle always has ≥ 1).
Equivalently: **max-cut of the undirected multigraph B(2,n) equals |E| − N(m)**, where N(m) is the number of binary
necklaces of length m (all of them, including the two constant ones). Equivalently: the monochromatic edge set D contains
exactly one rotation of every cyclic (n+1)-word, and B(2,n) − D is bipartite.
Equivalently (all closed walks): for every cyclic binary word t of ANY length ℓ, the number of its (n+1)-bit windows lying
in D is ≡ ℓ (mod 2).

### 1b. Even k — reduces to problem P(ν)

Density is monotone in k (ignore the last window bit). For even k the bound g'_2(2,k) = g_2(2,k+1), so the optimum for even k
equals the optimum for k+1 and is attained exactly by the (k+1)-schemes that ignore the last bit. Define ν = k+1 (odd):

**P(ν):** find h : {0,1}^ν → {0,1}, ν odd, m = ν+2, such that for every cyclic binary word s of length m, among its m windows
W_j = s_j s_{j+1} … s_{j+ν−1} (indices mod m), the number of j with h(W_j) = h(W_{j+1}) is exactly 1 per period
(a cyclic word of period p | m has p distinct windows; count over one period). Note each window misses two consecutive
characters of s.

Any P(ν) solution yields optimal schemes for k = ν−1 (even) and k = ν (odd).

## 2. Verifier API (use it; it is exact)

```python
import sys; sys.path.insert(0, '/home/user/test1/minimizer-frontier')
import numpy as np
from pnu import excess            # excess(h, nu): h = numpy int array of length 2**nu indexed by window as integer
                                   # (first window bit = most significant). 0 ⟺ optimal for P(nu).
from w2 import charged_count, bound_charged, solve, cycles
# charged_count(c, n): c over 2**n windows (odd-k formulation, 1a). Optimal iff == bound_charged(n).
# solve(kprime, restricted=False, enumerate_all=False, cap=...): SAT; returns list of colourings c (numpy arrays over 2**(kprime+1)).
#   restricted=True solves P(kprime): h(u) = c[u << 1].  Enumerating all P(5) solutions takes < 1 s, P(7) ~ 1 min (25088 sols).
#   Unrestricted: P-free odd-k problem, 10 / 98 / 53840 solutions for k' = 1, 3, 5.
# cycles(m): rotation orbits of m-bit integers.
from pnu import alt_vec            # alt_vec(W, nu): bits of W with odd positions flipped (the "alternating flip")
```
`excess` for ν = 3..13 runs in seconds. A rule is a *result* only if its excess is 0 for every tested ν (test at least ν = 3,5,7,9,11,13).
Do not report a lookup table of SAT solutions as a "rule".

## 3. Facts already established (do not redo; build on them)

Solution counts: P(3)=2, P(5)=16, P(7)=25088. Unrestricted odd k: 10, 98, 53840 for k = 1,3,5.
The unique P(3) solution (up to complement) is h(w0 w1 w2) = MAJ(w0, ¬w1, w2).

Symmetry feasibility (SAT-decided, ν or k' = 1..11):
- Odd-k unrestricted: colourings invariant under bitwise complement EXIST for all tested k (so f may depend only on the
  transition word ΔW of adjacent XORs); colourings invariant under reverse-complement (rc) EXIST; rc-anti-invariant do NOT;
  reverse-invariant only for k ≤ 3.
- P(ν), ν ≥ 5: h∘rc = 1−h is the ONLY feasible symmetry (rc-anti-invariant). h∘rc = h impossible; h∘NOT = h and h∘NOT = 1−h
  impossible; h∘rev = ±h impossible. Any closed-form candidate for P(ν) must be rc-ANTI-invariant.
- The complement-invariant unrestricted solutions, written as functions of the ν-bit transition word, coincide exactly with the
  P(ν) solution set for ν = 3, 5 (2 and 16 solutions).

Failed rule families (excess listed for ν = 3,5,7,9,11,13 unless noted):
- parity of position of the lexicographically min/max rotation, min suffix, colex, alternating-order rotation, first/last 0/1,
  longest run, etc. — correct for n ≤ 4 only (unrestricted formulation).
- Mykkeltveit-style complex sector representative — fails badly.
- alternating-flip + majority: 0, 4, 20, 92, 376. No alternating-flip weighted threshold function is optimal for ν = 5 or 7 (LP).
- alternating-flip + "argmax of ±1 walk occurs before argmin" (first occurrences): 0, 4, 12, 36, 96, 264;
  with mirror-symmetric tie-breaking by extremum-set span: 0, 4, 4, 20, 64, 176.
- drift-adjusted walk anchors in the 2-step order: not even self-consistent.
- Lyndon-factor features and pairwise XORs of simple features: none exact at ν = 5.

Nearest optimal P(7) solution to the walk rule differs in exactly these 8 flipped windows (alt_vec coordinates; rule, optimal):
0101100 (0→1), 0100110 (1→0), 0110010 (0→1), 0110011 (0→1), 0110100 (0→1), 0011010 (1→0), 0011001 (1→0), 0010110 (1→0).
They are tie cases (extremum attained more than once) and come in rc-pairs with opposite answers.

Lift picture (useful): for a cyclic word s of odd length m let U_p = s_{p mod m} ⊕ (p mod 2), a 2m-periodic word with
U_{p+m} = ¬U_p. The alt-flipped window of W_j is U[j..j+ν−1] ⊕ (j mod 2). Majority works when the ±1 walk of U crosses its
midline exactly twice per period (antipodally) and fails when it oscillates.

## 4. Minimizer gap

For (σ,k,w) = (2,2,2) the best minimizer (all 4! orders × both tie rules) has 11/16 charged contexts; the optimal forward
scheme has 10/16.
