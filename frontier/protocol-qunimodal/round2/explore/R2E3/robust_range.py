# For each delta: sbar = least s such that E_{t+1} >= E_{t+2}+E_{t+4} for all t>=s.  Compare with s0 and with the E-peak p.
import sys, random
sys.path.insert(0,'.')
from zigzag import ZZ
from collections import Counter
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); c2=Counter()
for it in range(N):
    r=random.randint(3,30); k=random.randint(1,40)
    mode=random.choice(['half','mixed','big','small'])
    if mode=='half': a=[random.randint(max(1,r//2-2),min(r-1,r//2+2)) for _ in range(k)]
    elif mode=='mixed': a=[random.randint(1,r-1)+r*random.randint(0,2) for _ in range(k)]
    elif mode=='small': k=random.randint(1,8); a=[random.randint(1,4*r) for _ in range(k)]
    else: a=[random.randint(1,100) for _ in range(k)]
    a=sorted(min(x,100) for x in a)
    if any(x%r==0 for x in a): continue
    z=ZZ(r,a)
    for d2,(E,A) in z.data.items():
        s0=next((s for s,v in enumerate(A) if v<0),None)
        if s0 is None: continue
        Ev=lambda j: E[j] if j<len(E) else 0
        n=len(E)
        sbar=0
        for t in range(n-1,-1,-1):
            if Ev(t+1)<Ev(t+2)+Ev(t+4): sbar=t+1; break
        p=max(range(n),key=lambda j:(E[j],-j))
        c['s0>=sbar' if s0>=sbar else 's0<sbar']+=1
        c2[sbar-p]+=1
print(c); print("sbar - peak distribution:",sorted(c2.items())[:30])
