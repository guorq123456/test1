# Per class pair delta (with tau~(delta)!=0): s0 = first s with A_s<0, L = last j with E_j>0.
# Distribution of s0-L, and check (Z2): A_{s0+2}+E_{s0+4} < 0, and minimal slack.
import sys, random
sys.path.insert(0,'.')
from zigzag import ZZ
from collections import Counter
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); z2bad=0; tot=0; ex=[]
for it in range(N):
    r=random.randint(3,14); k=random.randint(1,10)
    a=sorted(random.randint(1,random.choice([r-1,2*r,4*r,60])) for _ in range(k))
    if any(x%r==0 for x in a): continue
    z=ZZ(r,a)
    for d2,(E,A) in z.data.items():
        s0=next((s for s,v in enumerate(A) if v<0),None)
        if s0 is None: continue
        L=max(j for j,v in enumerate(E) if v>0)
        tot+=1; c[s0-L]+=1
        Ev=lambda j: E[j] if j<len(E) else 0
        if not (A[s0+2]+Ev(s0+4)<0):
            z2bad+=1
            if len(ex)<5: ex.append((r,a,d2,E[:L+2],A[:L+3],s0))
print("delta-instances",tot,"(Z2) failures",z2bad)
print("distribution of s0-L:",sorted(c.items()))
for e in ex: print(e)
