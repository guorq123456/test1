# Q1: all-quotient-1 instance (a_i = s_i + r) is stable.
# Q2: stability depends only on zero pattern Z={i: a_i<r}: compare n=1 off Z vs random larger quotients off Z.
import sys, random
from core import *
seed=int(sys.argv[1]); n=int(sys.argv[2]); rmax=int(sys.argv[3]); kmax=int(sys.argv[4])
random.seed(seed)
q1bad=0; q2bad=0; cnt=0; q2cnt=0; ex=[]
while cnt<n:
    r=random.randint(3,rmax); k=random.randint(2,kmax)
    mode=random.random()
    if mode<0.3: s=[random.randint(1,r-1) for _ in range(k)]
    elif mode<0.6:
        c=random.randint(2,max(2,r-2)); s=[min(r-1,max(1,c+random.randint(-1,1))) for _ in range(k)]
    else:
        vals=random.sample(range(1,r),min(r-1,random.randint(2,4))); s=[random.choice(vals) for _ in range(k)]
    R=Res(r,s); top=max(2,R.L0_R2E7())
    if not in_box(r,R.aL(top)): continue
    if len(R.Uinf)==1: continue
    cnt+=1
    a1=sorted(x+r for x in R.s)
    if not R.stable(a1): q1bad+=1; ex.append(('Q1',r,a1))
    for trial in range(4):
        Z=[random.random()<random.random() for _ in R.s]
        base=sorted(x if z else x+r for x,z in zip(R.s,Z))
        big=sorted(x if z else x+r*random.randint(1,1+(400-x)//r -1 if (400-x)//r>1 else 1) for x,z in zip(R.s,Z))
        if not in_box(r,big) or not in_box(r,base): continue
        q2cnt+=1
        sb=R.stable(base); sg=R.stable(big)
        if sb!=sg: q2bad+=1; ex.append(('Q2',r,base,big,sb,sg))
print("instances",cnt,"Q1 fails",q1bad,"Q2 tests",q2cnt,"Q2 fails",q2bad)
for e in ex[:6]: print(e)
