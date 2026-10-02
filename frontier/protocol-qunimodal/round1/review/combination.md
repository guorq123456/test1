# Claim: the closed form "E2_closed_small" follows from already-proved results

Rule (domain: r <= 3, or at most three a_i are >= 2). Let F = sum floor(a_i/r), n2 = #{a_i = 2 mod 3}.
Predict unimodal iff r | some a_i, or [r = 3 and b <= 1 + F + 2 floor(n2/6)], or [r != 3 and b <= 1 + F].

Ingredients (each separately refereed and accepted in round 1):
- (C43) arXiv:2605.12822 Cor. 4.3 (also reproved as Lemma 3 of E4/proof.txt): r | a_i for some i  =>  P unimodal.
- (T1) E4/proof.txt Theorem: b <= 1 + F  =>  P unimodal (all r >= 2, k >= 1).
- (T2) E1/proof.txt and E8/proof_r3.txt: r = 3, no a_i divisible by 3:  P unimodal  <=>  b <= 1 + F + 2 floor(n2/6).
- (T4) E2/proofs/main_proofs.txt Cor. D1 and E5/proofs.txt Thm 3: if r divides no a_i and at most three a_i are >= 2, then P unimodal => b <= 1 + F.
- (T5) E2 Cor. E / E5 Cor. 2: r = 2, all a_i odd: P unimodal => b <= 1 + F.

Derivation.
Step 0. Factors with a_i = 1 equal 1 and contribute floor(1/r) = 0 to F and nothing to n2, so they can be deleted.
Step 1. If r | a_i for some i: unimodal by (C43); the rule predicts True. Assume from now on r divides no a_i.
Step 2. r = 3: the rule is exactly (T2).
Step 3. r = 2: all a_i odd (Step 1). If b <= 1+F, unimodal by (T1). If b > 1+F, not unimodal by (T5). The rule is b <= 1+F.
Step 4. r >= 4 and at most three a_i >= 2: if b <= 1+F, unimodal by (T1); if b > 1+F, not unimodal by (T4). The rule is b <= 1+F.
Step 5. The cases r <= 3 (Steps 2-3) and "at most three nontrivial factors" (Step 4, and for r <= 3 already covered) exhaust the domain. For r = 3 with at most three nontrivial factors, n2 <= 3 so floor(n2/6) = 0 and Steps 2 and 4 agree.
Hence the rule is a theorem on its domain, provided the cited results are correct as stated (check that each cited statement, as written in its file, really has exactly the hypotheses used here).
