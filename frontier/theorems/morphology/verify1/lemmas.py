import sys
sys.path.insert(0,'.')
from itertools import product
from mine import peak_free, valley_free, b_ok, eps3
def dplus(x):  # full dilation, len N -> N+1
    N=len(x); return tuple(max(x[j] for j in (i-1,i) if 0<=j<N) for i in range(N+1))
def eplus(x):
    N=len(x); return tuple(min(x[j] for j in (i-1,i) if 0<=j<N) for i in range(N+1))
def dminus(y): return tuple(max(y[j],y[j+1]) for j in range(len(y)-1))
def eminus(y): return tuple(min(y[j],y[j+1]) for j in range(len(y)-1))
def comp(x,k): return tuple(k-v for v in x)
cases=0
for k in range(0,6):
    for N in range(1,12):
        if (k+1)**(N+1) > 3e5: break
        cases+=1
        W = list(product(range(k+1),repeat=N))
        Y = list(product(range(k+1),repeat=N+1))
        AN = {x for x in W if peak_free(x)}; VN={x for x in W if valley_free(x)}; CN=AN&VN
        BN1 = {y for y in Y if b_ok(y)}
        DN1 = {eps3(w) for w in Y}
        # C1-C3
        for x in W:
            assert comp(dplus(x),k)==eplus(comp(x,k)) and comp(eplus(x),k)==dplus(comp(x,k))
        for y in Y:
            assert comp(dminus(y),k)==eminus(comp(y,k)) and comp(eminus(y),k)==dminus(comp(y,k))
        assert {comp(x,k) for x in AN}==VN and {comp(x,k) for x in CN}==CN
        # Lemma 1
        for u in W:
            ed = eminus(dplus(u))
            for j in range(N):
                if 1<=j<=N-2: assert ed[j]==max(u[j],min(u[j-1],u[j+1]))
                else: assert ed[j]==u[j]
            assert (ed==u)==(u in VN)
            de = dminus(eplus(u))
            exp = tuple(max(u[j-1],u[j+1]) if (1<=j<=N-2 and u[j]>u[j-1] and u[j]>u[j+1]) else u[j] for j in range(N))
            assert de==exp and all(a<=b for a,b in zip(de,u)) and ((de==u)==(u in AN))
        assert {eminus(y) for y in Y}==VN
        assert {dminus(y) for y in Y}==AN
        # Lemma 2
        img_dp = {dplus(x) for x in W}
        assert img_dp == BN1
        for y in Y:
            de = dplus(eminus(y))
            for i in range(N+1):
                if 1<=i<=N-1: assert de[i]==min(y[i],max(y[i-1],y[i+1]))
                elif i==0: assert de[0]==min(y[0],y[1])
                else: assert de[N]==min(y[N-1],y[N])
            if y in BN1: assert de==y
        # Theorem 1
        Phi = {x: dplus(comp(x,k)) for x in AN}
        assert set(Phi.values())==BN1 and len(set(Phi.values()))==len(AN)
        for x,y in Phi.items(): assert comp(eminus(y),k)==x
        for y in BN1: assert dplus(comp(comp(eminus(y),k),k))==y
        # Corollary 1: image of eps- size
        assert len({eminus(y) for y in Y})==len(AN)
        # Lemma 3
        for w in Y: assert eps3(w)==eplus(eminus(w))
        assert DN1=={eplus(u) for u in VN}
        # Lemma 4
        imgep = {eplus(u) for u in W}
        for z in imgep: assert eplus(dminus(z))==z
        for u in VN:
            g = dminus(eplus(u)); assert g in CN and eplus(g)==eplus(u)
        # Theorem 2
        Th = {x: eplus(x) for x in CN}
        assert set(Th.values())==DN1 and len(set(Th.values()))==len(CN)
        for x,z in Th.items(): assert dminus(z)==x
        for z in DN1: assert dminus(z) in CN and eplus(dminus(z))==z
print('all lemma checks passed; cases', cases)
