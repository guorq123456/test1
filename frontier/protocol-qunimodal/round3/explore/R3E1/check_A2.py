"""Exact check of Lemma A2 / (A3.1),(A3.2): window sums vs Phi-representation, random fit-box instances r<=120.
Doubled coordinates: Z=2z; Phi(W) = sum_{i>=0} e(W+2ir); H(W,G)=Phi(W-G)-Phi(W+G); psi = H(r,G) (F even) or Phi(2r-G)-Phi(G) (F odd)."""
import random
from winx import InstX
from box import in_box
import survey2
rng=random.Random(9); n=bad=0
for it in range(200):
    r,a=survey2.gen(rng,False)
    if not in_box(r,a) or any(x%r==0 for x in a): continue
    I=InstX(r,a); r=I.r
    def Phi(W):
        s=0; i=0
        while W+2*i*r<=I.D+1: s+=I.e(W+2*i*r); i+=1
        return s
    b0=2 if I.F%2==0 else 1
    for g in I.gaps(b0):
        psi=(Phi(r-g)-Phi(r+g)) if I.F%2==0 else (Phi(2*r-g)-Phi(g))
        for b in range(b0,b0+12,2):
            W=(b+1)*r   # doubled (b+1)r/2
            n+=1
            if I.V(b,g)!=Phi(W-g)-Phi(W+g)-psi: bad+=1
            if I.Q(b+1,g)!=I.V(b,g)+I.e(g+(b+1)*r): bad+=1
print("checks",n,"mismatches",bad)
