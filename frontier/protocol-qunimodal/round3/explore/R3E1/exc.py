"""List g with Q_{N*+4}(g) >= 0 for given instances (regenerated from survey1 seeds)."""
import random, sys
from winx import InstX
from box import in_box
from survey1 import gen
def show(I):
    G,ns,N=I.analyze(); r=I.r
    for g in G:
        q=I.Q(N+4,g)
        if q>=0:
            V=I.V(N+1,g); Dl=I.e((N+2)*r-g)-I.e((N+2)*r+g); top=I.e(g+(N+4)*r)
            tau=I.V(4*(I.D+1)//r+3 if (4*(I.D+1)//r+3-I.F)%2==0 else 4*(I.D+1)//r+4,g)
            print("  g",g,"n*",ns.get(g),"V_{N+1}",float(V),"Delta",float(Dl),"top",float(top),"Q",float(q),"tauwin",float(tau))
for seed,big,cnt in [(1,0,300),(2,1,60)]:
    rng=random.Random(seed)
    for it in range(cnt):
        r,a=gen(rng,big)
        if not in_box(r,a) or any(x%r==0 for x in a): continue
        I=InstX(r,a); G,ns,N=I.analyze()
        if any(I.Q(N+4,g)>=0 for g in G):
            print(r,len(a),I.F,"N*",N,"a=",a if len(a)<15 else "..."); show(I)
