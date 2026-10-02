# random survey of sharp L0 (in box only). prints rows: r k s L0 R2E7 K0 T Uinf  and flags L0>r
import sys, random
from core import *
seed=int(sys.argv[1]); n=int(sys.argv[2]); rmax=int(sys.argv[3]); kmax=int(sys.argv[4]); out=open(sys.argv[5],'w')
random.seed(seed)
def sharp(R):
    top=max(2,R.L0_R2E7())
    # candidate Ls: 2 and s_i+1+j r up to top
    Ls=sorted(set([2]+[x for x in range(2,top+1) if any((x-1-si)%R.r==0 for si in set(R.s))]))
    prev=None
    for L in Ls:
        if R.stable(R.aL(L)): return L
    return top
big=0;cnt=0
while cnt<n:
    r=random.randint(4,rmax); k=random.randint(3,kmax)
    mode=random.random()
    if mode<0.3: s=[random.randint(1,r-1) for _ in range(k)]
    elif mode<0.6:
        c=random.randint(2,r-2); s=[min(r-1,max(1,c+random.randint(-1,1))) for _ in range(k)]
    else:
        vals=random.sample(range(1,r),min(r-1,random.randint(2,4))); s=[random.choice(vals) for _ in range(k)]
    R=Res(r,s); top=max(2,R.L0_R2E7())
    if not in_box(r,R.aL(top)): continue
    if len(R.Uinf)==1: continue
    L=sharp(R); cnt+=1
    if L>r: big+=1
    out.write(f"{r} {k} {' '.join(map(str,R.s))} | L0={L} R2E7={R.L0_R2E7()} K0={R.K0} T={R.T} mu={R.mu} Uinf={R.Uinf}\n"); out.flush()
print("count",cnt,"L0>r",big)
