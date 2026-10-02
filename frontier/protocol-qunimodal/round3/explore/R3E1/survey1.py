"""Survey (exact): where is Q_{N*+4}(g) negative?  Per instance prints:
r k F N* |binding| |second tier| #g #negQ sign(Q at g nearest r/2) S2 bmin bmax"""
import random, sys
from winx import InstX
from box import in_box
def gen(rng,big):
    if big: r=rng.randint(1000,12000); k=rng.randint(20,140)
    else:   r=rng.randint(4,120); k=rng.randint(3,140)
    mode=rng.choice(["centred","uniform","bimodal","small"])
    a=[]
    for _ in range(k):
        if mode=="centred": c=rng.uniform(0.1,0.9); s=int(r*c+rng.gauss(0,r*0.02))
        elif mode=="uniform": s=rng.randint(1,r-1)
        elif mode=="bimodal": s=int(r*rng.choice([0.25,0.7])+rng.gauss(0,r*0.01))
        else: s=int(r*rng.uniform(0.05,0.3))
        s=min(max(s,1),r-1)
        nmax=(0 if rng.random()<0.5 else 3) if big else (400-s)//r
        a.append(rng.randint(0,max(nmax,0))*r+s)
    a.sort(); return r,a
def stats(I):
    G,ns,N=I.analyze()
    q={g:I.Q(N+4,g) for g in G}
    gm=min(G,key=lambda g:abs(g-I.r/2))
    sg=lambda v:(v>0)-(v<0)
    return [I.r,I.k,I.F,N,sum(1 for g in G if ns.get(g,-9)==N),sum(1 for g in G if ns.get(g,-9)==N+2),len(G),sum(1 for g in G if q[g]<0),sg(q[gm]),
            any(q[g]<0 for g in G),min(g for g in G if ns.get(g,-9)==N),max(g for g in G if ns.get(g,-9)==N)]
if __name__=="__main__":
    seed=int(sys.argv[1]); big=int(sys.argv[2]); cnt=int(sys.argv[3])
    rng=random.Random(seed)
    for it in range(cnt):
        r,a=gen(rng,big)
        if not in_box(r,a) or any(x%r==0 for x in a): continue
        print(*stats(InstX(r,a)),flush=True)
