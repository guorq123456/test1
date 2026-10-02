# Multi-scale instances (mix of small and large a_i): min L'-ratio (d_j-d_{j+1})/d_{j+3} over high off-failures
# (j = F mod 2, V_j<0, d_{j+3}>0); also (C)-violations per thread and S2 on U.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box, U_set
from test_s2 import s2_ok
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
C=Counter(); best=None
for it in range(N):
    r=random.randint(3,30)
    ks=random.randint(0,25); kb=random.randint(1,15); km=random.randint(0,10)
    a=[random.randint(2,min(6,r+3)) for _ in range(ks)]+[random.randint(50,100) for _ in range(kb)]+[random.randint(7,49) for _ in range(km)]
    a=sorted(x for x in a if x%r)
    if len(a)<2 or not in_box(r,a): continue
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    hi=False
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for j in range(0,len(d)-3):
            if (j-F)%2 or Vs[j]>=0 or d[j+3]==0: continue
            hi=True; C['high_fail']+=1
            rat=(d[j]-d[j+1])/d[j+3]
            if best is None or rat<best[0]: best=(rat,r,a,pair,j,d[j:j+4])
            if Vs[j+2]+d[j+3]>=0: C['C_viol']+=1; print("CVIOL",r,a,pair,j,flush=True)
    C['inst']+=1
    if hi:
        U=U_set(r,a); ok,_=s2_ok(U,F); C['s2_checked']+=1
        if not ok: C['S2FAIL']+=1; print("S2FAIL",r,a,U,flush=True)
print(dict(C)); print("min L' ratio at high failures:",best)
