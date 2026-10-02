# For a with E6 not in J: list failing n (d_n < d_{n-rb}, 0<=n<=N/2) at b=T6 and b=T6-1; in terms of
# offsets from center: n - N/2 and the pair index m = n - rb relative to K/2.
import sys, itertools, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from e6_vs_inf import E6
def failing(r, a, b):
    ds = DS(r, a); D = ds.D; N = D + r * (b - 1)
    return [n for n in range(N // 2 + 1) if ds(n) < ds(n - r * b)]
if __name__ == '__main__':
    r, kmax, amax = map(int, sys.argv[1:4])
    vals = [x for x in range(1, amax + 1) if x % r]
    shown = 0
    for k in range(1, kmax + 1):
        for a in itertools.combinations_with_replacement(vals, k):
            a = list(a); rho = sorted(x % r for x in a); e6 = E6(r, rho)
            F = Fval(r, a); T = 1 + F + e6
            if e6 < 2: continue
            fT = failing(r, a, T)
            if not fT: continue
            fT1 = failing(r, a, T - 1)
            D = Dval(a)
            NT = D + r * (T - 1); NT1 = D + r * (T - 2)
            print(a, "D", D, "T6", T, "K(T6)", D + 1 - r * (T + 1), "fail@T6 (n-N/2):", [2 * n - NT for n in fT][:6], "fail@T6-1:", [2 * n - NT1 for n in fT1][:6], "tau", tau(r, rho))
            shown += 1
            if shown > 40: sys.exit()
