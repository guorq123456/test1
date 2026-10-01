# classify violating pairs (v, M-v) at every non-unimodal b <= B*+3 by (floor(v/r), floor((M-v)/r)) 
from load import *
from scond import Sfun
from collections import Counter
import sys
for r in range(2,7):
    C=Counter(); Cfirst=Counter()
    for a,mask in load(r):
        S_=uniset(mask); B=max(S_)
        S,Dg=Sfun(a,r)
        for b in range(2,B+4):
            if b in S_: continue
            M=Dg+1-r*(b-1)
            bad=[v for v in range(-r*(b-1)-r-2,(M+1)//2+1) if 2*v<M and S(v)<S(M-v)]
            types=frozenset((v//r,(M-v)//r) for v in bad)
            C.update(types)
            # minimal type: the one with smallest M-v class among violators
            Cfirst[min(types,key=lambda t:t[1])]+=1
    print(r,"all types",sorted(C.items()))
    print("  'best' type per failing b",sorted(Cfirst.items()))
