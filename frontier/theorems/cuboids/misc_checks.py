"""misc_checks.py -- (a) closed form == type count for n<=10^5; (b) perfect matchings of the
cube graph Q3: there are 9; each is either 4 parallel edges or of the 'mixed' form of Lemma 3."""
import itertools
from structure_count import closed, typecount
assert all(closed(n) == typecount(n) for n in range(1, 100001)); print('(a) ok to 1e5')
V = list(itertools.product((0, 1), repeat=3))
E = [(u, v) for u in V for v in V if u < v and sum(a != b for a, b in zip(u, v)) == 1]
dirn = lambda e: [i for i in range(3) if e[0][i] != e[1][i]][0]
M = [m for m in itertools.combinations(E, 4) if len({x for e in m for x in e}) == 8]
print('perfect matchings:', len(M))
for m in M:
    ds = sorted(dirn(e) for e in m)
    if len(set(ds)) == 1: continue
    used = set(ds); d = ({0, 1, 2} - used).pop()        # the unused direction
    assert len(used) == 2 and ds.count(ds[0]) == 2
    # the two faces x_d = 0 and x_d = 1 each contain two parallel edges, of different directions
    f0 = {dirn(e) for e in m if e[0][d] == 0}; f1 = {dirn(e) for e in m if e[0][d] == 1}
    assert len(f0) == 1 and len(f1) == 1 and f0 != f1
print('(b) ok')
# (c) Berselli-type formula and g.f. for A386884 (offset 1)
bers = lambda n: (n - 4) * (2 * (n - 4) * (n - 1) - (2 * n - 5) * (-1) ** n + 3)
assert all(bers(n) % 16 == 0 and bers(n) // 16 == closed(n) for n in range(1, 100001))
# power series of x^5 (1+x+4x^2) / ((1+x)^3 (1-x)^4) by polynomial long division
N = 400
den = [1]
for f in [[1, 1]] * 3 + [[1, -1]] * 4:
    den = [sum(den[j] * f[k - j] for j in range(len(den)) if 0 <= k - j < len(f)) for k in range(len(den) + len(f) - 1)]
num = [0] * 5 + [1, 1, 4]
c = []
for k in range(N):
    v = (num[k] if k < len(num) else 0) - sum(den[j] * c[k - j] for j in range(1, min(k, len(den) - 1) + 1))
    c.append(v)          # den[0] == 1
assert all(c[n] == closed(n) for n in range(1, N))
print('(c) ok: Berselli-type formula to 1e5, g.f. to n=399')
# (d) order-7 recurrence (signature (1,3,-3,-3,3,1,-1)) for 8 <= n < 2000
a = {n: closed(n) for n in range(1, 2000)}
assert all(a[n] == a[n-1]+3*a[n-2]-3*a[n-3]-3*a[n-4]+3*a[n-5]+a[n-6]-a[n-7] for n in range(8, 2000))
print('(d) ok: recurrence for 8 <= n < 2000')
