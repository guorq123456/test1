"""Rule E2_closed_small: closed form on the domain r<=3 or k_eff<=3 (k_eff = #{i: a_i>=2}).
 - r | some a_i: unimodal.
 - r = 3: unimodal iff b <= 1 + S + 2*floor(n2/6),  n2 = #{i : a_i = 2 mod 3}.
 - otherwise (r = 2, or k_eff <= 3): unimodal iff b <= 1 + S,  S = sum floor(a_i/r).
PROVED (proofs/main_proofs.txt): 'only if' in all cases (Thm B, Cor D1, Cor E, Cor R3);
'if' whenever r(b+1) >= D+1 (Cor S1(a), Cor R3(c)).  'if' for r(b+1) < D+1 is conjectural (box-verified).
"""
def domain(r, a):
    return r <= 3 or sum(1 for x in a if x >= 2) <= 3
def predict(r, a, b):
    if any(x % r == 0 for x in a): return True
    S = sum(x // r for x in a)
    if r == 3:
        n2 = sum(1 for x in a if x % 3 == 2)
        return b <= 1 + S + 2 * (n2 // 6)
    return b <= 1 + S
