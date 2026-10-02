# For random residue multisets (3 middle + n1 ones + nm (r-1)'s), enumerate all f-vectors (a=rho+r f) with
# f in [0,FMAX] (f>=1 for rho=1) up to symmetry and check whether X=|U|-1-F depends on f.
import random, sys, itertools, collections, pickle
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
seed=int(sys.argv[1]); ntrial=int(sys.argv[2]); R0,R1=int(sys.argv[3]),int(sys.argv[4]); MAXO=int(sys.argv[5]); FMAX=int(sys.argv[6])
random.seed(seed)
out=[]
for t in range(ntrial):
    r=random.randint(R0,R1)
    mids=sorted(random.randint(2,r-2) for _ in range(3))
    n1=random.randint(0,MAXO); nm=random.randint(0,MAXO)
    res=mids+[1]*n1+[r-1]*nm
    # enumerate f per element; limit total combos
    choices=[]
    for rho in res:
        lo=1 if rho==1 else 0
        hi=min(FMAX,(100-rho)//r)
        choices.append(range(lo,hi+1))
    total=1
    for c in choices: total*=len(c)
    seen=set(); Xs=collections.defaultdict(list); nonint=0
    it = itertools.product(*choices) if total<=3000 else (tuple(random.choice(c) for c in choices) for _ in range(3000))
    for fv in it:
        a=tuple(sorted(rho+r*f for rho,f in zip(res,fv)))
        if a in seen: continue
        seen.add(a)
        D,F,Gam,mu,T6=stats(r,list(a)); U=Uset(r,list(a))
        if list(U)!=list(range(1,len(U)+1)): nonint+=1; Xs['nonint'].append(a); continue
        Xs[len(U)-1-F].append(a)
    out.append((r,tuple(res),{k:len(v) for k,v in Xs.items()},{k:v[:3] for k,v in Xs.items()}, T6-1-F))
    if len(Xs)>1 or nonint:
        print(r,res,'E6',T6-1-F,{k:len(v) for k,v in Xs.items()},{k:v[:2] for k,v in Xs.items()})
pickle.dump(out,open(f'fixres_{seed}_{ntrial}_{R0}_{R1}_{MAXO}_{FMAX}.pkl','wb'))
print("done",len(out),"multi",sum(1 for o in out if len(o[2])>1))
