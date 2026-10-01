# tabulate B* relative to simple quantities
from load import *
from collections import Counter
for r in range(2,7):
    D=load(r); C1=Counter(); C2=Counter(); conj=Counter()
    for a,m in D:
        S=uniset(m); B=max(S); Dg=sum(x-1 for x in a)
        C1[B-(Dg//r)]+=1
        cb=1+sum(x//r for x in a)
        conj[(B>=cb, B-cb if B>=cb else None)]+=1
    print("r",r,"B*-floor(D/r):",sorted(C1.items()))
    print("   B*-(1+sum floor):",sorted(conj.items(),key=str))
