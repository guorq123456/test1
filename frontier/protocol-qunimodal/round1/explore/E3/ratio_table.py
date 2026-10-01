# Relation between E (set of d>=1 with P unimodal; coarse residue-class table) and
# rho = max/min of the residue-class sums of C(q)=prod_{a_i>1, r∤a_i}[a_i mod r]_q folded mod q^r-1.
import json
from fractions import Fraction
from collections import defaultdict
E=json.load(open('table_coarse.json'))
from features2 import _fold
from load import load
recs=load()
seen=set(); rows=defaultdict(list)
for r,a,m in recs:
    a2=tuple(x for x in a if x>1)
    if any(x%r==0 for x in a2): continue
    R=tuple(sorted(x%r for x in a2))
    if (r,R) in seen: continue
    seen.add((r,R))
    f=_fold(r,list(a2)); rho=Fraction(max(f),min(f)) if min(f) else None
    e=tuple(E.get(f"{r}|{','.join(map(str,R))}",[]))
    rows[r].append((rho,e,R,f))
for r in range(2,7):
    L=rows[r]
    byE=defaultdict(list)
    for rho,e,R,f in L: byE[e].append(rho)
    print(f'r={r}:')
    for e,v in sorted(byE.items()):
        v2=[x for x in v if x is not None]
        rng=f'[{float(min(v2)):.6f}, {float(max(v2)):.6f}]' if v2 else 'n/a'
        print(f'   E={e}: n={len(v)}, rho range {rng}, #rho=inf (some class sum 0)={sum(1 for x in v if x is None)}')
