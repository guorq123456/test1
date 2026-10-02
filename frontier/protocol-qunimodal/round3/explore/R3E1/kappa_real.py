"""Decay rate at the crossing level for real instances: kappa = ln(delta_{x1}/delta_{x1-r}), x1 = (D+1)/2 - (N*+2)r/2.
Random fit-box instances (survey2.gen).  Prints r k F N* kappa and summary min."""
import random, sys, math
from winx import InstX
from box import in_box
from survey2 import gen
def kappa(I):
    G,ns,N=I.analyze(); r=I.r
    zc=(N+2)*r/2; x1=int(math.floor((I.D+1)/2-zc)); x2=x1-r
    d=lambda x: I.delta[x] if 0<=x<=I.X else 0
    if x2<0 or d(x2)<=0 or d(x1)<=0: return N,float('inf')
    return N,math.log(d(x1))-math.log(d(x2)) if d(x1)<2**1000 else (math.log2(d(x1))-math.log2(d(x2)))*math.log(2)
if __name__=="__main__":
    seed=int(sys.argv[1]); big=int(sys.argv[2]); cnt=int(sys.argv[3]); rng=random.Random(seed); ks=[]
    for it in range(cnt):
        r,a=gen(rng,big)
        if not in_box(r,a) or any(x%r==0 for x in a): continue
        I=InstX(r,a); N,k=kappa(I); ks.append((k,r,len(a),I.F,N))
        print(r,len(a),I.F,N,"%.3f"%k,flush=True)
    ks.sort(); print("MIN kappa",ks[:5])
