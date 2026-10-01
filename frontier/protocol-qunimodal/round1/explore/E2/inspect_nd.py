import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2')
from core import *
from ystar import ystar
for r,a in [(6,[2,3,5,9,10,10,10]),(6,[1,4,4,4,8,9,9,11]),(3,[2]*6)]:
    D=sum(x-1 for x in a)
    U=[b for b in range(1,61) if truth(r,a,b)]
    print(r,a,"D=",D,"unimodal b:",U[:20],"tau",tau(r,a),"y*",ystar(r,a))
    d=dseq(r,a,D+2+r); tt=tau(r,a)
    for b in range(1,12):
        K=D+1-r*(b+1)
        if K<=0: break
        viol=[]
        for u in range(K//2+1, D+2-r):
            dv=d[K-u] if K-u>=0 else 0
            if d[u]-tt[u%r] < dv: viol.append((u,K-u,d[u],dv,tt[u%r]))
        print(" b",b,"K",K,"viol",viol[:5])
