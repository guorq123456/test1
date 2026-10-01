# List residue multisets R (nontrivial factors, no zero residue) by their unimodal-excess set E (d>=1), per r.
from load import load
from collections import defaultdict
recs=load()
Ex=defaultdict(set); kmax=defaultdict(int); allR=set()
for r,a,m in recs:
    a2=tuple(x for x in a if x>1); res=tuple(sorted(x%r for x in a2)); F=sum(x//r for x in a2)
    if 0 in res: continue
    allR.add((r,res))
    for b in range(1,61):
        d=b-1-F
        if d>=1 and (m>>(b-1))&1: Ex[(r,res)].add(d)
for r in range(2,7):
    by=defaultdict(list)
    for (rr,res) in sorted(allR):
        if rr==r: by[tuple(sorted(Ex[(rr,res)]))].append(res)
    for E,L in by.items():
        if E==(): print(f'r={r} E=empty: {len(L)} multisets'); continue
        print(f'r={r} E={E}: {len(L)} multisets')
        for res in L: print('     ',res, ' sum=',sum(res),' k=',len(res))
