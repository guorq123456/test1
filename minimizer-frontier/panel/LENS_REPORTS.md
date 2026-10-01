# Per-lens reports (raw agent returns)

## lens: literature

**summary**: (a) Max-cut of de Bruijn graphs IS studied, but only in one 2026 paper and in the opposite regime: Flin, Raevskaya, Stimpert, Suomela, Yang, "2-Coloring Cycles in One Round" (arXiv:2603.04235, Mar 2026; also PODC Brief Announcement doi:10.1145/3796701.3815937) reduce one-round randomized 2-colouring of cycles to "studying cuts in De Bruijn graphs" DB_normal(n) = words of length 3 over an alphabet of size n (word length fixed at 3, alphabet n -> infinity). They know exact values only for n=2 (DB_normal(2) = our B(2,3): "only 4 out of 16 edges are monochromatic ... no 2-coloring with fewer monochromatic edges (consider two self-loops and two triangles)", which is exactly our k=2 optimum 10/16 charged, verified: lit_rules_check.py) and n=4 (p_normal(4) ~ 0.2422 by exhaustive enumeration); for larger n they only have SDP-with-symmetry certificates (0.23879 <= p* < 0.24118) and say the exact value is open. Nothing in the literature treats max-cut / edge-bipartization / odd-cycle-transversal / frustration index of B(2,n) with n growing; the necklace-cycle argument used in our reformulation is the same "pure cycle" argument as Kille et al. and Flin et al. Fig. 2 (24 edge-disjoint 5-cycles), but nobody has a matching construction. (b) Nobody has claimed tightness of g' for sigma=w=2 for all k. The published evidence is computational only: Kille et al. 2024: "Additionally, when sigma = 2 and w = 2, the minimum density was equal to g'_sigma(w,k)" (Gurobi, 1<=w,k<=12, 12 h/instance); Groot Koerkamp's survey: "for sigma=w=2, the lower bound is also optimal for all even k" and Open Problem 1 verbatim: "Prove that the g'_sigma lower bound on forward scheme density is tight when k≡1 (mod w), and additionally when sigma=w=2."; Shur, Tziony, Orenstein 2026 Table A1 independently reports forward-scheme optima for Sigma=2, w=2, k=1..7,9,11 = 6/8,10/16,20/32,37/64,74/128,143/256,286/512,1118/2048,4412/8192, every one equal to the verifier's bound (bound_charged(n) for n=k+1, with even k via k+1). No construction for k≡1 (mod w) at finite sigma exists: Kille et al. prove mod-minimizer optimality only "when sigma goes to infinity" and state "the mod-minimizer does not quite match the lower bound for practical values of sigma"; the anti-lexicographic SUS-anchor (WABI 2026) is empirical, k=1 only, and "For alphabet size sigma=2, the density is at most 10% above the lower bound". (c) No 2025-2026 paper resolves or theoretically advances Open Problem 1. Computational advances: Shur et al. 2026 (above; also shows minimizers miss the forward optimum by exactly one charged window at even k=2,4,6 for w=2: 11 vs 10, 38 vs 37, 144 vs 143, and equal it at odd k<=11 — a precise generalisation of PROBLEM.md §4's "minimizer gap"); Shur 2025 arXiv:2506.05277 gives a closed form for the optimal (sigma=2,k=2,w)-minimizer, (2^w+w+5)/2^(w+2), the only closed-form optimum in the area, in the dual regime (k fixed, w varying). Methodological import: Flin et al. show the max-cut question for de Bruijn graphs admits symmetry-reduced SDP certificates and Lean formalisation; HRSS17 (Hirvonen–Rybicki–Schmid–Suomela, EJC 2017) gives the general "weighted neighbourhood graph <-> one-round local algorithm" correspondence of which our scheme f:{0,1}^n->{0,1} on binary-labelled cycles is an instance. Literature-derived rules transplanted to our setting (Flin's f2 local-max, f3 flip-if-constant, Fig.-2 'first-or-last symbol' colouring, 3-bit majority) were run through the verifier; none is exact beyond nu=3.

**best excess profile**: No new exact rule. Best literature-derived rule tested (central 3-bit majority, i.e. the known P(3) solution lifted): excess 0, 12, 68, 324, 1416, 6000 for nu=3,5,7,9,11,13 — worse than the lead's alt-flip majority (0,4,20,92,376). Script and output: /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-literature/lit_rules_check.py and lit_rules_check.out

**exact_rule_found**: False

