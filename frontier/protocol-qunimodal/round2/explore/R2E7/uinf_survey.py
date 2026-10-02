# Survey U_inf(r,res) over all residue multisets (r in RLIST, k in KLIST).
# Checks: (i) S2 shape: U_inf = [1,e*] or [1,e*]\{e*-1} with e* odd;  (ii) e* vs T6-F = 1+floor((S-k+1-2mu)/r);
# (iii) functional dependence of U_inf on candidate statistics.
import sys, itertools
from collections import defaultdict
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
RLIST = list(map(int, sys.argv[1].split(','))); KLIST = list(map(int, sys.argv[2].split(',')))
def mu_of(r, tau):
    m = r - 1
    while m > 0 and tau[m] <= 0: m -= 1
    return m
tot = 0; s2bad = 0; t6eq = 0; t6less = 0; gaps = defaultdict(int)
stat_fns = {
  'r,k,S': lambda r,k,res,tau: (r,k,sum(res)),
  'r,k,S,mu': lambda r,k,res,tau: (r,k,sum(res),mu_of(r,tau)),
  'r,k,S,mu,maxtau': lambda r,k,res,tau: (r,k,sum(res),mu_of(r,tau),max(tau)),
  'r,k,S,tau': lambda r,k,res,tau: (r,k,sum(res),tuple(tau)),
  'r,S-k,tau': lambda r,k,res,tau: (r,sum(res)-k,tuple(tau)),
  'r,k,S,#middle': lambda r,k,res,tau: (r,k,sum(res),sum(1 for s in res if 2<=s<=r-2)),
}
groups = {n: defaultdict(set) for n in stat_fns}
for r in RLIST:
    for k in KLIST:
        for res in itertools.combinations_with_replacement(range(1, r), k):
            res = list(res); tau = tau_vec(r, res); ui = Uinf(r, res)
            tot += 1
            es = max(ui); full = set(range(1, es+1))
            ok = (ui == full) or (es >= 3 and ui == full - {es-1})
            if not ok or es % 2 == 0:
                s2bad += 1
                if s2bad <= 10: print('S2-violation', r, res, sorted(ui))
            mu = mu_of(r, tau); t6 = 1 + (sum(res) - k + 1 - 2*mu)//r
            if es == t6: t6eq += 1
            elif es < t6: t6less += 1
            else: print('EXCEEDS T6 !!', r, res, ui, t6)
            if ui != full: gaps['hole'] += 1
            for n, f in stat_fns.items(): groups[n][f(r,k,res,tau)].add(frozenset(ui))
print(f'multisets={tot} S2-shape violations={s2bad} e*==T6-F: {t6eq}  e*<T6-F: {t6less}  non-interval: {gaps["hole"]}')
for n in stat_fns:
    amb = sum(1 for v in groups[n].values() if len(v) > 1)
    print(f'statistic ({n}): classes={len(groups[n])} ambiguous classes={amb}')
