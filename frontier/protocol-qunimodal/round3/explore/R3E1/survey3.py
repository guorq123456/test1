"""Cross-pair candidate witnesses on tuned large-r families (r>=1000, tight residues, F=0 or small) where the pair-local
inequality can fail.  Columns: r k F N* S2 W1 W2 W3 W4 W5 W6 NB ALLG nbind kifail_bind psi_sine_spread
 NB  : for every binding g with Q_{N*+4}(g)>=0, Q_{N*+4}(g+2)<0 (neighbour pair C-+2 rescues)
 ALLG: Q_{N*+4}(g)<0 for every g with psi(g)>0
 psi_sine_spread: max/min over g of psi(g)/sin(pi g/r) (1 = exactly sinusoidal class profile)"""
import random, sys, math
from winx import InstX
from box import in_box
from survey2 import psi_of
def gen_tuned(rng):
    r=rng.randint(3000,20000); k=rng.randint(60,130); c=rng.uniform(0.12,0.42); w=rng.randint(0,4)
    s0=int(round(c*r)); a=sorted(s0+rng.randint(-w,w) for _ in range(k))
    if rng.random()<0.3: a[0]+=r*rng.randint(1,2); a.sort()
    return r,a
def row(I):
    G,ns,N=I.analyze(); r=I.r
    q={g:I.Q(N+4,g) for g in G}; S2=any(v<0 for v in q.values())
    gm=min(G,key=lambda g:abs(g-r/2)); ps={g:psi_of(I,g) for g in G}
    g2=max(G,key=lambda g:ps[g])
    vb={g:I.Vt[g].get(N+1) for g in G}
    g3=min((g for g in G if vb[g] is not None),key=lambda g:vb[g])
    B=[g for g in G if ns.get(g)==N]
    Gs=set(G)
    NB=all(q[g]<0 or (g+2 in Gs and q[g+2]<0) for g in B)
    ALLG=all(q[g]<0 for g in G if ps[g]>0)
    kif=sum(1 for g in B if q[g]>=0)
    from fractions import Fraction
    mx=max(ps.values())
    rat=[float(Fraction(ps[g],mx))/math.sin(math.pi*g/r) for g in G if ps[g]>0]
    spread=max(rat)/min(rat) if rat else float('nan')
    return [r,I.k,I.F,N,int(S2),int(q[gm]<0),int(q[g2]<0),int(q[g3]<0),int(q[max(B)]<0),int(sum(q.values())<0),int(q[min(B)]<0),
            int(NB),int(ALLG),len(B),kif,"%.6f"%spread]
if __name__=="__main__":
    seed=int(sys.argv[1]); cnt=int(sys.argv[2]); rng=random.Random(seed)
    for it in range(cnt):
        r,a=gen_tuned(rng)
        if not in_box(r,a) or any(x%r==0 for x in a): continue
        print(*row(InstX(r,a)),flush=True)
