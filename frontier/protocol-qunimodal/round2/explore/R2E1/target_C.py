# Targeted search for violations of Lemma L' and of per-thread (C) in the "slow growth" regime:
# small k (4..8), large a (near 100), middle residues near r/2. Also computes S2 on U.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box, U_set
from test_s2 import s2_ok
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
C=Counter(); ex=[]
for it in range(N):
    r=random.randint(6,30); k=random.randint(4,8)
    a=[]
    while len(a)<k:
        rho=random.randint(max(2,r//2-r//4), min(r-2, r//2+r//4))
        m=(100-rho)//r
        f=random.randint(max(0,m-2),m)
        x=rho+r*f
        if 2<=x<=100 and x%r: a.append(x)
    a.sort()
    if not in_box(r,a): continue
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    viol_thread=False
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for j in range(0,len(d)-3):
            if (j-F)%2 or Vs[j]>=0: continue
            C['negV']+=1
            if d[j+3]>0: C['negV_pos']+=1
            if not d[j]>=d[j+1]+d[j+3]:
                C["L'fail"]+=1
                if Vs[j+2]+d[j+3]>=0: C['C_thread_viol']+=1; viol_thread=True; ex.append((r,a,pair,j))
    if viol_thread or random.random()<0.2:
        U=U_set(r,a); ok,why=s2_ok(U,F); C['S2checked']+=1
        if not ok: C['S2_FAIL']+=1; print("S2 FAIL",r,a,U,F,flush=True)
print(dict(C)); print(ex[:5])
