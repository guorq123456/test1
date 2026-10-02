# List small examples where H1 fires (tau_s<=-2, s>=2mu) and show failure positions at b=T6-1 and T6.
import sys, itertools
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *; import rule_H1
from failpos import fails
cnt=0
for r in range(4,9):
  for mids in itertools.combinations_with_replacement(range(2,r-1),3):
    for nm in range(0,2*r):
        a=sorted(list(mids)+[r-1]*nm)
        D,F,Gam,mu,T6=stats(r,a); tau=rule_H1._tau(r,a); s=(D+1)%r
        if tau[s]<=-2 and s>=2*mu:
            N1=D+r*(T6-2)
            f1=fails(r,a,T6-1); f0=fails(r,a,T6)
            print(r,mids,nm,"D",D,"F",F,"T6",T6,"mu",mu,"s",s,"tau",tau,"N/2(T6-1)",N1/2, "fail T6-1:",f1[:3],"fail T6:",f0[:2])
            cnt+=1
print(cnt)
