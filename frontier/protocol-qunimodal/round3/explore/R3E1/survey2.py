"""Test candidate cross-pair witnesses for S2 (exact).  For each instance compute N*, and whether Q_{N*+4}(g)<0 at:
 W1 g nearest r/2 (t nearest r/4);  W2 g maximizing psi(g)=|V_inf(g)| (class amplitude);  W3 g minimizing V_{N*+1}(g)
 (deepest binding);  W4 largest binding g;  W5 sum_g Q_{N*+4}(g) < 0 (uniform average);  W6 smallest binding g (pair-local KI at marginal end).
Output: r k F N* S2 W1..W6 (1 = witness works)."""
import random, sys
from winx import InstX
from box import in_box
def gen(rng,big):
    if big: r=rng.randint(1000,16000); k=rng.randint(20,140)
    else:   r=rng.randint(4,120); k=rng.randint(3,140)
    mode=rng.choice(["centred","uniform","bimodal","small","tight"])
    a=[]; c0=rng.uniform(0.05,0.95); w=rng.choice([0.001,0.003,0.01])
    for _ in range(k):
        if mode=="centred": c=rng.uniform(0.1,0.9); s=int(r*c+rng.gauss(0,r*0.02))
        elif mode=="uniform": s=rng.randint(1,r-1)
        elif mode=="bimodal": s=int(r*rng.choice([0.25,0.7])+rng.gauss(0,r*0.01))
        elif mode=="tight": s=int(r*c0+rng.gauss(0,r*w))
        else: s=int(r*rng.uniform(0.05,0.3))
        s=min(max(s,1),r-1)
        nmax=(0 if rng.random()<0.6 else rng.randint(1,3)) if big else (400-s)//r
        a.append(rng.randint(0,max(nmax,0))*r+s)
    a.sort(); return r,a
def psi_of(I,g):
    # V_inf(g): window large enough to cover all support
    b=4*(I.D+1)//I.r+4
    if (b-(2 if I.F%2==0 else 1))%2: b+=1
    return -I.V(b,g)
def witnesses(I):
    G,ns,N=I.analyze(); r=I.r
    q={g:I.Q(N+4,g) for g in G}
    S2=any(v<0 for v in q.values())
    gm=min(G,key=lambda g:abs(g-r/2))
    ps={g:psi_of(I,g) for g in G}
    g2=max(G,key=lambda g:ps[g])
    vb={g:I.Vt[g].get(N+1) for g in G}
    g3=min((g for g in G if vb[g] is not None),key=lambda g:vb[g])
    B=[g for g in G if ns.get(g)==N]
    return [r,I.k,I.F,N,int(S2),int(q[gm]<0),int(q[g2]<0),int(q[g3]<0),int(q[max(B)]<0),int(sum(q.values())<0),int(q[min(B)]<0)]
if __name__=="__main__":
    seed=int(sys.argv[1]); big=int(sys.argv[2]); cnt=int(sys.argv[3])
    rng=random.Random(seed)
    for it in range(cnt):
        r,a=gen(rng,big)
        if not in_box(r,a) or any(x%r==0 for x in a): continue
        print(*witnesses(InstX(r,a)),flush=True)
