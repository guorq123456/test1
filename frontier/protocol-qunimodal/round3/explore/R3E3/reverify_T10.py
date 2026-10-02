# Independent re-verification (own implementation cert.py) of the R2E2 residue certificate (TP,E,O)
# for all residue multisets rho (parts in [1,r-1]) with |rho| <= KMAX, restricted to the fit box.
import sys, itertools
from cert import Inst
from lib4 import in_box
r=int(sys.argv[1]); KMAX=int(sys.argv[2])
tot=0; skipped=0; fails=[]
def multisets(n,k):
    # counts c_1..c_{r-1} summing to k
    if n==1: yield (k,); return
    for c in range(k+1):
        for rest in multisets(n-1,k-c): yield (c,)+rest
for k in range(1,KMAX+1):
    for cnt in multisets(r-1,k):
        rho=[]
        for i,c in enumerate(cnt): rho+= [i+1]*c
        if not in_box(r,rho): skipped+=1; continue
        s=Inst(r,rho); tot+=1
        mu=s.mu_inf()
        if not s.TP() or s.EO(mu): fails.append(rho)
print("r",r,"KMAX",KMAX,"checked",tot,"skipped(out of box)",skipped,"fails",len(fails),fails[:5])
