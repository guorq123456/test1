# Hill climbing toward an S2 violation. usage: hill.py r seed iters kmin kmax
# score(a) = -1 if S2 violated; else min over 'violating flips' b in (B*,T6] (excluding B*+2 when U is an interval)
#   of nneg(b) + frac(b): nneg = #indices i<=N/2 with P_i<P_{i-1}; frac = neg mass/total variation (<1). 0 iff unimodal.
import sys,random,json
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E4')
from core import poly_a,dseq,T6,F_D,in_box,nmiddle
import numpy as np
def evaluate(r,a):
    A=poly_a(a); F,D=F_D(r,a); t6=T6(r,a,A)
    bhi=t6+1; L=(D+r*(bhi-1))//2+1
    d=dseq(A,r,L); mx=max(abs(x) for x in d) or 1
    darr=np.array(d,dtype=np.int64 if mx<2**62 else object)
    U={}; fr={}
    for b in range(F+1,bhi+1):
        N=D+r*(b-1); h=N//2; lo=r*b
        z=np.concatenate([darr[1:min(lo,h+1)], (darr[lo:h+1]-darr[0:h+1-lo]) if lo<=h else darr[0:0]])
        if len(z)==0: U[b]=True; fr[b]=0.0; continue
        neg=-z[z<0].sum() if (z<0).any() else 0
        tot=np.abs(z).sum()
        U[b]= (neg==0); fr[b]=int((z<0).sum())+(float(neg)/float(tot) if tot else 0.0)
    ins=[b for b in range(1,bhi+1) if b<=F or U[b]]
    Bs=max(ins); miss=[b for b in range(1,Bs+1) if b not in ins]
    shape='interval' if not miss else ('gap' if miss==[Bs-1] else 'bad')
    par=(Bs-1-F)%2==0
    viol= shape=='bad' or not par or Bs>t6
    if viol: return -1.0,dict(F=F,T6=t6,Bs=Bs,shape=shape,par=par,U=ins)
    cand=[b for b in range(Bs+1,t6+1) if not (shape=='interval' and b==Bs+2)]
    sc=min((fr[b] for b in cand),default=1e9)
    return sc,dict(F=F,T6=t6,Bs=Bs,shape=shape,pat=''.join('1' if U[b] else '0' for b in range(F+1,t6+1)))
def valid(r,a): return in_box(r,a) and all(x%r for x in a) and nmiddle(r,a)>=3 and len(a)<=40
def mutate(r,a,rng,kmin,kmax):
    a=list(a); m=rng.random()
    if m<0.35:
        i=rng.randrange(len(a)); a[i]+=rng.choice([-1,1])
    elif m<0.55:
        i=rng.randrange(len(a)); a[i]+=rng.choice([-r,r])
    elif m<0.7:
        i=rng.randrange(len(a)); a[i]=rng.randint(2,100)
    elif m<0.8 and len(a)<kmax: a.append(rng.randint(2,100))
    elif m<0.9 and len(a)>kmin: a.pop(rng.randrange(len(a)))
    else:
        i,j=rng.randrange(len(a)),rng.randrange(len(a)); t=rng.choice([1,r-1,r//2 or 1]); a[i]+=t; a[j]-=t
    return sorted(a)
if __name__=='__main__':
    r=int(sys.argv[1]); seed=int(sys.argv[2]); iters=int(sys.argv[3]); kmin=int(sys.argv[4]); kmax=int(sys.argv[5])
    rng=random.Random(seed)
    while True:
        k=rng.randint(kmin,kmax); a=sorted(rng.randint(2,min(100,3*r)) for _ in range(k))
        if valid(r,a): break
    sc,info=evaluate(r,a); best=(sc,a,info); nev=1; seen={}
    for it in range(iters):
        b=mutate(r,a,rng,kmin,kmax)
        if not valid(r,b): continue
        key=tuple(b)
        if key in seen: s2,i2=seen[key]
        else: s2,i2=evaluate(r,b); seen[key]=(s2,i2); nev+=1
        if s2<0:
            print(json.dumps(dict(VIOL=True,r=r,a=b,info=i2))); sys.stdout.flush(); break
        if s2<=sc or rng.random()<0.02:
            a,sc,info=b,s2,i2
            if sc<best[0]: best=(sc,a,info)
    print(json.dumps(dict(r=r,seed=seed,evals=nev,best_score=best[0],best_a=best[1],info=best[2])))
