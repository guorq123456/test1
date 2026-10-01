# list r=6 nonmonotone cases with residues, Gamma (class sums of A mod r) and unimodal b-set
from load import *
from scond import Apoly
from collections import Counter
r=6; C=Counter()
for a,mask in load(r):
    S=uniset(mask); B=max(S)
    if S!=list(range(1,B+1)):
        A=Apoly(a); G=[sum(A[j] for j in range(s,len(A),r)) for s in range(r)]
        mn=min(G); Gn=[g-mn for g in G]
        Q=sum(x//r for x in a); D=len(A)-1
        C[(tuple(sorted(x%r for x in a)),tuple(b-1-Q for b in S))]+=1
        if C[(tuple(sorted(x%r for x in a)),tuple(b-1-Q for b in S))]==1:
            print(a,"res",sorted(x%r for x in a),"m-set",[b-1-Q for b in S],"Gamma-min",Gn,"D",D,"Q",Q)
print(len(C))
