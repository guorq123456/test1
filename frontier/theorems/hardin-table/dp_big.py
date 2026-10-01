# Exact (big-integer) row transfer-matrix DP for narrow widths, independent of dp.cpp.
# mode 0: original rule; mode 1: mirrored rule, so T(n,k) = DP_mode1(width n+1, rows k+1).
import sys
from itertools import product
def Drow(a,b): return [a[j]+b[j+1]-a[j+1]-b[j] for j in range(len(a)-1)]
def run(W,NMAX,mode):
    rows=list(product((0,1),repeat=W))
    states=[(a,b) for a in rows for b in rows if all(x<=y for x,y in zip(Drow(a,b),Drow(a,b)[1:]))]
    sid={s:i for i,s in enumerate(states)}
    Dst=[Drow(a,b) for a,b in states]
    adj=[[] for _ in states]
    for i,(a,b) in enumerate(states):
        P=Dst[i]
        for c in rows:
            if (b,c) not in sid: continue
            Q=Dst[sid[(b,c)]]
            ok=all(P[j]<=Q[j] for j in range(W-1))
            if ok:
                if mode==0: ok=all(P[j+1]<=Q[j] for j in range(W-2))
                else:       ok=all(Q[j]<=P[j+1] for j in range(W-2))
            if ok: adj[i].append(sid[(b,c)])
    cnt=[1]*len(states); out=[]
    for n in range(1,NMAX+1):
        out.append(sum(cnt))
        nc=[0]*len(states)
        for i,v in enumerate(cnt):
            if v:
                for j in adj[i]: nc[j]+=v
        cnt=nc
    return out
if __name__=="__main__":
    W,NMAX,mode=map(int,sys.argv[1:4])
    for n,v in enumerate(run(W,NMAX,mode),1): print(n,v)