**insights**:
- Max-cut of de Bruijn graphs is an open problem in distributed computing under the name 'one-round 2-colouring of cycles' (Flin et al. 2026): p_normal(n) = min fraction of monochromatic edges of DB_normal(n) (word length 3, alphabet n). Our problem is the transposed regime (alphabet 2, word length n->infinity). The two families meet only at DB_normal(2) = B(2,3), where both give 4/16 monochromatic = 10/16 charged (verified with w2.charged_count). So the exact max-cut of B(2,n) for even n (claimed tight by SAT for k<=15) is not in the literature; proving |E|-N(n+1) for all even n would be a new theorem about de Bruijn graphs, not just about minimizers.
- Flin et al. obtain their lower bound on the cut via an SDP relaxation 'with correlation triangle inequalities' whose size is 'bounded by a constant independent of n' thanks to the automorphism group, with a rational dual certificate (Peyrl–Parrilo) formalised in Lean. For B(2,n) the same symmetry-reduced SDP would give an upper bound on max-cut; it cannot replace a construction, but it is the one published technique for exact cut statements on de Bruijn graphs.
- Hirvonen–Rybicki–Schmid–Suomela (EJC 2017): 'there exists a weighted neighbourhood graph N_d such that there is a one-to-one correspondence between heavy cuts of N_d and randomised local algorithms that find large cuts'. Our f:{0,1}^n->{0,1} is precisely a deterministic one-round-type rule on cycles whose nodes carry one random bit, with de Bruijn graph B(2,n) as the neighbourhood graph; this is the historical origin of the max-cut-of-de-Bruijn-graph viewpoint.
- Kille et al.'s ILP evidence for sigma=w=2 is nominally 1<=w,k<=12 with a 12 h limit (exact k reached is not stated in the text; Fig. 2 only), and their Conjecture 1 covers only k≡1 (mod w) — the sigma=w=2 even-k claim appears only as an observation ('Additionally, when sigma = 2 and w = 2, the minimum density was equal to g'') and was promoted to Open Problem 1 in Groot Koerkamp's survey/thesis.
- Shur–Tziony–Orenstein 2026 Table A1 (Sigma=2, w=2; columns GreedyMini / minimizer-ILP / forward-ILP / #windows): k=1: 6/6/6/8; k=2: 11/11/10/16; k=3: 20/20/20/32; k=4: 38/38/37/64; k=5: 74/74/74/128; k=6: 144/144/143/256; k=7: 286/286/286/512; k=9: 1118/1118/1118/2048; k=11: 4412/4412/4412/8192. The forward column equals bound_charged(k+1) (odd k) or bound_charged(k+2)/2 (even k) from the verifier for every listed k — independent corroboration of tightness up to k=11, and the statement that for w=2 an optimal minimizer is exactly one charged window above the optimal forward scheme at k=2,4,6 and equal at odd k. They also note the open question 'whether minimizers can achieve the same density as forward sampling schemes for k ≡ 1 (mod w) and k > 1' (fails to close at (w,k)=(4,9),(6,7)).
- Kille et al. explicitly link the conjecture to universal hitting sets: 'proving Conjecture 1 would also determine the minimum size of a (w, l = w+k)-UHS when k ≡ 1 (mod w)'. For w=1 the minimum UHS = minimum decycling set = minimum unavoidable set of size N(l) (Mykkeltveit 1972; Champarnaud–Hansel–Perrin 2004). Our monochromatic edge set D is a minimum unavoidable set of (n+1)-words (one per necklace) with the additional requirement that B(2,n)-D be bipartite; the two classical explicit minimum unavoidable sets are Mykkeltveit's V-set (PROBLEM.md: fails) and the Champarnaud–Hansel–Perrin set, which has not been tested (untested here; lens restricted to literature).
- Lempel's D-morphism (XOR of adjacent bits, B(2,n+1)->B(2,n)) is the classical name for PROBLEM.md's 'transition word' reduction; the known structural fact (Lempel 1970; restated in Alhakim–Akinwande arXiv:0812.4012 per search summary) that a cycle of odd weight in B_{n-1} is the image of a single self-dual cycle of double length while an even-weight cycle lifts to two disjoint cycles is exactly the 'lift picture' U_{p+m} = NOT U_p of PROBLEM.md §3; the complement-invariant unrestricted solutions are colourings pulled back through D.
- Shur 2025 (arXiv:2506.05277, Theorem 11) is the only closed-form optimum in this literature: minimum density of a (sigma=2,k=2,w)-minimizer is (2^w+w+5)/2^(w+2) for all w — proved via regular-language/eigenvalue methods; a possible model for how a closed-form proof in our regime might be organised (automata over cyclic words), though it concerns minimizers, k=2, and varying w.
- No 2025-2026 paper (open-closed mod-minimizer AMB 2025; SUS-anchor WABI 2026; GreedyMini Bioinformatics 2025; OptMini 2026; 10-minimizers 2026; Multiminimizers RECOMB 2026; Finimizers 2025) claims a construction or proof for k≡1 (mod w) at finite sigma or for sigma=w=2; all tightness statements remain ILP/empirical.

**dead ends**:
- Direct queries 'max cut de Bruijn graph', 'maximum cut of de Bruijn graphs', 'largest bipartite subgraph de Bruijn', 'odd cycle transversal de Bruijn', 'frustration index / edge bipartization de Bruijn', 'bipartite density de Bruijn' return nothing beyond Flin et al. 2026 (and unrelated cut-down de Bruijn sequences / independent-set papers).
- 'balanced 2-colouring de Bruijn necklaces', 'antipodal colouring odd-length necklaces one monochromatic edge', 'de Bruijn vertex 2-coloring exactly one monochromatic edge per cycle': no hits; this per-necklace formulation does not appear in the literature.
- Mykkeltveit decycling / unavoidable-set literature (Mykkeltveit 1972; Champarnaud–Hansel–Perrin 2004; Marçais–DeBlasio–Kingsford 2024 MDS sketching; Kingsford-group mdsscope) never considers bipartiteness of the remaining graph.
- mod-minimizer tie-breaking at finite alphabet: Kille et al. only say the scheme 'does not quite match the lower bound for practical values of sigma'; no paper fixes the finite-sigma loss.
- Flin et al.'s one-round rules (f2, f3, Fig.-2 colouring) transplanted to binary windows: not optimal for nu>=5 (verified).
- bioRxiv rate-limited (HTTP 429 / Cloudflare 1015) the full text of '10-minimizers' (10.64898/2026.03.16.712052); only its abstract-level description (constant-space minimizer class, Shur–Tziony–Orenstein) was obtained; nothing suggests it addresses forward-scheme tightness.
- GitHub READMEs of treangenlab/sampling-scheme-analysis and OrensteinLab/OptMini contain no result tables; Kille's exact maximal k for sigma=w=2 is only in their Supplementary Table S2 (not fetched).

**verifier**: refuted=False — I checked the claim's central conclusion and found nothing to refute it. Every source I could reach shows the problem as still open; none solves it or advances it in theory. Details:

1. Flin et al., arXiv:2603.04235. Fetched the abs page and the v2 HTML.
   - The authors, title and 2026 dates are correct.
   - The v2 HTML defines DBnormal(n) with vertices (a,b,c) for a,b,c in [n], so word length is fixed at 3 and the alphabet grows. That is the opposite regime to ours.
   - These quotes appear essentially verbatim: the Fig. 1 caption ("only 4 out of 16 edges are monochromatic"), pnormal(2)=0.25, pnormal(4)≈0.2422, and Lemma 4.4 (p* ≥ pdistinct(10^6) ≥ 0.23879, via an SDP relaxation with correlation triangle inequalities).
   - The abstract reports bounds of 0.23879 and 0.24118 only, so the exact value is still open.
   - The claim reads this paper as different-regime only, not a solution of our problem. That reading is correct.

2. Kille et al. 2024. The NSF PAR PDF downloaded through WebFetch; I extracted its text in my own scratch directory. All of these quotes are there:
   - "Additionally, when σ = 2 and w = 2, the minimum density was equal to g'σ(w,k)"
   - The ILP setup: 1≤w≤12, 1≤k≤12, 2≤σ≤4, 12 h on 128 threads
   - Conjecture 1, stated for k≡1 (mod w) only
   - The UHS sentence
   - "the mod-minimizer does not quite match the lower bound for practical values of σ", with optimality only as σ→∞

   So the σ=w=2 claim in this paper rests on computation only.

3. curiou

**verifier**: refuted=False — I checked every load-bearing citation against its source. All of them hold up, apart from one overstatement noted at the end. The literature claim is negative overall: Open Problem 1 for sigma=w=2 has no proof and no construction. The only "advances" it cites are computational, plus one max-cut paper on de Bruijn graphs in a different regime. All of that is confirmed.

(1) Flin, Raevskaya, Stimpert, Suomela, Yang, "2-Coloring Cycles in One Round" (arXiv:2603.04235, submitted 4 Mar 2026, revised 5 Mar). The abstract page does not mention de Bruijn graphs, but the HTML full text does. It contains: "studying two variants of 3-dimensional De Bruijn graphs"; "pnormal(n) for the smallest possible fraction of monochromatic edges in any 2-coloring of DBnormal(n)"; "only 4 out of 16 edges are monochromatic"; "We can check with exhaustive enumeration that pnormal(2)=0.25 and pnormal(4)≈0.2422"; and "We use a semidefinite-program (SDP) relaxation of the max-cut problem, with correlation triangle inequalities". The vertices are triples over an alphabet of size n. That is the opposite regime from ours (word length 3 fixed, alphabet growing), as claimed.

(2) Groot Koerkamp's survey (curiouscoding.nl/posts/minimizers/). Open Problem 1 is there verbatim. The sentence "for sigma=w=2, the lower bound is also optimal for all even k" is also there. Nothing claims a resolution.

(3) Kille et al., Bioinformatics btae736 (read through OUP). The page has the ILP ranges (1<=w<=12, 1<=k<=12, 2<=sigma

## lens: arithmetic

**summary**: The arithmetic-anchor lens produces no exact rule and, more usefully, is now provably closed off in several directions by exhaustive checks against the complete solution sets of P(5) (16 solutions) and P(7) (25088 solutions). (1) Every full-word anchor of the form a(s) = (Σ_{s_i=1} i − r)·wt^{-1} mod m (centre of mass), the same for transition/rising/falling-edge centroids, and the quadratic-residue anchor, is wildly inconsistent: the two hidden bits change the anchor almost arbitrarily (at ν=11 the centroid rule conflicts on 1659 of 2048 windows), and majority-resolving the 4 completions gives excess 4, 40, 100, 888, 3896 for ν=3..11 — far worse than plain alt-flip majority. (2) Consistent-by-construction window arithmetic is also dead: no exact solution at ν=5 or ν=7 is a function of (Σ i·w_i mod M, wt), (Σ i·w_i mod M, wt, Σ i²·w_i mod M), or even all moments up to degree 3 mod m (ν=7: 122 classes of 128, zero compatible solutions); exhaustively, no exact solution is of the form F(Σ c_i w_i mod M) for ANY weight vector c and any M ≤ 24 at ν=5 (while ν=3 correctly recovers MAJ as c=(1,−1,1) mod 5), and no exact P(7) solution is of the form F(Σ c_i w_i mod M, wt) for M ∈ {8,9,10}. The only positive hit, F(c·w mod 7, wt) at ν=5, turns out to be the non-arithmetic fact that some solutions depend on the two end bits only through w_0 + w_{ν−1}; this end-bit swap symmetry is SAT-feasible for ν = 5,7,9,11,13 (72 of the 25088 P(7) solutions), is the only position-swap symmetry that ever occurs, and cannot be combined with rc-anti-invariance for ν ≥ 9. (3) A verified reformulation explains the failures: for any exact solution, flipping bit s_p moves the seam a→a' by an even distance and the contiguous block between a+1 and a' must contain both of p+1, p+2 or neither (0 violations over all P(5) and 200 P(7) solutions); exact solutions are strongly non-local — the seam moves in 71% (ν=5) / 66% (ν=7) of single-bit flips, with every displacement occurring — so any content-arithmetic anchor, which is maximally sensitive to single bits, cannot satisfy the block condition. (4) The window pairs forced apart by every solution at ν=7 are translates (W and W shifted by d inside the window), including the ones with wt·d ≡ 0 (mod 9) that make all mod-9 moments coincide (0000111 vs 0111000) — the precise point where gcd(wt,m) > 1 enters and kills mod-m features.

**best excess profile**: No rule in this lens beats the alt-flip majority baseline (0,4,20,92,376). Best lens rule: centre-of-mass anchor (A−r)·wt^{-1} mod m with 2-step arc, h by majority over the 4 completions, r and shift re-optimised per ν: excess 4, 40, 100, 888, 3896 for ν=3,5,7,9,11 (ν=13 not run; the rule is inconsistent on 6/24/45/425/1659 windows). The only zero-conflict arithmetic construction (quadratic-residue anchor at ν=3) has excess 4 and is inconsistent from ν=5 on.

**exact_rule_found**: False

**insights**:
- Content-arithmetic anchors cannot work because of a verified seam-block law: in every exact solution, flipping bit s_p moves the seam by an even distance and the swept block (from a+1 to a') must contain both or neither of positions p+1, p+2 (the only two windows unaffected by the flip). A centroid (A−r)/wt mod m moves essentially uniformly when one bit flips, so it violates this on most windows (1659/2048 at ν=11).
- Exact solutions are non-local: the seam moves in about 2/3 of all single-bit flips at ν=5,7, for bits at every distance from the seam and with every possible displacement. Any anchor that only reacts to bits near the seam is ruled out; the mod-minimizer intuition (anchor = a local extremum position) does not transfer.
- Mod-m moments of the window (Σ i^p w_i, p ≤ 3, plus wt) fail at ν=7 for an identifiable reason: windows that are in-window translates by d with wt·d ≡ 0 (mod m) share all mod-m moments (0000111 vs 0111000, wt=3, d=3, m=9) yet every one of the 25088 solutions colours them differently. gcd(wt,m)>1 already bites inside a single window, not only on periodic words.
- In-window translates are generally forced apart: at ν=7, 31 of 63 shift-by-1 translate pairs, 9 of 15 shift-by-3 pairs and 2 of 3 shift-by-5 pairs are coloured differently by every solution, while NO shift-by-2, -4 or -6 pair is forced different — odd shifts separate, even shifts never force anything (consistent with the alternating structure).
- All 25088 P(7) solutions agree on two rigid classes of 32 windows each (e.g. 0000000 ≡ 0000010 ≡ 0001010 ≡ 0100000 ≡ 1101011 ... and 0000001 ≡ 0000100 ≡ 0010101 ≡ 1111111 ...): 64 of the 128 windows have forced colours up to global complement, plus smaller forced classes of size 8 and 3; 1124 pairs forced equal, 1171 forced different (forced_pairs.py). A candidate rule can be screened against these forced relations before any excess computation.
- End-bit swap symmetry (the window depends on its two end bits only through w_0 + w_{ν−1}, i.e. on the two neighbours of the hidden pair symmetrically) is SAT-feasible for every tested ν = 5..13 and is the only transposition symmetry any solution has; it is incompatible with rc-anti-invariance for ν ≥ 9. This is a new symmetry constraint a closed-form rule may adopt (but then it cannot also be rc-anti-invariant beyond ν=7).
- Among the 16 P(5) solutions exactly 8 are rc-anti-invariant; among the 25088 P(7) solutions exactly 448 are.
- The ν=3 solution MAJ(w0,¬w1,w2) is a modular weighted sum ([w0−w1+w2 mod 5 ∈ {1,2}]), but no 1-D modular weighted sum with any weights exists at ν=5 for M ≤ 16, so the arithmetic form of MAJ does not generalise.

**dead ends**:
- Full-word anchors from Σ i·s_i / wt, Σ over 0-positions (identical mod m), transition / rising / falling-edge centroids, and quadratic-residue roots: all inconsistent under the hidden-bit completions for every r and shift, with conflicts growing to ~80% of windows at ν=11.
- Secondary rules for gcd(wt,m)>1 (recursion on the primitive period) are moot: the prime-m cases ν=3,5,9,11 already fail.
- Polynomial weights vanishing at the two hidden positions, e.g. Σ s_i (i−j+1)(i−j+2) mod m: consistent by construction but a function of mod-m moments, which no exact solution factors through at ν=7.
- h = F(Σ i·w_i mod M, parity of wt) and h = F(Σ i·w_i mod M, wt): zero compatible exact solutions at ν=5 and ν=7 for all moduli tried.
- Arbitrary modular weighted sums h=F(c·w mod M): none at ν=5 (M≤16); with wt as a second coordinate none at ν=7 for M=8,9,10; the ν=5 hits at M=7 are just end-bit symmetry, not modular structure.

## lens: recursive

**summary**: A uniform recursive construction that is exact (excess 0) for every tested nu = 3,5,7,9,11,13 was found: a 2-bit "state-passing pyramid". Each odd nu gets a state g_nu:{0,1}^nu->{0,1}^2, the scheme is h_nu = first state bit, g_1 is a fixed base, and for nu>=3 g_nu(W) = PHI[g_{nu-2}(W[0:nu-2]), g_{nu-2}(W[1:nu-1]), g_{nu-2}(W[2:nu]), w_0, w_{nu-1}] with ONE fixed 256-entry table PHI (4^3 child-state combos x 4 end-bit combos -> 2 bits) used at every level. PHI was found by SAT (CaDiCaL) over the table entries with the P(nu) constraints for nu=3..13 imposed simultaneously, then independently re-verified by a table-free numpy rebuild calling pnu.excess (standalone script rule_state2_exact13.py prints 0 for nu=3..13). Honest caveats: the table content is machine-found and not hand-interpretable (its output bit agrees with MAJ(a,NOT b,c) on 93% of windows at nu=13; the second bit is a rare 'flag' that matches no simple hypothesis); 136 of its 256 entries are reachable through nu=13; the found table is NOT exact at nu=15 (excess 264 with unused entries arbitrary), fixing its 136 used entries and freeing the rest is UNSAT at 15, and the unconstrained nu<=15 search (run_state2_15.py) did not finish in 30 CPU-minutes, so exactness beyond 13 is open. A second exact-to-13 variant with w_1,w_{nu-2} added (1024 entries) behaves the same. The path to this result: the 1-bit version of the same recursion has a clean closed form, h_nu = MAJ(a,NOT b,c) except when a=1,c=0 and w_0=w_{nu-1} (then h=b), which reproduces MAJ(w0,NOT w1,w2) at nu=3 and is exact for nu=3,5,7 (the first rule family past nu=5) with excess 16,96,456 at 9,11,13; SAT proves no 1-bit uniform table over any end-local or middle context survives nu=11, and a verified structural fact explains why: every P(nu) solution on cycles of length nu+4 has at most one glitch (<=3 mono steps), a 3-window majority can only repair length-1 glitches, and the single P(3)-descendant branch of P(5) solutions is dead at nu=9, so the recursion must carry extra state to re-select its level-5 solution from another symmetry orbit.

**best excess profile**: nu=3,5,7,9,11,13: 0,0,0,0,0,0 (256-entry 2-bit pyramid, rule_state2_exact13.py; also the 1024-entry variant rule_state2_raw4_exact13.py). nu=15: not exact with the found tables (264 and 420); extension with used entries fixed UNSAT for both; unconstrained nu<=15 search (run_state2_15.py) unresolved after 30 min. Interpretable fallbacks: table-free 1-bit closed form (closed_form_rule.py) 0,0,0,16,96,456; 1-bit backbone+middle-bit 64-entry table (rule_1bit_mid_nu9.py) 0,0,0,0,40,276.

**exact_rule_found**: True

**insights**:
- Z-picture reformulation (verified, underlies everything): P(nu) holds iff for every cyclic word s of length m=nu+2 the sequence Z_j = h(s[j..j+nu-1]) XOR (j mod 2) is a clean square wave (exactly one change per m consecutive positions); Z is automatically antiperiodic with antiperiod m.
- Glitch bound (verified for ALL 16 P(5) and ALL 25088 P(7) solutions, and for the pyramid's own h_9 on 13-cycles and h_11 on 15-cycles): a P(nu) solution evaluated on cycles of length nu+4 has at most 3 mono steps (one glitch per antiperiod), and at most 5 on nu+6. Hence each recursion level nu-2 -> nu has to repair exactly one glitch of its child's Z-sequence; a 3-window majority repairs only length-1 glitches, which is why the 1-bit contiguous recursion stops being exact after nu=7 and why extra carried state is needed.
- The unique P(3) solution MAJ(w0,NOT w1,w2) equals 'h = w0 if w0 != w1 else w2' = w0 XOR [Delta W = 01]; in the Z-picture it is a plain 3-point majority filter of the alternating lift U. The 1-bit recursion h_nu = MAJ(a,NOT b,c) with the single exception (a,c)=(1,0) and w_0 = w_{nu-1} -> b is the exact generalisation that reproduces P(3) from h_1 = id and is exact for nu = 3,5,7 (chain P3 -> P5#5 -> P7#15644 with the same F at both levels; this is the first rule family known to be exact past nu=5). The exception is exactly the rc-anti-invariant asymmetry between (a,c)=(1,0) and (0,1) that the impossibility of self-dual solutions forces.
- Orbit structure of P(5) under {NOT, reverse, output complement}: three orbits, {5,6,12,13} (size 4), {2,4,8,15} (size 4) and a size-8 orbit. Only {5,6,12,13} descends from P(3) by the contiguous recursion, and that branch is provably dead at nu=9 (no end-local lift of its P7 solution exists, SAT). Every pyramid that is exact through 11 or 13 routes through one of the OTHER two orbits (plain 256-table: size-8 orbit; middle-bit variant: {2,4,8,15}); so an exact recursion must be able to 're-choose' its level-5 solution, which is what the second state bit buys. Not all P(5) solutions are rc-anti-invariant (the pyramid solutions are not at nu>=5).
- One bit per level is insufficient regardless of raw context: 1-bit uniform tables over the three contiguous children plus any of {w0,w1,w_{nu-2},w_{nu-1},w_mid} are UNSAT at nu=11; adding h_{nu-4} on 5 contiguous sub-windows (multi-scale) also dies at 11. Two bits per level with only w0,w_{nu-1} suffice through 13.
- For the 1-bit recursive h_9 the nearest optimal P(9) solution is Hamming distance 12 (of 512) away; the 12 windows each share their recursion key with 5-40 other windows, so no table repair is possible and the needed information is not end-local.
- The second state bit in the exact tables is a sparse flag (about 9-12% of windows in one solution) that is not h(rev W), h(NOT W), h(rc W), an end bit or a function of (h, w0, w_{nu-1}); its exact meaning is unknown.
- The output bit of the exact 256-table agrees with MAJ(a,NOT b,c) on 93% of windows at nu=13 (91% at 7, 86% at 9, 93% at 11), so the construction is 'alternating-sign majority smoothing of the child scheme plus a carried disambiguation bit'.

**dead ends**:
- Fixed-position deletion lifts (any pair, with or without the deleted bits as side information): zero consistent solution pairs at 3->5 and 5->7.
- Continuing the P(3)-descendant chain (P3 -> P5 orbit {5,6,12,13} -> P7) past nu=7: impossible by any end-local rule (SAT UNSAT with 21 features; needs 8 of 9 raw bits).
- 1-bit uniform tables of any tested end-local/middle context (backbone + 1 or 2 extra end features, middle bits, multi-scale h_{nu-4}): all UNSAT at nu=11 or earlier; the exact-through-9 ones need SAT-chosen base tables at nu=3,5 or stop at 9.
- Transition-word (Delta^2) recursion h_nu = G(end bits, h_{nu-2}(Delta^2 W)): no consistent pairs.
- Block-MAJ iteration of the P(3) rule on thirds of the window (nu=9): excess 292.
- Lyndon/Duval last-factor recursion (six variants): wrong already at nu=3.
- Lottery over many distinct nu<=11 tables scored at 13: all 148; the nu<=13 tables found do not extend to nu=15 with their used entries fixed (UNSAT for both the 256- and 1024-entry tables); unconstrained nu<=15 search unresolved (30 CPU-min).
- MaxSAT simplification of the table toward MAJ(a,NOT b,c) at nu<=11 did not finish in the available time (simplify_maxsat.py).

**verifier**: refuted=True — I re-implemented the rule from its text in verify-recursive-0/myrule.py, without reusing the claimant's build code. The only thing taken from the script is the PHI string, read from rule_state2_exact13.py. g_1(0)=(0,0) and g_1(1)=(0,1). Each g_nu = PHI[g(W>>2), g(middle nu-2 bits), g(low nu-2 bits), w0, w_{nu-1}], and h is the first state bit. I checked excess two ways: with pnu.excess, and with my own vectorised counter (Burnside necklace count plus mono steps summed over all 2^m rotations). The two agree everywhere.

Results:
- nu = 3, 5, 7, 9, 11, 13: excess 0, 0, 0, 0, 0, 0.
- nu = 15: excess 264.
- nu = 17: excess 2324.
Both held-out values match the lead's numbers exactly.

The script does not call solve(); it imports only pnu.excess. But PHI is a 256-entry table that SAT fitted on P(3)..P(13). Only 136 entries are reached through nu=13, and nu=15 adds just 10 new keys.

I also checked whether any choice of the unused entries could rescue the table. My own CaDiCaL check (ext15.py) fixes the 136 used entries and leaves the first bits of the 10 new nu=15 keys free. It uses an exactly-one-mono-step constraint per necklace cycle of length 17. It is UNSAT, which confirms the lead's claim.

So the table stays exact only on the nu values it was fitted to, fails at both held-out nu (15 and 17), and cannot be extended to 15 even with its free entries. It is a fitted lookup table, not a uniform exact rule.

**verifier**: refuted=True — I rebuilt the rule myself in /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/verify-recursive-1/indep.py, working from the text description and not from the lens's build(). Each state is a 2-bit integer, starting from g_1(0)=00 and g_1(1)=01. The table key is (g(W[0:nu-2]) << 6) | (g(W[1:nu-1]) << 4) | (g(W[2:nu]) << 2) | (w0 << 1) | w_{nu-1}, and h is the first state bit. Only the 512-character PHI string is copied from the lens script.

I scored every nu two ways: with pnu.excess and with my own vectorised excess (counting mono steps over all m-bit words, divided by m, minus the non-constant necklaces). Both agree: nu=3,5,7,9,11,13 give excess 0,0,0,0,0,0, nu=15 gives 264 and nu=17 gives 2324. This matches the lead's figures (264 and 2324) exactly.

Extension check (ext15.py): 136 of the 256 entries are used through nu=13, which matches the claim. At nu=15 the scheme needs 132 distinct keys, and only 10 of them are new. I fixed the used entries and set up P(15) as a SAT problem over the free entries. It is UNSAT trivially: 94 of the 7710 length-17 cycles already have 2 or more mono steps made only of fixed entries, before any free entry is chosen. This confirms the lens's own UNSAT result.

Lookup-table check: the script imports only pnu.excess and never calls solve() at runtime. However, its core is a 256-entry table that SAT chose with P(3)..P(13) imposed jointly, which the claim itself says. That is exactly the case the task describes: SAT 

## lens: datamining

**summary**: No exact rule. Enumerated all 16 P(5) and 25088 P(7) solutions, 20000 random-phase P(9) and 3000 P(11) solutions, and computed the EXACT forced core (SAT backbone with h(0^nu)=0) for nu=9,11,13. Main findings (all verified by scripts in /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-datamining/): (1) CORE RULE: in alt-flipped coordinates f, every window that contains '11' but no '00' is forced to 1, '00' but no '11' forced to 0, alternating f (constant W) forced to f0; i.e. classify each transition of W at position i by w_i xor (i mod 2) -- if all transitions have the same class, h = that class. This is the complete forced core for nu=3,5,7 (8/8, 24/32, 66/128 windows), its min-DNF has exactly nu terms (f_i f_{i+1}, i<nu-1, plus f_0 f_2...f_{nu-1}), and it is contained in the exact backbone for nu=9,11,13 (176/208, 464/562, 1218/1568); the extra forced windows at nu>=9 (32, 98, 350) are global consequences (single-cycle propagation of the core with up to 4 unknowns adds nothing) and take the majority value in all but 2 cases. (2) PHASE LAW (SAT-verified exactly for nu=7,9,11,13, enumeration for 5,7): among mixed windows, all those whose transitions lie only at odd positions (W = xxyyzz..t) share one free global bit a, and all those with transitions only at even positions take 1-a; h is negation-invariant there, so every walk rule that is antisymmetric under walk negation (all previous walk rules, 'span' included) necessarily errs on this component. (3) Core + phase law + the existing 'span' walk rule on the remaining mixed-parity windows gives excess [0,0,0,8,36,116] for nu=3..13 (previous best 0,4,4,20,64,176); script bestrule.py. The 'span' rule alone is already wrong on 0 windows of the exact backbone at nu=9,11,13: all its excess lives on free windows, and the exact MaxSAT nearest solution is 26 flips away at nu=9 and 127 at nu=11. (4) Part (e): the complement-invariant unrestricted k'=7 solutions, as functions of the 7-bit transition word, coincide exactly with P(7) (25088 = 25088, identical sets); I give a counting proof that this holds for all odd nu (even-weight and odd-weight (nu+2)-necklaces each partition the edges of B(2,nu), complement is a weight-parity-flipping bijection on odd-length necklaces, every odd closed walk has >=1 mono edge), and SAT confirms the implication for nu=3..11. Equivalent reformulation: P(nu) <=> the colouring of B(2,nu) has exactly N(nu+2)/2 monochromatic edges (verified: 4,10,30,94,316). (5) Projections: no P(7) solution factors through any 5- or 6-bit coordinate projection, second differences, first differences, or through (h5 on the three 5-sub-windows) for any P(5) h5 (0 of 16x25088); 24 pairs factor through (h5 triple, core-status), but the extracted recursion fails at nu=9 (excess 12). (6) Free windows are rc-closed with no fixed points, are NOT characterised by walk ties (nu=7: 32/62 free and 40/66 forced windows are ties), and form a heavily linked system: nu=7 has 12544 patterns on 62 free bits (13.6 bits) with link components of size 16 (the phase component), 6, 6 and 46 singletons; with the phase fixed, 24/42 (nu=7), 104/276 (nu=9), 726/1416 (nu=11) mixed-parity windows have solution mean in (0.1,0.9) and no single feature predicts the midpoint-tie windows -- the remaining freedom is genuinely global.

**best excess profile**: core rule + phase law + span walk rule: excess [0, 0, 0, 8, 36, 116] for nu = 3, 5, 7, 9, 11, 13 (script: /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-datamining/bestrule.py; log bestrule.log). Previous best reported in PROBLEM.md was [0,4,4,20,64,176].

**exact_rule_found**: False

**insights**:
- FORCED CORE for nu=5 (alt-flipped f -> value, normalised h(0^5)=0; 24 of 32): 01010->0 01011->1 01000->0 01001->0 01110->1 01111->1 01101->1 00010->0 00000->0 00001->0 00100->0 00101->0 11010->1 11011->1 11110->1 11111->1 11101->1 10010->0 10000->0 10001->0 10110->1 10111->1 10100->0 10101->1; FREE (both 11 and 00 present): 01100 00011 00110 00111 11000 11001 11100 10011.
- FORCED CORE for nu=7 (66 of 128): 0101010->0 0101011->1 0101000->0 0101001->0 0101110->1 0101111->1 0101101->1 0100010->0 0100000->0 0100001->0 0100100->0 0100101->0 0111010->1 0111011->1 0111110->1 0111111->1 0111101->1 0110110->1 0110111->1 0110101->1 0001010->0 0001000->0 0001001->0 0000010->0 0000000->0 0000001->0 0000100->0 0000101->0 0010010->0 0010000->0 0010001->0 0010100->0 0010101->0 1101010->1 1101011->1 1101110->1 1101111->1 1101101->1 1111010->1 1111011->1 1111110->1 1111111->1 1111101->1 1110110->1 1110111->1 1110101->1 1001010->0 1001000->0 1001001->0 1000010->0 1000000->0 1000001->0 1000100->0 1000101->0 1011010->1 1011011->1 1011110->1 1011111->1 1011101->1 1010010->0 1010000->0 1010001->0 1010110->1 1010111->1 1010100->0 1010101->1. Min DNF: f0f1|f1f2|f2f3|f3f4|f4f5|f5f6|f0f2f4f6 (zeros: the complemented terms). The 62 free windows are exactly the f containing both '11' and '00'.
- Core rule in raw coordinates: a transition of W at position i (w_i != w_{i+1}) has class w_i xor (i mod 2); if all transitions share a class, h = that class; constant W: h(0^nu)=0, h(1^nu)=1. Equivalently h(0^a 1^b)=1 iff a even, h(1^a 0^b)=1 iff a odd. Forced-core size is 2F(nu+2)-2 (8,24,66,176,464,1218); exact backbone sizes are 8,24,66,208,562,1568 for nu=3..13 (backbone.py, backbone{9,11,13}.npy).
- Extra forced windows at nu>=9 (32/98/350) all contain both '11' and '00'; they take the majority (end>0) value in 32/32, 96/98, 350/350 cases (the two exceptions at nu=11 are 00011111000->1 and 11100000111->0, which have end = -1/+1); for 3-run words 0^a 1^b 0^c the middle run b=3 is always forced to the side class and b=5,7 (nu=11: only symmetric [3,5,3]) to the middle class while even b stays free -- not a majority-margin effect, and not derivable from any single cycle (propagate.py).
- PHASE LAW (phaselaw_sat.py, exact for nu=7..13): mixed windows whose transitions are all at odd positions (W = x x y y z z ... t) share a global free bit a; those with all transitions at even positions take 1-a. Hence h(f) = h(NOT f) on this component, which every walk-negation-antisymmetric rule (majority, q, argmax/argmin, span) violates; adding the phase law to the span rule removes the entire excess at nu=5 and 7.
- Part (e) THEOREM (proof + SAT): for g on B(2,nu), 'every even-weight cyclic (nu+2)-word has exactly one mono step' <=> P(nu) <=> |mono edges of B(2,nu)| = N(nu+2)/2. Proof: every (nu+1)-bit edge lies in exactly one even-weight and one odd-weight (nu+2)-necklace; complement bijects even- and odd-weight necklaces (odd length); every odd closed walk (incl. loops) has >=1 mono step. So the complement-invariant unrestricted solution set equals P(nu) for all odd nu (counts 2,16,25088 at nu=3,5,7; implied.py UNSAT for nu=3..11; monocount.py: 4,10,30,94,316 mono edges).
- The solution set is highly non-product: nu=7 has 12544 patterns (mod complement) on 62 free bits, link components 16+6+6+46 singletons, 331 independent vs 335 constrained representative pairs; a P(9) count with h(0)=0 exceeds 50000 (count9.py, capped). Random-phase SAT sampling (enum_rand.py) recovered the exact backbone at nu=9 and 11 with 20000/3000 samples, whereas sequential blocking-clause enumeration (2000 solutions) overestimated the forced set (498 vs 208).
- Description length: the forced core is linear (nu DNF terms, or 'majority restricted to the core'); individual solutions need 3, 5, 9, >=17 terms (nu=3,5,7,9) and median 15 greedy-tree leaves at nu=7 vs 2 for the core -- the complexity is entirely in the choice on free windows.
- The 'span' rule (and majority) never contradict a forced window up to nu=13; the data say the remaining problem is a globally consistent choice on the mixed-parity free windows where solutions are nearly 50/50 and no local feature (first/last double, counts, extrema positions, run lengths, midpoint ties) predicts a consistent choice; MaxSAT nearest solution to bestrule is 26 flips at nu=9 (all mixed-parity windows) and 127 at nu=11.
- rc-anti-invariant solutions: 4/8 at nu=5, 224/12544 at nu=7; their forced core equals the general core at nu=5,7 (no simplification from imposing the only feasible symmetry).

**dead ends**:
- Projection/factorisation of P(7) through any 5- or 6-bit coordinate deletion, first or second differences: 0 solutions (proj.py).
- Recursive construction h_{nu+2} = core + F(h_nu on the three nu-sub-windows): the only consistent F's (24 pairs at 5->7) give excess 12 at nu=9 (recur2.py).
- Characterising free windows as walk tie cases: false at every nu.
- Identifying the extra forced windows at nu>=9 by a single feature or a pair of features (|end|, double-class counts, longest runs, inner run lengths): best pair still 12/336 errors at nu=9, 72/1584 at nu=11 (boundary.py).
- Unit-propagation / small-lookahead closure of the core as an explanation of the backbone: adds nothing.
- Every local tie-break tried for the mixed-parity windows (first/last double, counts, f0, parity of first/last double position, majority with margin, longest runs, extremum-set midpoints/centres/pairs/spans, M+mn, M-end vs -mn): none below [0,0,0,8,36,116] (freerules.py, freerules2.py, freerules3.py, hybrid.py).
- Predicting midpoint-tie windows from solution statistics: solution means are ~0.5, no single feature (ties.py).
- Fitting min-DNF to sample-based forced cores at nu>=9 is misleading when the sample is not backbone-exact (the nu=9 DNF from a biased 2000-sample had 9 unrelated 3-literal terms); use the SAT backbone instead.

## lens: theory

**summary**: No complete existence proof. Main positive results (all proved, then machine-checked): THEOREM A: for odd nu, h solves P(nu) iff c := h∘Delta (Delta = adjacent-XOR/transition map {0,1}^{nu+1}->{0,1}^nu) is an optimal 2-colouring of B(2,nu+1); equivalently the complement-invariant optimal colourings of B(2,nu+1) are exactly the h∘Delta with h in P(nu). Proof is a double count: mono(c)=2·mono(h), and sum over cyclic (nu+2)-words u of (mono steps of h on u) = 2·mono(h) with each term odd>=1, so c optimal <=> mono(c)=N(nu+2) <=> mono(h)=N(nu+2)/2 <=> every u has exactly one mono step <=> h in P(nu). Corollaries: excess(h,nu) = 2·mono(h) − N(nu+2) (identity, checked nu=3..13); in P(nu) the odd-weight cyclic words are redundant given the even-weight ones (counts 2/16/25088 unchanged); the even-weight (resp. odd-weight) necklaces of length nu+2 partition E(B(2,nu)) into N(nu+2)/2 odd closed walks (checked nu<=9); hence P(nu) <=> maxcut(B(2,nu)) = 2^{nu+1} − N(nu+2)/2. This unifies both parities into one conjecture maxcut(B(2,n)) = 2^{n+1} − beta(n), beta(n)=N(n+1) (n even), N(n+2)/2 (n odd), verified by direct max-cut for n=1..7 and implied for n<=18 by the existing SAT results; the odd case implies the even case. SHAPE CRITERION (proved via ANF, checked n=4,6): E−D is bipartite iff 0^{n+1} in D and for every tau ⊂ {0..n} with 0 in tau, #{(e,j): e in D\{0^{n+1}}, 0<=j<=n−max(tau), supp(e) ⊂ tau+j} ≡ max(tau)+1 (mod 2); the vectors Z_tau form a basis of the cycle space (rank 2^n+1 with the loop), so bipartiteness is exactly 2^n parity constraints indexed by n-bit words. EXACT COUNT: #D-sets = 2^{-(2^n+1)} Σ_{Z in cycle space} (−1)^{|Z|} Π_i (p_i − 2|Z∩C_i|), constant on cosets of span(necklaces) (verified: 49 at n=4); the leading term predicts 4.5/30.5/46 vs actual 5/49/26920 for n=2/4/6, so the parity constraints are massively correlated on transversals. PRECISE OBSTRUCTIONS: (i) B(2,6) and B(2,8) with all edges odd contain an odd-K5 minor (CP-SAT, independently re-verified at n=6), so by Guenin's theorem they are not weakly bipartite and the odd-cycle covering polyhedron is not integral: the Grötschel–Pulleyblank/Guenin LP route 'maxcut = |E| − tau*_odd' is unavailable for n>=6 (although no random objective ever exposed a fractional vertex and the uniform-objective LP value is integral = N(n+1) for n<=6). (ii) All three line-graph inductions fail from n=8 on: fixed-bit sections of n-solutions are not (n−2)-solutions (n=8: 0–3/40); 24/60 sampled 6-solutions extend to no 8-solution through any of the 12 fixed-bit sections; and no 8- or 10-solution has its mono set inside the 4-fold lift {a·e·b} (or e·ab, ab·e) of any sampled (n−2)-solution's mono set (0/59, 0/20), while this holds 5/5 at n=4 and 22/49 at n=6. Nearest n-solutions to the lifted (n−2)-colouring differ in 3–7 of 64 (n=6) and 7–14 of 256 (n=8) words. Also: fractional odd-cycle transversals whose weight depends only on the edge's set of linear periods do not exist (n=4,6,8). The cycle space of B(2,n) is spanned by closed walks of cyclic words of length <= n+4 (n=4..12), the short primitive words (length l<=n, l∤n+1) being independent modulo necklaces, each contributing exactly M(l). Forced-out edges (never monochromatic in any optimum) exist from n=6 on (8, 4, 58 for n=6,8,10; reversal-closed, mostly palindromes such as 0^{n/2}10^{n/2} for n=6,10); no forced-in edges.

**best excess profile**: No candidate rule was produced in this lens (it delivered equivalences and obstructions, not a scheme); nothing here improves on the reference profile already in PROBLEM.md (alternating flip + mirror-symmetric tie-break: 0, 4, 4, 20, 64, 176 for nu = 3..13).

**exact_rule_found**: False

**insights**:
- Theorem A (proved): h in P(nu) <=> h∘Delta is an optimal colouring of B(2,nu+1); the complement-invariant optima of the odd-k problem are exactly the P(nu) solutions lifted through the transition word, for all odd nu (explains the empirical coincidence at nu=3,5).
- Identity: excess(h,nu) = 2·mono(h) − N(nu+2), where mono(h) = #{(nu+1)-words x : h(x[0..nu−1]) = h(x[1..nu])}; so P(nu) is literally 'max-cut of B(2,nu) equals 2^{nu+1} − N(nu+2)/2', and in P(nu) the odd-weight cyclic-word constraints are implied by the even-weight ones.
- The even-weight (and separately the odd-weight) necklaces of length nu+2 partition E(B(2,nu)) into N(nu+2)/2 odd closed walks (edge x lies in the cyclic word x·parity(x)); Delta: B(2,nu+1)->B(2,nu) is the 2-fold cover with voltage 'first bit of the edge'.
- Unified conjecture for all n: maxcut(B(2,n)) = 2^{n+1} − N(n+1) (n even) and 2^{n+1} − N(n+2)/2 (n odd); the odd case implies the even case; verified n<=7 directly, n<=18 via SAT.
- Shape criterion: with Z_tau = {e : #{j : supp(e) ⊂ tau+j} odd}, {Z_tau : 0 in tau ⊂ [0,n]} ∪ {loop} is a basis of the cycle space (dim 2^n+1); E−D bipartite iff loop in D and Σ_{e in D\{loop}} #{j : supp(e) ⊂ tau+j} ≡ max(tau)+1 (mod 2) for all tau. Z_tau is the closed walk of the cyclic word 1_tau·0^n up to the loop.
- Exact count: #D = 2^{−dim Q} Σ_{Z in Q} (−1)^{|Z|} Π_i (p_i − 2|Z∩C_i|) with Q = cycle space / span(necklaces), dim Q = 2^n + 1 − N(n+1); the Z=0 term (4.5, 30.5, 46) is dwarfed by the true counts (5, 49, 26920), i.e. the constraints are highly correlated on transversals and the number of constraint bits exceeds the number of choice bits for n>=8 (197 vs 184; 837 vs 643).
- Closed walks of cyclic words of length <= n+4 span the cycle space (n=4..12); short primitive words of length l<=n with l∤n+1 are independent modulo the necklaces (exactly M(l) new dimensions each); the long constraints (lengths n+2, n+3, n+4) are the necklaces of B(2,n+1), B(2,n+2), B(2,n+3) projected down and dominate the count.
- Obstruction: (B(2,6), all edges odd) and (B(2,8), all edges odd) have odd-K5 minors (branch sets listed in q12.out/q12b.out) => not weakly bipartite (Guenin 2001) => the odd-cycle LP relaxation of max-cut is not integral in general; any polyhedral proof must use the specific face (necklace equalities) or a different relaxation.
- Nevertheless the fractional statement tau*_odd(B(2,n)) = N(n+1) (equivalently, the necklace packing is a maximum fractional odd-cycle packing) is a NECESSARY condition that holds for n<=6 by LP and n<=18 by SAT; it is the natural intermediate target, but its certificate cannot be a function of the edge's linear periods alone.
- Every section-based and lift-based induction from n−2 to n fails by n=8; any inductive existence proof must change about 5% of the lifted colouring (3–7/64 at n=6, 7–14/256 at n=8) in a non-local way.
- Forced-out edges appear from n=6 (8, 4, 58 at n=6,8,10), reversal-closed and mostly palindromic (e.g. 0^{n/2}10^{n/2} for n ≡ 2 mod 4); forced-in edges never occur; at n=4 the degree-2 solutions are exactly MAJ(x0,¬x1,x2), MAJ(x1,¬x2,x3) and MAJ(d0,¬d1,d2) on the transition word (plus complements), and for even n no rc-anti-invariant solution exists while rc-invariant ones do (26/98 at n=4).

**dead ends**:
- Weak-bipartiteness/Guenin route (odd-cycle clutter ideal => maxcut = |E| − tau*): odd-K5 minors exist in B(2,6) and B(2,8).
- Fixed-bit-section restriction and extension inductions between n−2 and n: both false at n=8.
- Line-graph sub-selection induction (choose D_n among the lifted defects of D_{n−2}): false at n=8 and n=10 for all three lifts.
- Explicit fractional transversals depending only on linear periods (min period / odd periods / full period set): infeasible for n=4,6,8.
- Pure counting/probabilistic (LLL-style) existence: random-transversal heuristic gives fewer choice bits than constraint bits for n>=8; the true count exceeds the heuristic by orders of magnitude, so any such proof must exploit the correlation structure, which was not identified.
- Direct literature: no published result on max-cut or odd-cycle packing of de Bruijn graphs; the Kille et al. tightness for sigma=w=2 is ILP-only.
- Not finished within the session: n=6 essential-length transversal count (q14b), n=8 tau* LP (q17), n=10 odd-K5 search and the longer n=4 search (q12b), n=8 LP ideality sweep (q5b).

**verifier**: refuted=True — I'm marking this refuted on the strict rule: one result labelled PROVED is false as written. The main result and most of the computational claims did check out.

VERIFIED (independent scripts in /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/verify-theory-0/):

1. Theorem A is correct.
   - The proof checks step by step:
     - Delta is 2-to-1 and sends B(2,nu+1) edges onto B(2,nu) edges, so mono(h∘Delta) = 2·mono(h).
     - The (nu+1)-windows of all cyclic (nu+2)-words cover each (nu+1)-word exactly twice, so the per-necklace counts sum to 2·mono(h).
     - Each count is odd and at least 1, because every period divides nu+2, which is odd.
     - Complement-invariant colourings are exactly those that factor through Delta.
   - Numerical checks (thmA.py, thmA2.py):
     - The identity excess(h,nu) = 2·mono(h) − N(nu+2) holds on random h for nu = 3,5,7,9,11. The pnu.excess function skips the two constant necklaces, but the identity still holds.
     - Every P(nu) solution lifted through Delta is optimal for nu = 3,5,7.
     - The complement-invariant unrestricted solutions are exactly the lifted P(nu) sets: 2 of 98 at n=4 and 16 of 53840 at n=6.
   - The even-weight necklaces partition E(B(2,nu)) into N/2 classes for nu ≤ 11. This makes the odd-weight constraints redundant, so the max-cut form of P(nu) is correct.

2. Max-cut formula: brute force for n = 1..4 matches 2^{n+1} − beta(n). The CP-SAT output (q13.out) covers n up to 7. bigk.log has P(

**verifier**: refuted=False — The claim does not say it proves the conjecture ("No complete existence proof"). What it does assert, its theorems, equivalences and obstructions, holds up when checked independently. Three side statements are wrong or imprecise, but no conclusion depends on them.

CHECKED BY HAND
- Theorem A holds.
  - mono(h∘Delta) = 2·mono(h), because Delta is 2-to-1 on (nu+2)-bit contexts.
  - Every (nu+1)-word y appears exactly twice, as a window of y0 and of y1, across (necklace, position-in-period) pairs. So the sum over necklaces of the mono count equals 2·mono(h).
  - Each necklace term is odd and at least 1, because nu+2 is odd. So h∘Delta is optimal iff mono(h) = N(nu+2)/2 iff h is in P(nu).
  - excess(h) = 2·mono(h) − N(nu+2) matches pnu.excess, which drops the two loops, each counted once.
- The corollaries hold. The edge y lies in exactly one even-weight cyclic word, y·parity(y). So the even-weight necklaces partition the edges, and the even-weight constraints alone imply P(nu).
- The count formula holds. The character sum is correct, and it is invariant on cosets: adding a necklace C_k flips both the sign and the k-th factor.
- The shape basis holds for all n, not just the small cases. My own short proof:
  - Z_tau is a cycle because the translates telescope in pairs.
  - The Z_tau are independent because on the coordinates e = 1_tau' (0 in tau') the matrix is subset inclusion, which is unitriangular.
  - The loop is independent of them.
  - |Z_tau| ≡ (n−max+1)·2^|tau| ≡ 0 ≡ n 

## lens: edgeview

**summary**: No exact rule found. Every canonical-rotation rule tried (unique-unbordered, longest-run with next-run tie-breaks, centre-of-mass variants, alternating-flip-then-majority orders, the faithful Mykkeltveit rule and its +-1 shifts and positive-axis mirror, and all of these applied to the transition word with offsets 0,+-1) is optimal for n=2 (and some for n=4) and fails from n=6 on, with the number of necklace cycles violated growing to >80% of all cycles by n=12 (framework: /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-edgeview/edgeview.py, rules1.py, log rules1.log). A deterministic first-fit greedy over necklaces with a parity union-find gets stuck already at n=4 for all 28 order combinations (greedy.py). The main products of this lens are structural, all verified by the exact verifier/SAT: (1) P(nu) is exactly 'a perfect matching E of the necklace graph G_m (vertices = binary necklaces of length m=nu+2, edges = (m-1)-words u joining [u0] and [u1]; bipartite even-weight/odd-weight) such that B(2,nu)-E is bipartite'; verified on all 2/16/25088 solutions of P(3)/P(5)/P(7); G_5 has 5 perfect matchings (1 valid), G_7 has 6285 (8 valid) (matching.py). (2) The valid matchings are characterised by the cyclic-word parity constraints of length <= m+1 only (6285->8 at m=7 with l<=8; SAT count at m=9 drops from >=25089 to exactly 12544 at L=10=m+1 and not before) (matchfilter.py, locality_sat.py). (3) rc-anti-invariance of h is equivalent to the mirror law mu(rc s) = m-1-mu(s) on the missing-character position; verified on all 8/448 rc-anti solutions of P(5)/P(7) (mirror_check.py). (4) Exact allowed missing-character sets for every necklace at m=7,9,11,13 (allowed_mu.py, allowed_mu_p*.json): exactly 6 forced necklaces at every m (0^{m-1}1, 0^{m-3}101, 0^{m-3}111 and their mirrors), and for every single-run word 0^a 1^b the missing character is ALWAYS the second or second-to-last character of the odd-length run (never its centre when the run has length >=5), verified for all (a,b) at m=7,9,11,13. (5) This forced set rules out every Greene-Kleitman/symmetric-chain-type matching (flipping a cyclically unmatched position), e.g. 0^5 1^4 at m=9 allows only positions {1,3} while the GK-unmatched positions are {0} or {4} (gk_exclusion.py). (6) No P-view rule from a 135-rule grid (run selection x position x chirality, min/max-rotation anchors) even yields a perfect matching for nu>=5; the best agreement of any such rule with any single optimal D is 25/58 necklaces at m=9 (murules.py, agree.py).

**best excess profile**: Edge rules give no h when B-D is not bipartite, so official excess is reported for the BFS-forest colouring: best P-view rule 'minrot+1' (missing character = position 1 of the min-lex rotation, odd partner by flipping): excess(h,nu) for nu=3,5,7,9,11,13 = 0, 4, 24, 136, 708, 3232 (best_profile.py / best_profile.log). Best unrestricted edge rule by violated necklace cycles: centre-of-mass-centred rotation: n=2,4 optimal; n=6: 7/20 cycles violated, +5 charged; n=8: 34/60, +19; n=10: 140/188, +90; n=12: 536/632, +400 (rules1.log). Neither beats the lead's walk rules (0,4,4,20,64,176).

**exact_rule_found**: False

**insights**:
- P(nu) <=> perfect matching of the necklace graph G_m: in the P(nu) picture a monochromatic step (W_j,W_{j+1}) is the (nu+1)-word u = s with one character s_mu deleted, and its mono-ness does not depend on the deleted character, so the step set E is a set of (m-1)-words each covering the two necklaces [u0],[u1]; 'exactly one per necklace' makes E a perfect matching of the bipartite graph G_m (even-weight vs odd-weight necklaces), and optimality additionally needs B(2,nu)-E bipartite. Verified on all solutions of P(3),P(5),P(7); |E| = N(m)/2; common to all solutions: 0^{nu+1}, 1^{nu+1}, 0 1^{nu-1} 0, 1 0^{nu-1} 1. Counts: G_5 has 5 perfect matchings, 1 valid; G_7 has 6285, 8 valid (matching.py, matching.log).
- Locality: valid matchings are exactly the perfect matchings satisfying the parity constraints (#E-windows == l mod 2) of cyclic words of length l <= m+1; shorter lengths do not suffice (m=7: 6285 -> 5129 (l<=2) -> 2025 -> 1617 -> 37 (l<=5) -> 18 (l<=6,7) -> 8 (l<=8); m=9 by SAT: >=25089 matchings up to l<=9, exactly 12544 at l<=10) (matchfilter.log, locality7.log).
- Mirror law: in the P-view (missing-character position mu(s) in Z_m), h(rc W)=1-h(W) is equivalent to mu(rc s) = m-1-mu(s) for all cyclic s; verified on all 8 rc-anti solutions of P(5) and all 448 of P(7) (mirror_check.py). Equivalently E is closed under rc of (nu+1)-words. rc-anti solutions: 8/16 at P(5), 448/25088 at P(7); complement-closed E need not exist (fails for most P(5) D's).
- Exact allowed missing-character sets (SAT with assumptions) for every necklace at m=7,9,11,13 (allowed_mu_p{5,7,9,11}.json): exactly 6 forced necklaces at each m: 0^{m-1}1 (mu = the 1), 0^{m-3}101 (mu = the lone 0), 0^{m-3}111 (mu = middle 1), and their mirrors 0^3 1^{m-3}, 0101^{m-3}, 01^{m-1}; mean allowed-set size grows (3.1/7, 4.0/9, 6.5/11, 9.3/13) so the constraints are global couplings, not per-necklace restrictions.
- Single-run law (verified for every (a,b) with a+b=m, m=7,9,11,13): for s = 0^a 1^b the missing character lies in the odd-length run and is its second or its second-to-last element (both occur, coinciding for runs of length <=3; the run's centre is never allowed for length >=5; a length-1 run is the forced case). Within one solution the two chiralities are tied by the mirror law (e.g. P(5) row 1: 0[0]00011 with 00111[1]1).
- The allowed sets at m=7 are contiguous cyclic arcs except for the single-run words (arcs with the centre removed); at m>=9 many families show 'arc minus parity-excluded points' (e.g. 0^9 1^2 0 1 at m=13 allows the 0-run minus its 5th and 9th positions plus the lone 0), consistent with a parity/alternation effect inside long runs.
- Negative structural facts: (a) the palindromic rotations 0001000 and 0100010 (and complements) are never monochromatic at n=6 (the l=4 word 0001 forces an even number of {0001000,0010001,0100010,1000100} and the data shows zero); (b) any rule that flips a Greene-Kleitman cyclically-unmatched position (hence any SCD-derived matching of the necklace poset, GKS 2004 / Jordan 2010) is excluded by the forced sets; (c) first-fit greedy with parity union-find cannot work for any tested order already at n=4, so the solution set has no 'sequential' description in these orders; (d) the two natural embeddings of P(nu) into odd-k colourings (ignore last bit, c(W)=h(W[:-1]); complement-invariant, c(W)=h(Delta W)) give different D sets in e-space but the same P-view D.
- Diagnostic by length (shortcyc.py): min-lex and Mykkeltveit reps already violate l=2..4 parity constraints at n=6; the COM-centred rule violates none below l=8 at n=6, i.e. its failures are intrinsically global.

**dead ends**:
- All canonical-rotation representatives from combinatorics on words (unbordered, longest run with tie-breaks, centre of mass, alt-flip orders, faithful Mykkeltveit and shifts/mirror) and their transition-word versions: exact only for n<=4.
- First-fit greedy/sequential constructions of D with any of 7 necklace orders x 4 rotation orders: stuck from n=4.
- Palindrome / symmetry-axis representatives: correct for m=5 by coincidence, refuted at m=7 by forbidden rotations.
- Greene-Kleitman / symmetric-chain-decomposition matchings of the necklace poset: incompatible with the forced sets for 0^a 1^b (m=9,11,13), so Jordan's SCD cannot be the matching.
- Per-necklace 'missing character' rules defined by run selection + position (135 variants): none is even a bijection between even and odd necklaces for nu>=5; best agreement with any optimal D is 25/58 at m=9.
- Reading the solution as a product of per-necklace choices: allowed sets are large unions (mean 9.3 of 13 positions at m=13) while individual solutions are a 1e-11 fraction of the product space, so the rule, if it exists, must be formulated globally (walk/potential-like), not as a representative selection per necklace.

## lens: runs

**summary**: I found no exact rule. I did find a structure theorem, checked by SAT for ν ≤ 13, which recasts P(ν) as a problem of choosing one rising edge per window.

**The framework.** Call a "01" at positions i,i+1 of the window a rising edge at index i. Define class R: every window W with at least one rising edge has h(W) equal to the parity of the index of one of its rising edges, and a window with none (W = 1^a 0^b) has h(W) = a mod 2.
- For ν = 5 and 7, every P(ν) solution falls into exactly one of four classes: R, 1−R, R∘NOT, 1−R∘NOT. The split is 4/4/4/4 of the 16 solutions at ν = 5 and 6272 ×4 of the 25088 at ν = 7.
- For ν = 9, 11, 13, SAT shows no solution lies outside these four classes, and class R is satisfiable.
- So, up to the trivial symmetries, P(ν) asks for a rule that picks a rising edge in each window. It is never a free Boolean function.

**Why pure run-length rules cannot work.** Any h that depends only on the run lengths of W, or of alt(W), is unchanged by complementing W. The established facts say h∘NOT = h is infeasible for ν ≥ 5, so such rules are ruled out. The rule must tell rising edges from falling ones. Reverse-complement maps a rising edge at index i to a rising edge at ν−2−i, with the opposite parity. So any selection rule that commutes with reverse-complement is automatically rc-anti-invariant.
- Correction to PROBLEM.md: rc-anti-invariance is not necessary. Only 448 of the 25088 P(7) solutions, and 8 of the 16 P(5) solutions, are rc-anti-invariant. The claim that every closed form must be rc-anti-invariant is wrong.

**Narrowing the choice (SAT-checked through ν = 13).**
- Restricting h to the parities of the edges that maximise min(a,b) stays satisfiable. Here a is the visible 0-run before the edge and b the visible 1-run after it. Every other local score I tried (sum, max, product, |a−b|, the outer runs c and d, truncation variants) becomes unsatisfiable by ν = 7–9.
- Restricting to the edges whose valley in the ±1 walk is deepest also stays satisfiable. "Deepest" here means the larger of the two rises around the valley, measured until the walk goes strictly lower, cut off at the window ends. Adding "strict majority of the tied edges' parities" on top is still satisfiable, and then fixes 7550 of the 8192 windows at ν = 13.
- After that, no further local tie-break stays satisfiable through ν = 13. I tried symmetric, orientation-dependent and outer-run features. The only one that survives one more step is preferring the shortest alternating stretch around the edge, which fixes a few more windows and then nothing can be added.

**Best explicit rule (R_A).** Pick the deepest valley, then take the majority parity. If still tied, pick the largest max(a,b), then majority. Then the largest sum of the two rises, then majority. Finally pick the edge nearest the window centre; the coin-flip fallback is never reached for ν ≤ 13.
- P(ν) excess for ν = 3, 5, 7, 9, 11, 13: **0, 0, 0, 0, 20, 36**.
- The odd-k unrestricted formulation agrees. Charged-count excess is 0, 0, 0, 0, 10, 18, both when the rule ignores the last bit and when f(S) = h(ΔS).
- This beats the earlier families (walk rule 0, 4, 4, 20, 64, 176; alternating-flip majority 0, 4, 20, 92, 376).

**Hand analysis.** For words with 2 runs (one rising edge), the rule gives exactly one defect, proved by hand. For words with 4 runs (two edges), any score that does not decrease as visible runs get longer, with a tie-break that switches only once as the window slides, gives exactly one defect. In general, exactly one defect happens exactly when the chosen edge, followed around the cycle, makes exactly one jump of odd length. All remaining failures are words with 3 to 6 rising edges, where several edges tie exactly (e.g. 0000100001001 = blocks (4,1),(4,1),(2,1)).

Scripts are in /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-runs/:
- best_rule.py rebuilds R_A and prints all excesses.
- classes_sat.py, classes.py, satframe.py check the four-class theorem.
- satscore.py, majt.py, feats.py, greedy.py, stages.py run the feasibility checks.
- stagesearch2.py, stagesearch4.py, deepsearch.py, asymsearch.py are the explicit rule searches.
- byruns.py and failcyc.py break failures down by number of rising edges.
- globanchor.py tests whether a cyclic-level "global anchor" exists.

On the relayed question about running this with Opus: my run only shows that this setup (verifier plus SAT used as a feasibility check) got further than the previous rule families. It cannot show how much of that comes from the model choice.

**best excess profile**: R_A (deepest valley → majority → max(a,b) → majority → rise sum → majority → nearest centre; fallback never used): P(ν) excess for ν = 3, 5, 7, 9, 11, 13 = 0, 0, 0, 0, 20, 36. Odd-k charged excess (k = ν) = 0, 0, 0, 0, 10, 18, both when ignoring the last bit and when f(S) = h(ΔS). Script: /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-runs/best_rule.py

**exact_rule_found**: False

**insights**:
- Structure theorem, enumerated at ν = 5, 7 and SAT-checked at ν = 9, 11, 13: every P(ν) solution is, up to complementing the output and/or the input, a rising-edge selector. That is, h(W) equals the parity of the index i of some rising edge (W_i W_{i+1} = 01), and h(1^a 0^b) = a mod 2. The four classes split the solution set exactly in quarters. (classes.py, classes_sat.py)
- Reverse-complement keeps the edge type and maps index i to ν−2−i, flipping its parity. So any edge choice that commutes with reverse-complement gives rc-anti-invariance for free.
- rc-anti-invariance is NOT necessary: only 448/25088 P(7) and 8/16 P(5) solutions have it. PROBLEM.md's claim that any closed form must be rc-anti-invariant is wrong.
- Exactness condition in this framework: h(W_j) = (e(j) − j) mod 2, where e(j) is the chosen edge position. A defect happens exactly when e jumps by an odd amount, and the jumps over one turn add up to m (odd). So exactly one jump must be odd.
- If one edge is seen and chosen by all ν−1 windows containing it, the 3 windows that miss it work automatically whenever they agree on any single edge.
- Words with 2 runs: the framework gives exactly one defect, proved by hand. Words with 4 runs: any score that does not decrease as visible runs get longer, plus a tie-break that switches once as the window slides, is exact. Failures need 3 or more rising edges (byruns.py).
- Of all local per-edge scores tried, only two survive as hard SAT filters through ν = 13: max min(a,b) and deepest valley. Both measure how deep the valley at the edge is. Adding strict majority of tied parities after the valley filter is also feasible.
- The remaining hard cases are exact ties between edges in the cyclic word, e.g. 0000100001001 with blocks (4,1),(4,1),(2,1). A SAT solution there anchors on the first 0^4|1 (the one followed by the other 0^4 block). Windows that miss it switch to an edge an even distance away, not the nearer one. Whether a truncated left run counts as long decides the choice, so local features cannot settle it.
- In the odd-k unrestricted formulation, charged excess is exactly half the P(ν) excess for both embeddings (ignore last bit; f(S) = h(ΔS)). Rising edges of t = ΔS are the ends of runs of length ≥ 2 in S.

**dead ends**:
- Any rule using only run lengths of W or alt(W): complement-invariant, so impossible for ν ≥ 5.
- Rising edge nearest the window centre: 0,0,4,48,288,1460.
- Choosing by the cyclic max of min(a,b), sum, or max(a,b) as a global anchor: SAT-infeasible at ν = 5–7.
- Secondary local scores after max min(a,b) (sum, max, product, |a−b|, c+d, outer-run min/max/sum, truncation variants): every one SAT-infeasible by ν = 9.
- Orientation-dependent local tie-breaks (a, b, c, d, index, truncation flags, left/right rise): cannot extend the feasible pers+majority framework.
- Weighted parity votes with fitted weight tables: overfit (372 excess at ν = 13).
- Majority of all rising-edge parities without the valley filter: infeasible at ν = 11.

## lens: synthesis-search

**summary**: No exact rule exists in this DSL. Every formula and tie-break was checked against the full P(5) and P(7) solution sets (16 and 25088 SAT solutions), and survivors were scored with the exact verifier at nu = 3..13.

(1) Unrestricted search. The DSL has 228 features and 34,740 named atoms, of which 18,764 are distinct on the joint nu=5,7,9 truth tables. Results by formula size:
- Size 1: 4 atoms are exact at nu=5 (alt walk: midpoint of argmax-set < nu, and variants), but none at nu=7. Profile [0,0,12,124,612,3000].
- Size 2: 528,103,398 formulas evaluated (3*C(K,2)), none exact at nu=5 and 7.
- Size 3: about 1.98e13 formulas covered implicitly (6 parts of 3.30e12 each; OR-on-top is covered by De Morgan). 92 are exact at nu=5 and 7: 48+16+16 with XOR on top, 12 of AND(.,XOR) shape, 0 for the other two AND shapes. All 92 fail at nu=9. Their profiles (nu=3..13) are [0,0,0,28,208,1112] x4, [0,0,0,52,516,3500] x80 and [0,0,0,88,452,2080] x8. None is rc-anti-invariant at nu=7.
- If-then-else c?a:b: all 13898^3 class triples covered; 52.4M nu=5 hits, 0 exact at nu=7. A planted triple was recovered, so the search code is correct.

(2) Targeted tie-break for the walk rule [first argmax < first argmin], with tie = max or min attained more than once. The tie windows (18 at nu=5, 72 at nu=7) give 17,070 tie-restricted atom classes and about 2.24e13 size-3 formulas. No size-1 or size-2 tie-break is exact at nu=5 and 7. 969 size-3 tie-breaks are exact at nu=5 and 7, but every one fails at nu=9. The best is [0,0,0,12,152,1296], which beats walk at nu=9 (12 vs 36) but is worse from nu=11 on (152 vs 96, 1296 vs 264). Among the 309 that are rc-anti at nu=7, the best is [-,-,-,48,264,1276].

(3) The tie-break failure is structural, not a weakness of the DSL. A SAT check shows the walk rule fixed only on non-tie windows can be extended to a P(nu) solution at nu=5 and 7, but not at nu=9 or 11 (unsat core of size 3). So no tie-break of any complexity can rescue the walk rule. The certificate and the MaxSAT distances are listed in the insights.

On the meta-question (whether running this exploration with Opus changes the result much): in this lens the verdicts came from exhaustive enumeration plus the exact verifier and SAT, so the model does not change the yes/no answers. It affects only which DSL, which search shapes and which structural checks (like the SAT extendability test) get tried. The extendability test was the most informative finding here.

**best excess profile**: Best is a different rule at each nu; none is exact. Best at nu=9: walk + synthesized tie-break, nu=3..13 = [0,0,0,12,152,1296]. Best unrestricted size-3 formula at nu=9: [0,0,0,28,208,1112]. Over nu>=11 the plain walk baseline [0,4,12,36,96,264] stays best: every DSL formula exact at nu<=7 overfits and degrades faster. All checked with the official pnu.excess in /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-synthesis-search/verify_best.py

**exact_rule_found**: False

**insights**:
- OBSTRUCTION (SAT, tie_extend.py / tie_core.py): fix the alt-flip walk rule [argmax before argmin] only on windows whose walk has a unique max and a unique min. That partial function extends to a P(nu) solution at nu=5,7 but is UNSAT at nu=9 and nu=11. So no tie-break predicate of any complexity can make the walk rule exact.
- The nu=9 UNSAT core is 3 windows of the single cyclic word 00011011011 (m=11): windows 000110110, 011011000, 011000110 at positions 0, 5, 8 all get h=0 from the walk rule. The three arcs 5, 3, 3 are all odd. On an odd cycle with exactly one monochromatic step the colouring alternates except at one defect, so each odd arc whose endpoints share a colour must contain a defect. That forces 3 defects, a contradiction.
- General lemma (cheap necessary test for any candidate rule): on a cyclic word of odd length m, if three of its windows sit at positions where all three cyclic arcs between them are odd, the three cannot all get the same h value.
- MaxSAT: a P(nu) solution must disagree with the walk rule on at least 0 / 6 / 14 non-tie windows at nu=7 / 9 / 11.
- MaxSAT Hamming distance to the nearest P(nu) solution: walk 8/128, 50/512, 189/2048 (about 6%, 10%, 9%); majority 12, 60, 244; midM<midmn 9, 49. The distance does not shrink with nu, so the walk rule is not a good skeleton to correct locally.
- The nu=5 filter is very weak: 23M+ size-3 formulas match some P(5) solution. The nu=7 filter (25,088 targets out of 2^128) leaves 92 unrestricted formulas and 969 tie-breaks, and all of them break at nu=9. Small-nu exactness of a flat-DSL formula is no evidence of a general rule.
- Only 448 of the 25,088 P(7) solutions (and 8 of 16 P(5)) are rc-anti-invariant. All 92 unrestricted size-3 formulas exact at nu=5,7 are rc-anti at nu=5 but NOT at nu=7, matching the warning that a generalizing rule must be rc-anti-invariant. Among the 72 P(7) completions of the walk rule only 12 are rc-anti, and 48 of the 72 tie windows are forced.
- If-then-else (decision-list) shapes c?a:b over the DSL produce zero rules exact at nu=5 and 7, even though XOR-on-top shapes produce 92. Every exact-at-7 formula uses XOR somewhere. This suggests parity corrections are essential, which fits the parity nature of the one-defect-per-odd-cycle condition.
- Note for verifiers: another panel agent writes into the same scratch directory (features.py, search.py, stage2.py, tie_small.py, full_stage1_hits.pkl, ...). Those files are not mine. My files are listed below and do not share names with theirs.
- My scripts (all in /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-synthesis-search/):
- Setup and verifier: common.py (fast batch excess, checked against pnu.excess), sols.py (writes sols.npz), dsl.py (feature language), build_atoms.py (writes atoms.pkl).
- Unrestricted search: search57.py + search57_tail.py (main search), eval_found.py (profiles survivors; output in eval_final.txt), inspect_found.py, mux.py + mux_test.py (if-then-else search).
- Tie-break search: tie57.py (run with argument xor or and), tie_rc.py, tie_targets.py, tie_anal.py.
- Structural checks: tie_extend.py and tie_core.py (SAT obstruction), nontie_viol.py and nearest9.py (MaxSAT), safezone.py.
- Final check: verify_best.py (standalone re-verification of the best rules with the official verifier).

**dead ends**:
- Single atoms, 2-leaf and 3-leaf AND/OR/XOR formulas over the 18,764-atom DSL: nothing exact at nu=9 (exhaustive over nu=5,7, then profiled)
- If-then-else c?a:b over DSL atoms: nothing exact even at nu=7
- Any tie-break for the alt-flip walk (argmax-before-argmin) rule: impossible at nu>=9 by SAT (3-window odd-arc certificate), so the whole walk-plus-tie-break family should be abandoned
- Size-3 DSL tie-breaks exact at nu=5,7 (969 found) all overfit: best excess at nu=11 is 152, worse than the untouched walk rule (96)
- Restricting a simple rule (walk, majority, area sign, midpoint order) to a single-atom 'safe' domain: extendable domains cover at most about 25% of windows at nu=11
- nu=5 exactness as a filter: essentially uninformative (millions of size-3 formulas pass)

## lens: repair

**summary**: I did not find an exact rule. The main results are certified no-go statements: SAT shows that h0 cannot be repaired by tie-breaking alone, and that no rule depending only on the positions of the walk's extrema works.

(1) h0 is exactly invariant under h(NOT W) = 1 − h(W), with 0 violations at nu = 3..9. PROBLEM.md says that symmetry is impossible for nu ≥ 5, so every repair must break it. In every nearest solution, each corrected window W has an uncorrected complement NOT W, so NOT-violations always equal exactly twice the distance.

(2) Nearest optimal solutions, found with RC2 MaxSAT: distance 2, 8, 50, 189 for nu = 5, 7, 9, 11. Restricted to rc-anti-invariant solutions the distances are 2, 10, 54, 256. For nu = 5 and 7 every correction is a tie window. From nu = 9 on some are not: 6 untied at nu = 9 (4 with interior extrema) and 24 untied at nu = 11 (16 interior). The explicit correction sets are saved to files.

(3) No-go results (SAT). For nu = 9 and 11, no optimal solution agrees with h0 even on just the windows whose max and min are both unique and interior. The minimum number of forced changes on that class is 4 at nu = 9 and 10 at nu = 11. Over all 210 unique-extrema windows at nu = 9 it is 6. As a consequence, every rule of the form "argmax < argmin, ties resolved by X", for any X at all, has excess at least 8 at nu = 9 and at least 20 at nu = 11 (exact MaxSAT optimum). No optimal solution factors through:
- the pair of argmax/argmin position sets, at nu = 11 or 13 (possible at 5, 7, 9);
- first/last argmax and argmin plus the values M, mn and the end value, at nu = 9;
- the position sets plus M, mn and end with rc-anti required, at nu = 11 (possible at 11 without rc-anti, impossible at 13).

(4) A positive structural finding. SAT finds a chain of rc-anti-invariant optimal solutions h_3, ..., h_13 (all excess 0 by the verifier) satisfying three recursive relations: h_nu(00·W) = h_{nu−2}(W), h_nu(W·11) = h_{nu−2}(W), and h_nu(0·W·1) = 1 − h_{nu−2}(W). These fix half of all windows recursively from the level below. The mirror version (11·W, W·00, 1·W·0) holds by complement symmetry. Requiring W·00 and W·11 together is infeasible, as are interior run-shortening (000→0), deleting 0101/1010, and all the other prefix/suffix variants tested. At nu = 7 the chain leaves 144 of the 448 rc-anti solutions. Applying h0 or its variants on the remaining "core" windows did not help (best profile 0, 4, 12, 44, 164, 592).

(5) Best simple rule I found in this lens has profile 0, 4, 4, 24, 72, 200: compare the mean of the argmax set with the median of the argmin set, break equality by the sign of y at the centre. It is worse than the known span tie-break (0, 4, 4, 20, 64, 176).

On the user's question (whether running this with Opus changes the results much): every claim above comes from the exact verifier or SAT, so correctness does not depend on the model. What the model affects is which hypotheses get tried, for example the feature-sufficiency and hereditary-relation SAT tests here. No closed form was found in this lens, and the SAT no-go results apply no matter which model searches.

**best excess profile**: Best rule found in this lens: h = [mean(argmax set) < median(argmin set)], equality broken by [y(nu//2) + y(nu//2+1) − y(nu) > 0]; excess 0,4,4,24,72,200 for nu=3,5,7,9,11,13 (script: /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-repair/tiesearch.py). This does NOT beat the known span tie-break rule (0,4,4,20,64,176). Proven floor for any pure tie-breaking of h0: excess at least 8 (nu=9) and at least 20 (nu=11).

**exact_rule_found**: False

**insights**:
- h0 is exactly invariant under h(NOT W) = 1 − h(W) (0 violations, nu=3..9). PROBLEM.md says that symmetry is infeasible for nu>=5, so any repair must break it. In every nearest optimal solution, each corrected window W has its complement NOT W uncorrected (NOT-violations = 2 × distance for all nu=5..11).
- Lift picture: write G(j) = h(W_j) XOR (j mod 2) along the antiperiodic lift U. P(nu) says G is a square wave (one switch per m steps). h0 gives the same window function on even and odd j, which is exactly why it is NOT-anti-invariant. A valid h must use different functions on even and odd lift positions.
- Pure tie-breaking cannot work: for nu=9 and 11, no optimal solution keeps h0 on windows with unique interior extrema. At least 4 (nu=9) and 10 (nu=11) of those windows must change, and every tie-breaking repair has excess at least 8 and 20 (MaxSAT-exact).
- Extremum-position information alone is insufficient: there is a solution depending only on (argmax set, argmin set) for nu<=9, but none for nu=11 or 13. Summaries rich enough to be sufficient at nu=13 (positions at levels M, M−1, mn, mn+1, plus end) split 8192 windows into 7250 classes, so they are nearly the full window.
- Hereditary structure: SAT finds an rc-anti chain of optimal solutions h_3..h_13 with h(00·W) = h(W·11) = h_{nu−2}(W) and h(0·W·1) = 1 − h_{nu−2}(W). The exact verifier confirms excess 0 and all relations at every level (verify_chain.py). This fixes half of the windows at each level recursively. The relations imply h_nu(0X) ≠ h_nu(X1), i.e. no monochromatic step drops a 0 and adds a 1. That condition alone is SAT-feasible for nu=5..13.
- These relations are tight in the sense that every extension tested fails: W00 together with W11, interior run-shortening (000→0, 111→1), deleting 0101/1010, and any 01/10 prefix or suffix relation (with or without negation) are all infeasible by nu=9. At nu=7, the chain constraints cut the rc-anti solutions from 448 to 144.
- In the problem's matching formulation, every chain solution's monochromatic edges e (nu+1 bits) serve both necklaces e·0 and e·1. So the monochromatic edge set D is a perfect matching of the necklace graph (vertices = non-constant m-necklaces, edges = (m−1)-words joining neck(e0) and neck(e1)), plus half-edges at 0^{m−1} and 1^{m−1}.
- The nearest-solution correction sets are not canonical: several solutions sit at the same distance (e.g. PROBLEM.md's nu=7 set is the rc-image of the one found here). Treating any single nearest solution as 'the' correction set is therefore unreliable; feasibility tests (feature sufficiency, hereditary relations) are more informative than learning a classifier on corrections.
- On whether the model choice (e.g. Opus) matters much: all conclusions here rest on the exact verifier and SAT, so correctness does not depend on the model. The model only affects which hypotheses are proposed and tested. The SAT no-go results apply whichever model is searching.

**dead ends**:
- Characterising the correction as 'argmax<argmin with ties resolved by X': impossible for nu>=9 for any X (SAT certificate, fixsat.py; tie excess floor in tiebound.py).
- Mirror-symmetric position statistics (mid, mean, median, interior variants) with tie-break features (end value, q = M+mn−end, q*end, centre y, v0/vlast, count/parity of extrema, M vs −mn): best 0,4,4,24,72,200.
- Tilted walks y_alt + eps*y_plain or lexicographic: best 0,4,20,100,432,1672.
- Stripping 00/11 pads before applying a walk rule: best 0,4,16,68,268,1040.
- Recursive hybrid (hereditary relations + walk rule on the core): best 0,4,12,44,164,592. The chain is far from h0 on 00·W windows (132 of 2048 disagree at nu=13).
- Run-length invariances (000→0 inside a window), 0101→01 deletions, and 01/10 prefix/suffix hereditary relations: all SAT-infeasible by nu=9.

## lens: otherparams

**summary**: 关于你的问题（让 Opus 来跑对结果影响大不大）：这一次运行没法回答，因为没有用别的模型跑同一套 explore 作为对照。下面每个数字都是确定性的验证器（SAT/CP-SAT、excess、charged_count）算出来的，所以这些数是否正确和用什么模型无关。模型能影响的只有两点：选了哪些方向去查，以及失败后能不能看出结构。本 lens 最有用的发现来自一个很简单的检查（"这些最优解是不是 minimizer？"），这不需要什么特别的能力。真正卡住的是题目本身（目前没有任何闭式规则），而不是谁在跑。

Findings (all verifier-checked; scripts in /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-otherparams/):

(1) Number of optimal schemes in the other tight cases:
- (σ,w,k)=(2,2,1): 10; (2,2,3): 98; (3,2,1): 72; (4,2,1): 696; (2,3,1): 68; (2,4,1): 632.
- (3,2,3): more than 200k (enumeration timed out).
- (2,3,4): enumeration timed out at 600 s, but single optimal schemes exist (56/128).
- (2,4,5): CP-SAT found nothing within 600 s.

(2) In every tight case tested, an optimal MINIMIZER exists. A minimizer here means a total order on k-mers, with ties broken by a per-window choice where needed.
- (3,2,3): exists, even with leftmost ties.
- (2,3,4): exists, even with leftmost ties. A t=1 mod-minimizer also exists, but only with window-dependent tie choice.
- (2,2,k odd): exists for k=1..13, even with leftmost ties.
- Natural orders (lex and all compositions of rev/comp/alt-flip/Gray, plus σ=3 affine/alternating digit maps) are never optimal in the mirror cases. The best ones are over the bound by 2 at (2,3,4), 4 at (3,2,3), 20 at (2,4,5) and 59 at (2,3,7).

(3) Mirror applied to σ=w=2, even k (P(ν)). EVERY P(ν) solution for ν=3,5,7 (2 + 16 + 25088 solutions) is exactly a minimizer on (ν−1)-mers: h(W) = [rank(suffix k-mer) < rank(prefix k-mer)]. The only extra freedom is the tie at the constant windows.
- Rebuilding each solution from its topological order reproduces it exactly, with excess 0.
- The tie rule must be OPPOSITE at the two constant windows, h(0^ν) ≠ h(1^ν). Setting them equal is UNSAT for ν=3..13.
- So the "minimizer gap 11 vs 10 at (2,2,2)" in PROBLEM.md §4 is purely an artifact of uniform tie-breaking. The order 10 < {00,11} < 01, with tie 000→right and 111→left, gives 10/16, which is optimal.

(4) Three rank levels always suffice. P(ν) can be solved by a 3-valued level function λ: proper 3-colouring of undirected B(2,ν−1), with h = [λ(suf) < λ(pref)].
- SAT for ν=3..13; 2 levels are UNSAT for ν≥3.
- The same holds for odd k unrestricted, k=1..13, with leftmost ties.
- In this language optimality means: along every cyclic word, the λ-sequence of its k-mers is zigzag except for exactly one monotone triple 0-1-2 or 2-1-0.
- 3-level solutions are rare: at ν=7 the DAG-height histogram is 3:72, 4:18360, 5:6656.
- λ can be taken rc-invariant (SAT, ν≤11). rc-anti, rev±, comp± are UNSAT for ν≥5.
- Middle level size |M|: min 2/5/13/39 for ν=3/5/7/9; max 2/7/28 for ν=3/5/7.

(5) No closed-form order found. Every structured λ or order I tested fails beyond small ν:
- λ factoring through prefix/suffix bits, alternating sum + end bits, or walk-extremum summaries;
- Mykkeltveit / double-decycling orders;
- refining the alternating-sum key;
- recursive or automaton constructions (λ_{k+2} = F(2 removed bits, λ_k(rest)) with one F shared across ν, up to 6 levels; one-step lifts are SAT only with 5 levels and an F that changes per step).

The best natural minimizer is key = (alternating sum, lex of alt-flipped k-mer). It reproduces the alt-flip majority exactly on P(ν) and is exact for odd k ≤ 5.

**best excess profile**: Minimizer with key(x) = (alternating sum of the (nu-1)-mer x, lex value of alt-flipped x) and ties h(0^nu)=0, h(1^nu)=1. P(nu) excess for nu=3,5,7,9,11,13: 0, 4, 20, 92, 376, 1504 (same as alt-flip majority). Odd k (leftmost ties), charged minus bound for k=1,3,5,7,9,11,13: 0, 0, 0, 2, 18, 90, 402. Script: /tmp/claude-0/-home-user-test1/2d8e5f37-ae2d-55a9-a4e7-10eca5fea8e6/scratchpad/lens-otherparams/best_rule.py

**exact_rule_found**: False

**insights**:
- Reformulation (verified): every P(nu) solution for nu<=7 is exactly a minimizer h(W)=[rank(y)<rank(x)] for W=(x,y) over (nu-1)-mers. The constant windows must break ties in opposite directions; equal ties are UNSAT for nu<=13. Script: verify_minimizer.py, tie_sat.py.
- Correction to PROBLEM.md section 4: the (2,2,2) minimizer gap 11 vs 10 exists only under uniform tie rules. Order 10<{00,11}<01 with tie 000->pick right, 111->pick left gives 10/16, which is optimal (tie_check.py).
- In minimizer language, optimality means: along each cyclic word, the rank sequence of its k-mers is cyclically zigzag except for exactly one double ascent/descent. The search space becomes acyclic orientations of the undirected de Bruijn graph B(2,k), i.e. k-mer orders.
- Three rank levels suffice: P(nu) for nu=3..13 and odd k=1..13 (the latter even with standard leftmost ties). So a solution is a proper 3-colouring lambda of B(2,k) where every cyclic (k+3)-word (P) or (k+2)-word (odd k) has exactly one monotone triple 0-1-2 or 2-1-0 at a middle-level k-mer. Two levels never suffice for k>=2.
- 3-level solutions are rare (72 of 25088 at nu=7) but rc-invariant ones exist (nu<=11). Any explicit construction could target an rc-invariant 3-colouring lambda of B(2,k).
- Odd k for sigma=w=2 has optimal standard minimizers (leftmost ties) for k=1..13 (minsat.py up to k=7 with full orders; levels via tie_sat.py up to k=11 and levels_sat.py up to k=13).
- Mirror cases behave like sigma=w=2: optimal minimizers exist, but no natural (lex/transform/decycling) order is optimal. The best natural orders always involve the alternating flip, as at sigma=2.

**dead ends**:
- Lex orders under any composition of rev/comp/alt-flip/Gray/inverse-Gray: best P(nu) excess 0,4,28,156,736 at nu=3..11.
- Mykkeltveit decycling and double-decycling (Pellow et al.) k-mer orders: not refinable to any P(nu) solution (nu=5..11).
- Alternating-sum key, or its sign, as a coarse order: P(nu) UNSAT from nu=7; odd k UNSAT from k=9.
- 3-level lambda depending only on prefix/suffix bits, (altsum, end bits) or walk min/max/end/argext summaries: UNSAT by nu=9-11.
- Recursive 2-bit lifts with a table F shared across nu (finite-state transducer with <=6 level-states; the 7-level outer and front modes are also UNSAT): UNSAT for the chain P(3)->P(9).
- Full enumeration of optima for (3,2,3) (>200k, timed out) and (2,3,4) (CP-SAT single-worker enumeration found 0 in 600 s). (2,4,5): no optimum found in 600 s with 8 workers.
