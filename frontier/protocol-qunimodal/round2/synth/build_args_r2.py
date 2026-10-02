import json, sys
P='/tmp/claude-0/qu'
r1 = json.load(open(P+'/synth/args_r1.json'))
problem = r1['problem'].replace("Question:", "U = {b : P unimodal}, F = sum floor(a_i/r), D = sum(a_i-1). Question:")
E2=P+'/explore2'
# numeric review status filled from review results (argv[1] = json {id: 'PASS (...)' or 'REJECT (...)'})
st = json.loads(open(sys.argv[1]).read()) if len(sys.argv) > 1 else {}
r1_synth = json.load(open(P+'/synth/r1_result.json'))['synthesis']
passed = r1['passed'] + [
 {"id":"S1-r1","statement":"Round-1 synthesis results (synthesis proof ACCEPTED by referee): E6 = floor((D+1-2mu)/r) - F is even and >= 0 (Lemma 7); {1..1+F} c U c {1..1+F+E6}; flat domain (at most two middle residues, residue in [2,r-2]): U = {1..1+F+E6} exactly (Thm E); peeling: U(a + r e_i) contains {1} and 1+U(a) (Thm B); large-part regime: U = [1,F] u (F+U_inf), U_inf depends only on r and the residue vector (B4).","proof_file":P+"/synth/r1/proof.txt","basis":"已证明 (referee ACCEPT)"},
 {"id":"T9","statement":"(R2E1) Thread criterion: P_b unimodal iff for every residue thread V_b>=0 and V_{b-1}+d_b>=0, with a parity split (Theorem 12). Consequences: S2(i): if b in U and b == F (mod 2) then b+1 in U; max U == 1+F (mod 2) when r divides no a_i; step-2 closure: b in U, b>=3 => b-2 in U (no hypothesis on r|a_i); U finite iff r divides no a_i (Thm 15); conditional Thm 17: if at the first off-parity failure the inequality L' (d_j - d_{j+1} >= d_{j+3}) holds then B* <= B_off + 3, i.e. S2.","proof_file":E2+"/R2E1/proof_S2_partial.txt","basis":"已证明 (referee ACCEPT; z3 for bounded induction steps; ~300k cases 0 mismatch)"},
 {"id":"T10","statement":"(R2E2) Theorem R: S2 follows from three finite residue-level conditions TP_rho, E_rho, O_rho on the small-part instance rho (parts = residues < r); part sizes never matter (lifting). Lemma 10: b > 1+floor((2y*-D-1)/r) => not unimodal, y* = least y with d_y<0. The certificate holds for all 3,154,273 residue multisets swept (r=2..30, k up to 40 for r<=5 down to 4 for r=28..30, plus equal residues k<=60); referee reproduced the count.","proof_file":E2+"/R2E2/proof_S2_reduction.txt","basis":"已证明 (reduction, referee ACCEPT) + 有限范围计算 (certificate sweep, reproduced by referee)"},
 {"id":"T11","statement":"(R2E3) Structure theorem: if r divides no a_i, U = [1,sigma] u {sigma+2, sigma+4, ..., tau*-2} with sigma == tau* == 1+F (mod 2), tau* >= sigma+2; hence S2 <=> tau* <= sigma+4. Lemma 7: residue-class sums of prod[a_i]_q are cyclically unimodal peaked at S/2 (statement to be read on the coset S/2+Z).","proof_file":E2+"/R2E3/proof_S2_partial.txt","basis":"已证明 (referee ACCEPT)"},
 {"id":"T12","statement":"(R2E5) Window Lemma: P unimodal iff tau_m + g_{K-m} - g_m >= 0 for the r integers m with K/2-r <= m < K/2. Sandwich theorem for all-equal a=nr+s, middle s: E(0) c E(1) c ... and E(n)=E_inf once 2(nr+s) > k(s-1)+1-r. With finite certification: U([nr+s]^k) = [1,kn+1] u (kn+1+E_inf) for all n>=1, 4<=r<=30, 3<=k<=60. Parity structure of E_inf (two chains: odd e <= E_odd, even e <= E_even, E_odd < E_even) proved for all r>=4, middle s, k>=3.","proof_file":E2+"/R2E5/proofs.txt","basis":"已证明 (referee ACCEPT; finite part reproduced)"},
 {"id":"T13","statement":"(R2E6) Sandwich window for E = B*-1-F from M = max tau (Thm 1/Cor 1, needs a_min >= 2n_lo+2r); explicit bounds on M via L_k = max_j sum_i ln|sin(pi j s_i/r)/sin(pi j/r)| (Thm 2); growth order (Thm 3): fixed r and residue proportions with positive middle mass, k->infinity, a_min large: |E - (c k - ln k/(r lambda))| <= C2 with c = (sigma1 - 2 theta*)/r, 0 < c < sigma1/r (Lemma 6). So the excess is linear in k.","proof_file":E2+"/R2E6/proof_excess_asymptotics.txt","basis":"已证明 (referee ACCEPT)"},
 {"id":"T14","statement":"(R2E7) Explicit L0 = max(1, floor((S-k+3-r)/2)) (S = sum(a_i-1)) for the large-part regime; universal necessity U(a) c [1,F+1] u (F+U_inf); two-chain structure of U_inf; U_inf c [1, T6-F].","proof_file":E2+"/R2E7/proofs.txt","basis":"已证明 (referee ACCEPT)"},
 {"id":"T15","statement":"(R2E8) r>=4, r divides no a_i, exactly three a_i with middle residue, nm = #{a_i == -1 mod r}: if r<=30 and nm<=37 then U = [1,B*] with B* = T6 - 2*[tau_s<=-2 and s>=2mu], s=(D+1) mod r, T6 = 1+floor((D+1-2mu)/r).","proof_file":E2+"/R2E8/proof_three_middle.txt","basis":"已证明 (computer-assisted, referee ACCEPT, finite part recomputed independently)"},
 {"id":"N2_S2","statement":"S2 holds on all 100,488 multisets r in [4,8], 1<=k<=6, a_i in [2,2r+2], r dividing no a_i; B_main-B_off = 1 in 100,402 and 3 in 86. Reviewer A also found 0 violations on ~553k new instances (k to 11, a_i to 4r, r 9..14).","basis":"有限范围计算 — "+st.get('N2_S2','review status pending')},
 {"id":"N2_allequal","statement":"All-equal middle-residue rule (R2E5): 0 errors on 4,824,541 (instance,b) pairs (r=4..8 all n, r=9..30 n in {0,1}, k=3..60).","basis":"有限范围计算 — "+st.get('N2_allequal','review status pending')},
 {"id":"N2_three","statement":"Three-middle rule (R2E8): 0 errors in fit range r in [4,30], k<=40, a_i<=100.","basis":"有限范围计算 — "+st.get('N2_three','review status pending')},
]
conjectures = """Current conjectures (not proved):
- S2 (round-1 synthesis, open): if r divides no a_i, U = {1..B*} or {1..B*} minus {B*-1}, B* == 1+F (mod 2). After round 2: S2(i), step-2 closure and the parity of max U are PROVED (T9, T11). What remains is exactly the odd shift b -> b-3 (equivalently B_off >= B*-3, equivalently tau* <= sigma+4 in T11, equivalently the residue certificate TP/E/O of T10 for every rho).
- Three-middle closed form T15 beyond r<=30 or nm<=37 (0 errors on hidden holdout H4 incl. k up to 100).
- Cyclic unimodality of prod[rho_i] mod (q^r-1) as a route to TP/E/O (0 failures in test_cyclic_unimodal.py, unproved)."""
holdout = r1['holdout_summary'] + """
Round-3 holdout H3 (hidden; 43,239 instances, larger r and k): round-1 synthesis rule 0/43,239; exact criteria (E2_exact, E5_exact) 0; r=3 rule 0; E4 (one-sided, FN only) and E2_residue (FP only) consistent with their one-sided claims.
Round-4 holdout H4 (hidden from round-2 explorers; 1,270 (r,a) tuples, 51,858 (instance,b) pairs; strata: r in {2,3} with k 91-140; r 4-12 with k 91-140, a_i<=250; r in {61..120} with k 10-40, a_i<=400; three middle residues r 7-24, k 41-100; all-equal middle residue r 4-14, k 91-150; many small parts r 13-30; residues near r/2, k 91-140). b window [B0-5, T6+2] plus random b.
- Round-1 synthesis rule: 0/51,858. R2E1 thread criterion: 0/51,858. R2E2 residue-certificate rule (s3star): 0/51,858.
- R2E5 all-equal rule: 0/10,293 (its domain). R2E8 three-middle rule: 0/7,897 (domain; includes nm far above 37).
- R2E7 B4 and chains rules: 0/943 each (their domain).
- R2E6 asymptotic fits C11: 142 errors (120 FP, 22 FN) / 49,114; C3: 172 (120 FP, 52 FN) -> 拟合表.
- S2 checked on all 1,270 H4 tuples (full U computed): 0 violations."""
failures = r1['failures'] + "\n\nROUND 2 failure records (verbatim from explorers, file " + E2 + "/failure_only.txt):\n" + open(E2+'/failure_only.txt').read()
args = {"problem": problem, "passed": passed,
        "holdout_summary": conjectures + "\n\n" + holdout,
        "failures": failures,
        "lit_items": r1['lit_items'] + "\nRound-2 literature (step 0 r2 + recheck, verdict CORRECTED): /tmp/claude-0/qu/lit2/step0_r2.json and /tmp/claude-0/qu/review/r2/rX_result.json (review id 'literature'). New links: ProveIt data/thresholds.csv (b=2, a_i=2, all r: critical n = r^2-3) and r3_binomial_thresholds.csv; Handelman arXiv:1102.2961 Thm 2.1 (order k^4 for a different property E). Round-2 claims for r>=4: not found in searched sources (b=2 slice of all-equal family is literature).",
        "round": 2}
json.dump(args, open(P+'/synth/args_r2.json','w'), ensure_ascii=False)
print(len(json.dumps(args)))
