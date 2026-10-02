# Random search for S2 counterexamples inside the fit box.
import sys, random
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import *
from test_s2 import s2_ok
seed=int(sys.argv[1]); n=int(sys.argv[2])
random.seed(seed)
bad=[];gaps=0
for it in range(n):
    r=random.randint(4,30)
    k=random.randint(2,40)
    mode=random.random()
    if mode<0.4:
        amax=random.randint(2,3*r)
    elif mode<0.7:
        amax=random.randint(2,min(100,r+5))
    else:
        amax=random.randint(2,100)
    a=[]
    while len(a)<k:
        x=random.randint(2,amax)
        if x%r: a.append(x)
    a.sort()
    U=U_set(r,a);F=sum(x//r for x in a)
    ok,why=s2_ok(U,F)
    if set(U)!=set(range(1,max(U)+1)): gaps+=1
    if not ok:
        bad.append((r,a,U,F,why)); print("BAD",r,a,U,F,why,flush=True)
print("seed",seed,"tested",n,"gaps",gaps,"bad",len(bad))
