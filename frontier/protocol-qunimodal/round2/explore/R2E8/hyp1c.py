import pickle,sys,collections
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
tab=pickle.load(open(sys.argv[1],'rb'))
c=collections.Counter()
for (r,mids,n1,nm),(Xs,info) in tab.items():
    res=list(mids)+[1]*n1+[r-1]*nm
    a=sorted(rho if rho!=1 else r+1 for rho in res)
    D,F,Gam,mu,T6=stats(r,a)
    tau=[Gam[t]-Gam[t-1] for t in range(r)]
    s=(D+1)%r
    if tau[s]<=-2 and s<2*mu:
        c[(2*mu-s>r, (s-2*mu)//r)]+=1
print(c)
