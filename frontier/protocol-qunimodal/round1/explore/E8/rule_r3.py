# Rule (path H5', r=3, no a_i divisible by 3).
# P = [a_1]_q...[a_k]_q [b]_{q^3} is unimodal  <=>  b <= 1 + T + 2*floor(n2/6),
#   T  = sum floor(a_i/3),  n2 = #{i : a_i = 2 mod 3}.
# Equivalently 3(b-1) <= M - (n2 mod 6) with M = sum (a_i - 1).
# Proven for all parameters in this domain: see proof_r3.txt.
def domain(r, a):
    return r == 3 and len(a) >= 1 and all(x % 3 != 0 for x in a)

def predict(r, a, b):
    if r == 3 and any(x % 3 == 0 for x in a):   # outside domain; Cor. 4.3 of arXiv:2605.12822
        return True
    T = sum(x // 3 for x in a)
    n2 = sum(1 for x in a if x % 3 == 2)
    return b <= 1 + T + 2 * (n2 // 6)
