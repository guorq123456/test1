# Abstract test: d = unimodal nonneg integer sequence (d_0..d_{I-1}, then zeros), parity f in {0,1}.
# t0 = sum (-1)^i d_i ; TS: (-1)^f t0 >= 0.  OK(b): V_b>=0 and V_{b-1}+d_b>=0  (V_b = sum_{i<b} (-1)^{b-1-i} d_i)
# Check (i): OK(b), b=f mod 2 => OK(b+1);  (C): OK(b), b!=f mod2, b>=4 => OK(b-3); (A) OK(b)=>OK(b-2)
import itertools, sys
from collections import Counter
def V(d,b): return sum((-1)**(b-1-i)*d[i] for i in range(b))
def dd(d,i): return d[i] if i<len(d) else 0
def OK(d,b): return V(d,b)>=0 and V(d,b-1)+dd(d,b)>=0 if b>=1 else True
def unimodal(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
C=Counter(); ex={}
maxv=int(sys.argv[1]); maxI=int(sys.argv[2])
for I in range(1,maxI+1):
    for d in itertools.product(range(maxv+1),repeat=I):
        if not unimodal(d): continue
        d=list(d)
        t0=sum((-1)**i*x for i,x in enumerate(d))
        for f in (0,1):
            if (-1)**f*t0<0: continue
            C['cases']+=1
            B=len(d)+3
            dz=d+[0]*6
            for b in range(1,B+1):
                if not OK(dz,b): continue
                if b%2==f and not OK(dz,b+1): C['i']+=1; ex.setdefault('i',(d,f,b))
                if b%2!=f and b>=4 and not OK(dz,b-3): C['C']+=1; ex.setdefault('C',(d,f,b))
                if b>=3 and not OK(dz,b-2): C['A']+=1; ex.setdefault('A',(d,f,b))
print(C); print(ex)
