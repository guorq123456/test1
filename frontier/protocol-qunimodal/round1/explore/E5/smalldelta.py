# Is B* = B*_A whenever max|Gamma_t - Gamma_{t+1}| <= 1 ?  (and for residues all in {1,r-1})
import sys; sys.path.insert(0,'rules')
from common import gamma
from load import load, uniset
from collections import Counter
for r in range(2,7):
    C=Counter()
    for a,mask in load(r):
        G=gamma(r,a); D=sum(x-1 for x in a)
        mu=r-1
        while mu>0 and G[mu-1]>=G[mu]: mu-=1
        BA=1+(D+1-2*mu)//r; B=max(uniset(mask))
        dmax=max(abs(G[i]-G[(i+1)%r]) for i in range(r))
        unit=all(x%r in (1,r-1) for x in a)
        C[(dmax<=1, unit, B==BA)]+=1
    print(r,"(maxdelta<=1, residues in {1,r-1}, B*==B*_A):",sorted(C.items()))
