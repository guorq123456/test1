# Test H1: delta=2 iff tau_s + 1 < 0 and s >= 2mu, s=(D+1) mod r (using canonical reps from table pickle).
import pickle,sys,collections
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
tab=pickle.load(open(sys.argv[1],'rb'))
err=0; tot=0; conf=collections.Counter(); ex=[]
for (r,mids,n1,nm),(Xs,info) in tab.items():
    X=list(Xs)[0]; E6,mu=info; delta=E6-X
    res=list(mids)+[1]*n1+[r-1]*nm
    a=sorted(rho if rho!=1 else r+1 for rho in res)
    D,F,Gam,mu2,T6=stats(r,a)
    tau=[Gam[t]-Gam[t-1] for t in range(r)]
    s=(D+1)%r
    pred=2 if (tau[s]+1<0 and s>=2*mu) else 0
    conf[(delta,pred)]+=1; tot+=1
    if pred!=delta: err+=1; ex.append((r,mids,n1,nm,delta,pred,s,mu,tau))
print(conf, "err",err,"of",tot)
for e in ex[:15]: print(e)
