# Q1 test restricted to nontrivial cases: all-quotient-1 instance a=s+r has a part <= M_e2 (windows actually see the parts)
import sys, random
from core import *
random.seed(int(sys.argv[1])); n=int(sys.argv[2]); rmax=int(sys.argv[3]); kmax=int(sys.argv[4])
cnt=0; nontriv=0; fails=0; minmargin=None
while cnt<n:
    r=random.randint(3,rmax); k=random.randint(2,kmax)
    u=random.random()
    if u<0.4: s=[random.randint(1,r-1) for _ in range(k)]
    else:
        c=random.randint(1,r-1); s=[min(r-1,max(1,c+random.randint(-1,1))) for _ in range(k)]
    R=Res(r,s); a=sorted(x+r for x in R.s)
    if not in_box(r,a) or not in_box(r,R.aL(max(2,R.L0_R2E7()))): continue
    cnt+=1
    E=[e for e in R.Uinf if e>=2]
    if not E: continue
    M=R.Delta(min(E))//2+R.r
    if min(a)>M: continue
    nontriv+=1
    if not R.stable(a): fails+=1
print("instances",cnt,"nontrivial (some quotient-1 part inside a needed window)",nontriv,"Q1 fails",fails)
