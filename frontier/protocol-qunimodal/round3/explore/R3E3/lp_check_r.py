# Empirical: does L' hold at n*(C) for every pair, for r=5,6 ? (fit box only)
import random, sys
from pairs import pair_data
from lib4 import in_box
r=int(sys.argv[1]); random.seed(int(sys.argv[2])); N=int(sys.argv[3])
fails=0; tot=0; worst=[]
for it in range(N):
    k=random.randint(2,45); mode=random.random()
    pool=[x for x in range(2,3*r) if x%r] if mode<0.5 else [x for x in range(2,80) if x%r]
    if mode>0.8: pool=[x for x in range(2,3*r) if 2<=x%r<=r-2]
    a=sorted(random.choice(pool) for _ in range(k))
    if not in_box(r,a): continue
    tot+=1
    for p in pair_data(r,a):
        m=p['nstar']
        if m is None: continue
        y=p['y']; l=y(m+1)-y(m+2); rr=y(m+4)
        if l<rr: fails+=1; print("FAIL",a,p['C'],m,l,rr)
        if rr>0: worst.append((l/rr,a,p['C']))
worst.sort(key=lambda z:z[0])
print(r,tot,"Lprime fails",fails,"min ratio",worst[:3])
