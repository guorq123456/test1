# excess e (B*-1-sum floor)/2 by residue count vector, r given
from load import *
from collections import defaultdict
import sys
rr=int(sys.argv[1])
D=load(rr); tab=defaultdict(set)
for a,m in D:
    S=uniset(m); B=max(S); cb=1+sum(x//rr for x in a)
    cnt=tuple(sum(1 for x in a if x%rr==s) for s in range(1,rr))
    tab[cnt].add((B-cb)/2)
nz=[(c,sorted(v)) for c,v in sorted(tab.items()) if v!={0}]
print(len(tab),"classes;",len(nz),"with nonzero excess")
for c,v in nz: print(c,v, "sum(s-1)=",sum(n*s for n,s in zip(c,range(0,rr-1))), "k=",sum(c))
