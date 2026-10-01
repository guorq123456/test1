# Z = 2X+1-D-rF (F=sum floor(a_i/r)); case-A threshold B_A = 1+F+floor(Z/r). Tabulate Z by r.
# Also verify quasi-symmetry g_i - g_{D-r+1-i} = S_{i mod r}-S_{(i-1) mod r} for 0<=i<=D-r+1.
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7')
from lfun import pcoef
def Gco(p,r,n):
    g=[0]*(n+1)
    for i in range(n+1):
        v=(p[i] if i<len(p) else 0)-(p[i-1] if 0<=i-1<len(p) else 0)
        g[i]=v+(g[i-r] if i>=r else 0)
    return g
Z=collections.Counter(); qs_bad=0; qs_tot=0
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k])
    p=pcoef(a); D=len(p)-1
    g=Gco(p,r,D+3*r)
    X=next(i for i in range(len(g)) if g[i]<0)-1
    F=sum(v//r for v in a)
    Z[(r,2*X+1-D-r*F)]+=1
    S=[sum(p[j] for j in range(len(p)) if j%r==t) for t in range(r)]
    for i in range(0,D-r+2):
        qs_tot+=1
        if g[i]-g[D-r+1-i]!=S[i%r]-S[(i-1)%r]: qs_bad+=1
print("quasi-symmetry checks",qs_tot,"failures",qs_bad)
for r in range(2,7):
    print(r, sorted((z,c) for (rr,z),c in Z.items() if rr==r))
