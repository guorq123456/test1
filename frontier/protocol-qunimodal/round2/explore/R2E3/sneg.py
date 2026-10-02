# Per delta with tau~(delta)!=0: zigzag values Z_s (s>=0), Z_s - Z_{s+1} = A_s, Z_s -> +-|tau~|/2 on the two chains.
# s0 = first ascent (A_s<0); s_neg = first s of the lower chain (parity of s0) with Z_s < |tau~|/2.
# Report distribution of s_neg - s0 (claim (Z3): s_neg <= s0+2, which implies (Z2)).
import sys, random
sys.path.insert(0,'.')
from zigzag import ZZ
from collections import Counter
from fractions import Fraction
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter()
for it in range(N):
    r=random.randint(3,30); k=random.randint(1,40)
    mode=random.choice(['half','mixed','big','small'])
    if mode=='half': a=[random.randint(max(1,r//2-2),min(r-1,r//2+2)) for _ in range(k)]
    elif mode=='mixed': a=[random.randint(1,r-1)+r*random.randint(0,2) for _ in range(k)]
    elif mode=='small': k=random.randint(1,8); a=[random.randint(1,4*r) for _ in range(k)]
    else: a=[random.randint(1,100) for _ in range(k)]
    a=sorted(min(x,100) for x in a)
    if any(x%r==0 for x in a): continue
    z=ZZ(r,a)
    for d2,(E,A) in z.data.items():
        s0=next((s for s,v in enumerate(A) if v<0),None)
        if s0 is None: continue
        L=max(j for j,v in enumerate(E) if v>0)
        tau=A[L] if L%2==0 else -A[L]          # tau~ = (-1)^L A_L
        # Z_s up to additive constant: Z_s = Z_inf_chain + sum_{t>=s, same chain...}; easier: Z_{s+1}=Z_s-A_s, fix by limit of lower chain.
        Z=[Fraction(0)]
        for s in range(L+2): Z.append(Z[-1]-A[s])
        # lower chain (parity s0) limit must be -|tau|/2 : shift
        par=s0%2; lim=Z[L+1 if (L+1)%2==par else L]
        shift=Fraction(-abs(tau),2)-lim
        Zs=[v+shift for v in Z]
        sneg=next(s for s in range(par,len(Zs),2) if Zs[s]<Fraction(abs(tau),2))
        c[sneg-s0]+=1
print("s_neg - s0 distribution:",sorted(c.items()))
