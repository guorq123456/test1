# Classify every non-unimodal instance in the box by failure type, using G = p/[r]_q (g_n coefficients):
#   (1-q)P = G(q)(1-q^{rb}), so Delta c_{i-1} = g_i - g_{i-rb}.  h=floor(N/2).
#   Type I  : first bad index i (smallest i<=h with g_i<g_{i-rb}) has g_i<0 and i<rb  -> i = X+1 (b-independent)
#   Type II : first bad index i >= rb (overlap of two shifted copies of G)
# Also verify: t (first strict descent, from viol.txt) == i-1, and exact criterion reproduces all 4.15M labels.
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7')
from lfun import pcoef
def Gco(p,r,n):
    g=[0]*(n+1)
    for i in range(n+1):
        v=(p[i] if i<len(p) else 0)-(p[i-1] if 0<=i-1<len(p) else 0)
        g[i]=v+(g[i-r] if i>=r else 0)
    return g
viol={}
for Ln in open('/tmp/claude-0/qu/explore/E7/viol.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); b,D,R,N,t,s,nd=x[2+k:]
    viol[(r,a,b)]=(t,s,nd)
cnt=collections.Counter(); mism=0; tmis=0; ex=collections.defaultdict(list)
uI=collections.Counter()
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    p=pcoef(a); D=len(p)-1
    g=Gco(p,r,D+r*60)
    X=next(i for i in range(len(g)) if g[i]<0)-1
    B=0
    while B<60 and (m>>B)&1: B+=1
    for b in range(1,61):
        R=r*(b-1); N=D+R; h=N//2; rb=r*b
        bad=None
        for i in range(1,h+1):
            if g[i]-(g[i-rb] if i>=rb else 0)<0: bad=i; break
        u=(m>>(b-1))&1
        if (bad is None)!=(u==1): mism+=1
        if bad is None: continue
        t=viol[(r,a,b)][0]
        if t!=bad-1: tmis+=1
        typ='I' if bad<rb else 'II'
        ff = 'first-fail' if b==B+1 else 'later'
        cnt[(r,typ,ff)]+=1
        if typ=='I': uI[(r, (2*bad - (D-r+1)))]+=1  # 2*(distance of first neg coef from quasi-center c=(D-r+1)/2)
        if typ=='II' and len(ex[(r,ff)])<4: ex[(r,ff)].append((a,b,D,X,bad,h,rb))
print("exact criterion label mismatches:",mism,"; t != bad-1 mismatches:",tmis)
for kk in sorted(cnt): print(kk,cnt[kk])
for kk in sorted(ex): print('typeII examples',kk,ex[kk])
print("Type I: 2u = 2(X+1)-(D-r+1), u = distance of first negative coef of G from quasi-center; by r:")
for r in range(2,7): print(r, sorted((v,c) for (rr,v),c in uI.items() if rr==r))
