# Stress (Key)/(Z2) on large-k residue-heavy instances inside the fit box (k<=40, a_i<=100, r<=30).
import sys, random
sys.path.insert(0,'.')
from zigzag import ZZ
from collections import Counter
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); z2bad=0; tot=0; inst=0
for it in range(N):
    r=random.randint(3,30); k=random.randint(10,40)
    mode=random.choice(['half','mixed','big'])
    if mode=='half': a=[random.randint(max(1,r//2-2),min(r-1,r//2+2)) for _ in range(k)]
    elif mode=='mixed': a=[random.randint(1,r-1)+r*random.randint(0,2) for _ in range(k)]
    else: a=[random.randint(1,100) for _ in range(k)]
    a=sorted(min(x,100) for x in a)
    if any(x%r==0 for x in a): continue
    inst+=1
    z=ZZ(r,a)
    for d2,(E,A) in z.data.items():
        s0=next((s for s,v in enumerate(A) if v<0),None)
        if s0 is None: continue
        L=max(j for j,v in enumerate(E) if v>0)
        tot+=1; c[s0-L]+=1
        Ev=lambda j: E[j] if j<len(E) else 0
        if not (A[s0+2]+Ev(s0+4)<0): z2bad+=1; print("Z2 FAIL",r,a,d2)
print("instances",inst,"delta-instances",tot,"(Z2) failures",z2bad,"s0-L:",sorted(c.items()))
