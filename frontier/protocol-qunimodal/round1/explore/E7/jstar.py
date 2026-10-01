# Proven upper bound X <= D - j*, j* = max{ j in 0..r-1 : S_j > S_{(j-1) mod r} } (S_t residue-class sums of p).
# Gives necessary condition: unimodal => r(b-1) <= D+1-2j*.  Compare bound B_up=1+floor((D+1-2j*)/r) with true B.
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7/rules')
from rule_exact import _p, _g
viol=0; cmp=collections.Counter(); eqX=0; n=0
U={}
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    p=_p(a); D=len(p)-1; g=_g(p,r,D+3*r)
    X=next(i for i in range(len(g)) if g[i]<0)-1
    S=[sum(p[j] for j in range(t,D+1,r)) for t in range(r)]
    js=max(j for j in range(r) if S[j]>S[(j-1)%r])
    n+=1
    if X>D-js: viol+=1
    if X==D-js: eqX+=1
    B=0
    while B<60 and (m>>B)&1: B+=1
    Bup=1+(D+1-2*js)//r
    cmp[(r,'B==Bup' if B==Bup else ('B<Bup' if B<Bup else 'B>Bup!!'))]+=1
print("tuples",n,"violations of X<=D-j*:",viol,"; X==D-j* (tail-zone first negative):",eqX)
for kk in sorted(cmp): print(kk,cmp[kk])
