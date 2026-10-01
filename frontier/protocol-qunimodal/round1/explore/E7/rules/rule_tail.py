"""Rule TAIL: unimodal <=> r | a_i for some i, or r(b-1) <= D + 1 - 2 j*,
where p = prod [a_i]_q, D = deg p, S_t = sum_{j = t mod r} p_j (t=0..r-1) are the residue-class sums,
and j* = max{ j in {0..r-1} : S_j > S_{(j-1) mod r} }.
The inequality r(b-1) <= D+1-2j* is a PROVEN necessary condition (proof_criterion.txt, Cor. 6);
the rule asserts it is also sufficient. Domain claimed: r <= 3 (0 errors in the box there).
For r = 3 it simplifies to: b <= 1 + sum floor(a_i/3) + 2*floor(n2/6), n2 = #{i : a_i = 2 mod 3}.
"""
def _p(a):
    c = [1]
    for A in a:
        n = [0] * (len(c) + A - 1)
        for i, v in enumerate(c):
            for j in range(A):
                n[i + j] += v
        c = n
    return c

def _g(p, r, n):
    g = [0] * (n + 1)
    for i in range(n + 1):
        v = (p[i] if i < len(p) else 0) - (p[i - 1] if 1 <= i <= len(p) else 0)
        g[i] = v + (g[i - r] if i >= r else 0)
    return g


def domain(r, a):
    return r <= 3

def predict(r, a, b):
    if any(x % r == 0 for x in a):
        return True
    p = _p(a)
    D = len(p) - 1
    S = [sum(p[t::r]) for t in range(r)]
    js = max(j for j in range(r) if S[j] > S[(j - 1) % r])
    return r * (b - 1) <= D + 1 - 2 * js
