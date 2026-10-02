# Numerical sanity checks of the lemmas in proof_three_middle.txt on random tuples in the fit box:
# (S) symmetry g_i = tau_{i mod r} + g_{D+1-r-i} for 0<=i<=D+r;
# (F) if tau_s<=-2, s=(D+1) mod r, s>=2mu then U contains no b>=T6-1 (checked for b in [T6-1,T6+2]);
# (I) tau of a equals tau of the residue vector.
import random,sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *; import rule_H1
random.seed(9); badS=badF=badI=0; nF=0; n=0
for _ in range(4000):
    r=random.randint(2,15); a=sorted(random.randint(1,40) for _ in range(random.randint(1,7)))
    if any(x%r==0 for x in a): continue
    n+=1
    D,F,Gam,mu,T6=stats(r,a); g=gseq(a,r,D+2*r+2); tau=[g[D+1+((t-(D+1))%r)] for t in range(r)]
    G=lambda i: g[i] if i>=0 else 0
    if any(g[i]!=tau[i%r]+G(D+1-r-i) for i in range(0,D+r)): badS+=1
    if tau!=rule_H1._tau(r,[x%r for x in a]): badI+=1
    s=(D+1)%r
    if tau[s]<=-2 and s>=2*mu:
        nF+=1; U=Uset(r,a,T6+2)
        if any(b in U for b in range(max(1,T6-1),T6+3)): badF+=1
print("tuples",n,"symmetry failures",badS,"tau-invariance failures",badI,"lemmaF cases",nF,"lemmaF failures",badF)
