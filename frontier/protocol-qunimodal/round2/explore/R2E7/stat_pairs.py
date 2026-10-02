# For candidate statistics, find a pair of residue multisets with equal statistic but different U_inf
# (exhaustive over r in 2..9, k in 2..6).  Prints first pair per statistic and ambiguous-class counts.
import sys, itertools
from collections import defaultdict
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from rule_B4 import Uinf, _tau
def mu_of(tau): return max([t for t in range(len(tau)) if tau[t] > 0], default=0)
stats = {
 '(r,k,S)': lambda r,k,res,tau: (r,k,sum(res)),
 '(r,k,S,mu)': lambda r,k,res,tau: (r,k,sum(res),mu_of(tau)),
 '(r,k,S,mu,T)': lambda r,k,res,tau: (r,k,sum(res),mu_of(tau)),
 '(r,k,tau)': lambda r,k,res,tau: (r,k,tuple(tau)),
 '(r,S-k,tau)': lambda r,k,res,tau: (r,sum(res)-k,tuple(tau)),
 '(r,k,S,tau)': lambda r,k,res,tau: (r,k,sum(res),tuple(tau)),
 '(r,k,S,#middle)': lambda r,k,res,tau: (r,k,sum(res),sum(1 for s in res if 2 <= s <= r-2)),
}
G = {n: defaultdict(dict) for n in stats}; nm = 0
for r in range(2, 10):
    for k in range(2, 7):
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); tau = _tau(r, res); U = frozenset(Uinf(r, res)); nm += 1
            for n, f in stats.items(): G[n][f(r,k,res,tau)].setdefault(U, (r, tuple(res)))
print('multisets', nm)
for n in stats:
    amb = [v for v in G[n].values() if len(v) > 1]
    pair = None
    if amb:
        v = amb[0]; pair = [(sorted(U), res) for U, res in list(v.items())[:2]]
    print(f'{n}: classes={len(G[n])} ambiguous={len(amb)} example={pair}')
