# Count cases by (tau_s<=-2, s>=2mu) and min tau overall for 3-middle residues (canonical reps).
import pickle,sys,collections
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
tab=pickle.load(open(sys.argv[1],'rb'))
c=collections.Counter(); mint=collections.Counter()
for (r,mids,n1,nm),(Xs,info) in tab.items():
    res=list(mids)+[1]*n1+[r-1]*nm
    a=sorted(rho if rho!=1 else r+1 for rho in res)
    D,F,Gam,mu,T6=stats(r,a)
    tau=[Gam[t]-Gam[t-1] for t in range(r)]
    s=(D+1)%r
    c[(tau[s], s>=2*mu)]+=1; mint[min(tau)]+=1
print(sorted(c.items())); print(sorted(mint.items()))
