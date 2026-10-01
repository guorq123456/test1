# smallest k with excess m*>0, per r ; and per k, counts of m* values
from load import *
from collections import Counter, defaultdict
for r in range(2,7):
    C=defaultdict(Counter)
    for a,mask in load(r):
        B=max(uniset(mask)); Q=sum(x//r for x in a); C[len(a)][B-1-Q]+=1
    print(r,{k:dict(C[k]) for k in sorted(C)})
