# Exact rational verification of the strict two-sided inequalities
#   H(e_n - 1) - H(e_{n-1}) < H(e_{n-1}) - H(e_{n-2}) < H(e_n) - H(e_{n-1})
# for the first few n (e = A087125: 0,5,54,539,5340,52865,523314,...).
# The case n = 2 (triple 0,5,54) is the only one needed by the proof; the others are extra checks.
import gmpy2, sys
from gmpy2 import mpz, mpq
def hsum(a, b):
    """sum_{j=a}^{b-1} 1/j as (p, q) via binary splitting (q = prod j)."""
    if b - a == 1: return mpz(1), mpz(a)
    m = (a + b) // 2
    p1, q1 = hsum(a, m); p2, q2 = hsum(m, b)
    return p1 * q2 + p2 * q1, q1 * q2
def H(k):
    if k == 0: return mpq(0)
    p, q = hsum(1, k + 1); return mpq(p, q)
e = [0, 5]
while len(e) < 8: e.append(10 * e[-1] - e[-2] + 4)
NMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 5
cache = {}
def Hc(k):
    if k not in cache: cache[k] = H(k)
    return cache[k]
print("H(5) =", Hc(5), "  2H(5) - H(0) =", 2 * Hc(5))
print("H(53) =", float(Hc(53)), " H(54) =", float(Hc(54)), " 137/30 =", 137 / 30)
for n in range(2, NMAX + 1):
    u, v, w = e[n - 2], e[n - 1], e[n]
    T = 2 * Hc(v) - Hc(u)
    hw = Hc(w); hw1 = hw - mpq(1, w)
    ok = hw1 < T < hw
    print(f"n={n}: triple ({u},{v},{w}):  H({w}-1) < 2H({v})-H({u}) < H({w}) : {ok}   "
          f"[T-H(w-1) = {float(T-hw1):.6e}, H(w)-T = {float(hw-T):.6e}]")
    assert ok
print("all exact checks passed")
