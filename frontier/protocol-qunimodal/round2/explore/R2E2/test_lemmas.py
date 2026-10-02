# Numerical sanity checks of every lemma used in proof_S2_reduction.txt (fit box only).
#  L3  : unimodal(P(a,b))  <=>  Phi(K)   [K = D+1-r(b+1); Phi(K): for x>=1-rb, 2x<K : Q_{K-x} >= d_x]
#  LCW : if Phi(K+r) holds (b-1 unimodal, b>=2) then  Phi(K) <=> ND(K)
#  LM  : ND_a(K) => ND_{a+r e_i}(K)  for K <= D(a)+1   (lifting monotonicity, pairwise)
#  TU  : unimodal => K >= 2 mu*   (mu* = max{u: Q_u<0} = D+1-r-y*)
#  TP  : every y with d_y<0 has floor((2y-D-1)/r) == F mod 2
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS, unimodal_d, Fval
from limit import tau

def Phi(ds, tt, r, K, b):
    for x in range(1 - r * b, (K + 1) // 2 + 1):
        if 2 * x >= K: break
        if ds(K - x) - tt[(K - x) % r] < ds(x): return False
    return True
def ND(ds, tt, r, K):
    for x in range((K - r) // 2 - 1, (K + 1) // 2 + 1):
        if K - r <= 2 * x < K and ds(K - x) - tt[(K - x) % r] < ds(x): return False
    return True
random.seed(99)
cnt = dict(L3=0, LCW=0, LM=0, TU=0, TP=0); bad = dict(L3=0, LCW=0, LM=0, TU=0, TP=0)
for it in range(3000):
    r = random.randint(2, 12); k = random.randint(1, 8)
    a = sorted(random.randint(1, 3 * r) for _ in range(k))
    a = [x for x in a if x % r] or [1]
    ds = DS(r, a); tt = tau(r, a); D = ds.D; F = Fval(r, a)
    y = 0
    while ds(y) >= 0: y += 1
    ms = D + 1 - r - y
    for yy in range(0, D + r + 1):
        if ds(yy) < 0:
            cnt['TP'] += 1
            if ((2 * yy - D - 1) // r - F) % 2: bad['TP'] += 1
    prev = None
    for b in range(1, (D + 1) // r + 4):
        K = D + 1 - r * (b + 1)
        u = unimodal_d(ds, b); ph = Phi(ds, tt, r, K, b)
        cnt['L3'] += 1; bad['L3'] += (u != ph)
        if u: cnt['TU'] += 1; bad['TU'] += (K < 2 * ms)
        if b >= 2 and prev:
            cnt['LCW'] += 1; bad['LCW'] += (ph != ND(ds, tt, r, K))
        prev = u
    # lifting monotonicity of ND
    i = random.randrange(len(a)); a2 = sorted(a[:i] + [a[i] + r] + a[i + 1:])
    ds2 = DS(r, a2)
    for K in range(-3 * r, D + 2):
        if ND(ds, tt, r, K):
            cnt['LM'] += 1; bad['LM'] += (not ND(ds2, tt, r, K))
print("checks:", cnt)
print("violations:", bad)
