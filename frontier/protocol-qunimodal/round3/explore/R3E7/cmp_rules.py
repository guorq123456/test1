# compare candidate rules for sharp L0 against true sharp L0 (exhaustive small + random), fit box only
import sys, random, itertools
from rules_lib import *
mode=sys.argv[1]
def gen():
    if mode=='exh':
        rmax,kmax=int(sys.argv[2]),int(sys.argv[3])
        for r in range(3,rmax+1):
            for k in range(2,kmax+1):
                for s in itertools.combinations_with_replacement(range(1,r),k): yield r,list(s)
    else:
        random.seed(int(sys.argv[2])); n=int(sys.argv[3]); rmax=int(sys.argv[4]); kmax=int(sys.argv[5])
        for _ in range(n):
            r=random.randint(4,rmax); k=random.randint(3,kmax); u=random.random()
            if u<0.3: s=[random.randint(1,r-1) for _ in range(k)]
            elif u<0.6:
                c=random.randint(2,r-2); s=[min(r-1,max(1,c+random.randint(-1,1))) for _ in range(k)]
            else:
                vals=random.sample(range(1,r),min(r-1,random.randint(2,4))); s=[random.choice(vals) for _ in range(k)]
            yield r,s
def Me2(R):
    E=[e for e in R.Uinf if e>=2]
    if not E: return 2
    return max(2,R.Delta(min(E))//2+R.r+1)
rules={'exact':L0_exact,'first':L0_first,'single':L0_single,'two':lambda R:2,'R2E7':lambda R:max(2,R.L0_R2E7()),'Me2':Me2,'maxs1':lambda R:max(R.s)+1}
ubv={'R2E7':0,'Me2':0,'maxs1':0}
err={k:0 for k in rules}; cnt=0; nontriv=0; ex={k:[] for k in rules}
for r,s in gen():
    R=Res(r,s); top=max(2,R.L0_R2E7())
    if not in_box(r,R.aL(top)): continue
    cnt+=1
    t=L0_sharp_true(R)
    if t>2: nontriv+=1
    for name,f in rules.items():
        v=f(R)
        if name in ubv and v<t: ubv[name]+=1
        if v!=t:
            err[name]+=1
            if len(ex[name])<3: ex[name].append((r,R.s,t,v))
print("upper-bound violations",ubv); print("instances",cnt,"nontrivial(L0>2)",nontriv,"errors",err)
for k,v in ex.items():
    if v: print(k,v)
