import sys, time
sys.path.insert(0, '/tmp/claude-0/deep/morphology/verify1')
from fast import *
BF = '/tmp/claude-0/deep/morphology/verify1/bf/'
def rb(a):
    d = {}
    for line in open(BF + 'b%d.txt' % a):
        line = line.strip()
        if not line or line.startswith('#'): continue
        n, v = line.split()[:2]
        d[int(n)] = int(v)
    return d
def antidiag(idx):  # 1-based index -> (n,k), order T(1,d-1),T(2,d-2),...
    d = 2
    while idx > d-1:
        idx -= d-1; d += 1
    n = idx; k = d - n
    return n, k
stats = {}
def chk(name, ok):
    stats.setdefault(name, [0, 0])
    stats[name][0] += 1
    if not ok: stats[name][1] += 1
t0 = time.time()
cacheA, cacheB, cacheC, cacheD = {}, {}, {}, {}
def get(cache, fn, k, L):
    if k not in cache or len(cache[k]) <= L:
        cache[k] = fn(max(L, 2*len(cache.get(k, [])), 10), k)
    return cache[k][L]
A = lambda N, k: get(cacheA, A_seq, k, N)
B = lambda M, k: get(cacheB, B_seq, k, M)
C = lambda N, k: get(cacheC, C_seq, k, N)
D = lambda M, k: get(cacheD, D_seq, k, M)
# columns
for k, a in zip(range(2, 8), [200880, 200881, 200882, 200883, 200884, 200885]):
    for n, v in rb(a).items():
        chk('A2008%d=A(n+2,%d)' % (a % 100, k), A(n+2, k) == v)
        chk('Thm1 A(n+2)=B(n+3) on col', B(n+3, k) == v)
for k, a in zip(range(2, 8), [202882, 203094, 203184, 203050, 203059, 202909]):
    for n, v in rb(a).items():
        chk('A%d=B(n,%d)' % (a, k), B(n, k) == v)
for k, a in zip(range(2, 8), [200865, 200866, 200867, 200868, 200869, 200870]):
    for n, v in rb(a).items():
        chk('A%d=C(n+2,%d)' % (a, k), C(n+2, k) == v)
        if k <= 5: chk('Thm2 col: D(n+3,%d)' % k, D(n+3, k) == v)
for k, a in [(2, 217450), (3, 218051)]:
    for n, v in rb(a).items():
        chk('A%d=D(n,%d)' % (a, k), D(n, k) == v)
# rows
for r, a in zip(range(2, 8), [200887, 200888, 200889, 200890, 200891, 200892]):
    for m, v in rb(a).items():
        chk('A%d row' % a, A(r+2, m) == v)
for r, a in zip(range(2, 8), [200872, 200873, 200874, 200875, 200876, 200877]):
    for m, v in rb(a).items():
        chk('A%d row' % a, C(r+2, m) == v)
print('cols/rows done', time.time()-t0, flush=True)
# full tables
for idx, v in rb(200886).items():
    n, k = antidiag(idx)
    chk('A200886 = A(n+2,k)', A(n+2, k) == v)
    chk('A200886 = B(n+3,k)', B(n+3, k) == v)
print('A200886 done', time.time()-t0, flush=True)
for idx, v in rb(200871).items():
    n, k = antidiag(idx)
    chk('A200871 = C(n+2,k)', C(n+2, k) == v)
    if k <= 22:
        chk('A200871 = D(n+3,k) (k<=22)', D(n+3, k) == v)
print('A200871 done', time.time()-t0, flush=True)
# window-2 min filter tables
i2 = {2: img2_seq(80, 2), 3: img2_seq(80, 3)}
for K, a in [(2, 217883), (3, 217954)]:
    for idx, v in rb(a).items():
        n, w = antidiag(idx)
        if w == 2:
            chk('A%d col2 = img(eps-) [subset constr]' % a, i2[K][n] == v)
            chk('A%d col2 = B(n+1,%d)' % (a, K), B(n+1, K) == v)
# 2D tables
for K, a in [(2, 202889), (3, 203101), (4, 203191), (5, 203057), (6, 203066), (7, 202916)]:
    for idx, v in rb(a).items():
        n, m = antidiag(idx)
        if m == 1: chk('A%d col1 = B(n,%d)' % (a, K), B(n, K) == v)
        if n == 1: chk('A%d row1 = B(m,%d) (symmetry)' % (a, K), B(m, K) == v)
for K, a, nb in [(1, 217637, 'hv'), (1, 218084, 'hva'), (1, 217982, 'hvda'), (2, 217457, 'hv'), (2, 217645, 'hva'), (2, 217547, 'hvda'), (3, 218181, 'hv'), (3, 218651, 'hva'), (3, 218056, 'hvda')]:
    for idx, v in rb(a).items():
        n, m = antidiag(idx)
        if m == 1: chk('A%d col1 = D(n,%d)' % (a, K), D(n, K) == v)
        if m == 2 and nb == 'hvda': chk('A%d col2 = D(n,%d)' % (a, K), D(n, K) == v)
print('all done', time.time()-t0)
tot = 0; bad = 0
for kk, (c, b) in stats.items():
    print('%-45s %6d checks %d fail' % (kk, c, b)); tot += c; bad += b
print('TOTAL', tot, 'FAIL', bad)
