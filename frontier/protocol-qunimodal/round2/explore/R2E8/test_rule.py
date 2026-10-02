# Test a rule module (predict/domain) against exact U (core.Uset) on random in-domain tuples within fit box.
# usage: test_rule.py module seed n R0 R1 MAXO FMAX
import random,sys,importlib,collections
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
mod=importlib.import_module(sys.argv[1]); seed=int(sys.argv[2]); n=int(sys.argv[3]); R0,R1=int(sys.argv[4]),int(sys.argv[5]); MAXO=int(sys.argv[6]); FMAX=int(sys.argv[7])
random.seed(seed); errs=0; tested=0; inst=0; badinst=[]
for _ in range(n):
    r=random.randint(R0,R1)
    mids=[random.randint(2,r-2) for _ in range(3)]
    n1=random.randint(0,MAXO); nm=random.randint(0,MAXO)
    a=[m+r*random.randint(0,FMAX) for m in mids]+[1+r*random.randint(1,FMAX) for _ in range(n1)]+[r-1+r*random.randint(0,FMAX) for _ in range(nm)]
    a=sorted(x for x in a if x<=100)
    if len(a)>40 or not mod.domain(r,a): continue
    D,F,Gam,mu,T6=stats(r,a); bmax=T6+3
    U=set(Uset(r,a,bmax)); inst+=1; e=0
    for b in range(1,bmax+1):
        tested+=1
        if mod.predict(r,a,b)!=(b in U): e+=1
    errs+=e
    if e: badinst.append((r,a,sorted(U),T6,F))
print("instances",inst,"b-tests",tested,"errors",errs,"bad instances",len(badinst))
for x in badinst[:12]: print(x)
