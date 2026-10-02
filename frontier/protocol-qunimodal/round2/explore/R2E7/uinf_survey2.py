# Broader survey of U_inf(r,res) over all residue multisets with r in RLIST, k in KLIST.
# Reports: S2 shape (U_inf=[1,e*] or [1,e*]\{e*-1}, e* odd), e* vs T6-F, gap parity, hole count,
# and functional dependence on candidate statistics.  Usage: python3 uinf_survey2.py RLIST KLIST
import sys, itertools
from collections import defaultdict, Counter
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
RLIST = list(map(int, sys.argv[1].split(','))); KLIST = list(map(int, sys.argv[2].split(',')))
def mu_of(tau):
    m = len(tau) - 1
    while m > 0 and tau[m] <= 0: m -= 1
    return m
tot = s2bad = 0; gapC = Counter(); holes = []
stats = {
 'r,k,S,mu': lambda r,k,res,tau,mu: (r,k,sum(res),mu),
 'r,k,S,mu,tau0': lambda r,k,res,tau,mu: (r,k,sum(res),mu,tau[0]),
 'r,k,S,mu,tau[0..mu]': lambda r,k,res,tau,mu: (r,k,sum(res),mu,tuple(tau[:mu+1])),
 'r,k,S,tau': lambda r,k,res,tau,mu: (r,k,sum(res),tuple(tau)),
 'r,S-k,tau': lambda r,k,res,tau,mu: (r,sum(res)-k,tuple(tau)),
 'r,k,tau': lambda r,k,res,tau,mu: (r,k,tuple(tau)),
}
G = {n: defaultdict(set) for n in stats}
for r in RLIST:
    for k in KLIST:
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); tau = tau_vec(r, res); ui = Uinf(r, res); mu = mu_of(tau)
            tot += 1; es = max(ui); full = set(range(1, es+1))
            ok = (ui == full) or (es >= 3 and ui == full - {es-1})
            if not ok or es % 2 == 0:
                s2bad += 1; print('S2-violation', r, res, sorted(ui))
            t6 = 1 + (sum(res) - k + 1 - 2*mu)//r
            assert es <= t6
            gapC[t6 - es] += 1
            if ui != full: holes.append((r, tuple(res), es))
            for n, f in stats.items(): G[n][f(r,k,res,tau,mu)].add(frozenset(ui))
print(f'r={RLIST} k={KLIST} multisets={tot} S2 violations={s2bad} histogram of (T6-F)-e*: {dict(sorted(gapC.items()))} holes={len(holes)}')
for h in holes[:12]: print('  hole', h)
for n in stats:
    print(f'  stat ({n}): classes={len(G[n])} ambiguous={sum(1 for v in G[n].values() if len(v)>1)}')
