# Does the "robust" sufficient condition for (Z2), E_{s0+1} >= E_{s0+2} + E_{s0+4}, hold at the first negative index s0?
import sys, random
sys.path.insert(0,'.')
from zigzag import ZZ
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); tot=0; bad=0; ex=[]
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
        tot+=1
        if Ev(s0+1) < Ev(s0+2)+Ev(s0+4):
            bad+=1
            if len(ex)<4: ex.append((r,a,d2,s0,[Ev(j) for j in range(s0-1,s0+6)],[A[j] for j in range(s0-1,s0+5)]))
print("delta-instances",tot,"robust condition fails",bad)
for e in ex: print(e)
