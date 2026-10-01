# Reclassify failures: first bad index i (smallest i<=h with g_i < g_{i-rb}).
#  Type I  : g_i < 0  (then i = X+1, the first negative coefficient of G; b-independent location)
#  Type II : g_i >= 0 but g_i < g_{i-rb} (pure overlap violation; needs i >= rb)
# Report counts, and for type II list (r,a,b), and whether condition (i) [h<=X] holds there.
import sys, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7')
from lfun import pcoef
def Gco(p,r,n):
    g=[0]*(n+1)
    for i in range(n+1):
        v=(p[i] if i<len(p) else 0)-(p[i-1] if 0<=i-1<len(p) else 0)
        g[i]=v+(g[i-r] if i>=r else 0)
    return g
cnt=collections.Counter(); II=[]
for Ln in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,Ln.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    p=pcoef(a); D=len(p)-1
    g=Gco(p,r,D+r*60)
    X=next(i for i in range(len(g)) if g[i]<0)-1
    for b in range(1,61):
        R=r*(b-1); N=D+R; h=N//2; rb=r*b
        bad=None
        for i in range(1,h+1):
            if g[i]-(g[i-rb] if i>=rb else 0)<0: bad=i; break
        if bad is None: continue
        typ='I' if g[bad]<0 else 'II'
        cnt[(r,typ)]+=1
        if typ=='II': II.append((r,a,b,D,X,h,rb,bad,g[bad],g[bad-rb], h<=X))
for kk in sorted(cnt): print(kk,cnt[kk])
with open('/tmp/claude-0/qu/explore/E7/typeII.txt','w') as f:
    for t in II: f.write(' '.join(map(str,t))+'\n')
print("type II instances",len(II),"; with condition (i) h<=X true:",sum(t[-1] for t in II))
print("bad-rb values:",collections.Counter(t[7]-t[6] for t in II))
print("(g_bad, g_{bad-rb}) values:",collections.Counter((t[8],t[9]) for t in II))
for t in II[:10]: print(t)
