# Verifies, on random fit-box instances (b>=2), the lemmas used in proofs.md:
#  WL : window lemma  -- unimodal <=> s_m := g_m - g_{Delta-m} - tau_m >= 0 for all m in (Delta/2, Delta/2+r]
#  GW : g_n <= w_n for all n (k = number of parts, 1-parts kept)
#  EPS: eps_n = B(n) - c_n >= 0 and nondecreasing on [0, Delta/2 + r]
#  NEC: unimodal => R(Delta) computed with k' = #parts>=2 (needs k'>=2)
# Usage: python3 verify_lemmas.py SEED NTRIALS
import sys, random
from math import comb
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
seed, NT = map(int, sys.argv[1:3]); rng = random.Random(seed)
def polyA(a):
    c = [1]
    for A in a:
        n = [0]*(len(c)+A-1)
        for i, v in enumerate(c):
            for j in range(A): n[i+j] += v
        c = n
    return c
cnt = dict(WL=0, GW=0, EPS=0, NEC=0); bad = dict(WL=0, GW=0, EPS=0, NEC=0)
for t in range(NT):
    r = rng.randint(2, 30); k = rng.randint(2, 10)
    a = sorted(rng.randint(1, rng.choice([r, 2*r, 60])) for _ in range(k))
    if not in_box(r, a): continue
    D = sum(x-1 for x in a); Acoef = polyA(a)
    c = [Acoef[j] - (Acoef[j-1] if j >= 1 else 0) for j in range(D+1)] + [-Acoef[D]]   # A(q)(1-q)
    M = D + 1 + 3*r
    g = [0]*(M+1)
    for n in range(M+1):
        g[n] = (c[n] if n <= D+1 else 0) + (g[n-r] if n >= r else 0)
    tau = [sum(c[j] for j in range(D+2) if j % r == t) for t in range(r)]
    w = wcoef(k, r, M)
    B = lambda n: comb(n+k-2, k-2) if n >= 0 else 0
    cnt['GW'] += 1
    if any(g[n] > w[n] for n in range(M+1)): bad['GW'] += 1
    eps = [B(n) - (c[n] if n <= D+1 else 0) for n in range(M+1)]
    F = sum(x//r for x in a)
    bs = list(range(2, F + D//r + 3))
    gt = gt_profile(r, a, bs)
    kp = sum(1 for x in a if x >= 2); resp = [x % r for x in a if x >= 2]
    taup = tau_vec(r, resp) if kp >= 1 else None
    wp = wcoef(kp, r, M) if kp >= 2 else None
    G = lambda n: g[n] if n >= 0 else 0
    for b, u in zip(bs, gt):
        Delta = D + 1 - r*(b+1); lo = Delta//2 + 1
        ok = all(G(m) - G(Delta-m) >= tau[m % r] for m in range(lo, lo+r))
        cnt['WL'] += 1
        if ok != u: bad['WL'] += 1; print('WL fail', r, a, b)
        top = lo + r - 1
        cnt['EPS'] += 1
        if any(eps[n] < 0 for n in range(0, max(top,0)+1)) or any(eps[n] < eps[n-1] for n in range(1, max(top,0)+1)): bad['EPS'] += 1; print('EPS fail', r, a, b)
        if kp >= 2 and all(x % r for x in a):
            cnt['NEC'] += 1
            if u and not R(r, kp, taup, Delta, wp): bad['NEC'] += 1; print('NEC fail', r, a, b)
print(f'seed={seed} checks={cnt} failures={bad}')
