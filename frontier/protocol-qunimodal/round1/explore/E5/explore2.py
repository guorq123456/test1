# check sufficiency (all b<=1+sum floor unimodal) and tabulate excess e vs residue multiset
from load import *
from collections import defaultdict
import sys
rr=int(sys.argv[1])
D=load(rr); tab=defaultdict(set); suff_fail=0
for a,m in D:
    S=uniset(m); B=max(S); cb=1+sum(x//rr for x in a)
    if any(b not in S for b in range(1,cb+1)): suff_fail+=1
    res=tuple(sorted(x%rr for x in a)); 
    tab[res].add((B-cb))
print("sufficiency failures",suff_fail)
amb=0
for res in sorted(tab,key=lambda t:(len(t),t)):
    if len(tab[res])>1: amb+=1
    if len(res)<=int(sys.argv[2]): print(res, sorted(tab[res]))
print("residue classes",len(tab),"ambiguous",amb)
