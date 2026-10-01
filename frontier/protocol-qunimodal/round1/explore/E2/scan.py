# Full scan of the fit box (r in 2..6, k<=8, 2<=a_i<=12, no r|a_i; a_i=1 factors are trivial and dropped)
# For each (r,a): tau (Fourier/residue), y*, c(t), B1=floor((D+1-2y*)/r)-1, pair-obstruction set O (b<=60 with K>0).
# Output: pickle of records.
import sys, itertools, pickle
from multiprocessing import Pool
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2')
from core import pcoef, tau
def analyze(args):
    r,a=args
    D=sum(x-1 for x in a); tt=tau(r,a)
    p=pcoef(a); L=D+2+r
    dp=[0]*(len(p)+1)
    for i,v in enumerate(p): dp[i]+=v; dp[i+1]-=v
    d=[0]*L
    for n in range(L):
        d[n]=dp[n] if n<len(dp) else 0
        if n>=r: d[n]+=d[n-r]
    def dd(v): return d[v] if 0<=v<L else (0 if v<0 else tt[v%r])
    ys=None
    for y in range(-r, D+2):
        if dd(y) < tt[y%r]: ys=y
    cs=[c for c in range(r) if tt[c]>0]; c=max(cs)
    B1=(D+1-2*ys)//r - 1
    O=[]
    for b in range(1,61):
        K=D+1-r*(b+1)
        if K<=0: break
        for u in range(K//2+1, min(K, D+1-r)+1):
            E=dd(u)-tt[u%r]
            if E>=0 and E<dd(K-u): O.append((b,u,K-u)); break
    return (r,tuple(a),D,tuple(tt),ys,c,B1,O)
def jobs():
    for r in range(2,7):
        for k in range(1,9):
            for a in itertools.combinations_with_replacement([x for x in range(2,13) if x%r],k):
                yield (r,list(a))
if __name__=='__main__':
    with Pool(8) as P:
        res=P.map(analyze, list(jobs()), chunksize=500)
    pickle.dump(res,open('/tmp/claude-0/qu/explore/E2/scan.pkl','wb'))
    print(len(res))
