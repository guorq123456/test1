"""Rule R3 (closed form for r = 3, derived from Rule TAIL via roots of unity):
unimodal <=> 3 | a_i for some i, or b <= 1 + sum_i floor(a_i/3) + 2*floor(n2/6), n2 = #{i : a_i = 2 mod 3}.
Domain: r == 3. Necessity is proven (proof_criterion.txt Cor. 6 + Lemma 8); sufficiency is a conjecture (0 errors in box, n2<=8 there)."""
def domain(r, a):
    return r == 3

def predict(r, a, b):
    if any(x % 3 == 0 for x in a):
        return True
    n2 = sum(1 for x in a if x % 3 == 2)
    return b <= 1 + sum(x // 3 for x in a) + 2 * (n2 // 6)
