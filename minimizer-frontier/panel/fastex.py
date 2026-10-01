import sys; sys.path.insert(0,'/home/user/test1/minimizer-frontier')
import numpy as np
from w2 import cycles
_cache={}
def prep(nu):
    if nu in _cache: return _cache[nu]
    m=nu+2; rows=[]; wts=[]
    for cyc in cycles(m):
        if len(cyc)==1: continue
        e0=cyc[0]; s=[(e0>>(m-1-i))&1 for i in range(m)]
        idx=[]
        for j in range(m):
            W=0
            for t in range(nu): W=(W<<1)|s[(j+t)%m]
            idx.append(W)
        rows.append(idx); wts.append(len(cyc)/m)
    R=np.array(rows); w=np.array(wts)
    _cache[nu]=(R,w); return R,w
def fexcess(h,nu):
    R,w=prep(nu); v=h[R]; eq=(v==np.roll(v,-1,axis=1)).sum(1)
    return int(round((eq*w).sum()))-len(w)
if __name__=='__main__':
    from pnu import excess
    rng=np.random.default_rng(0)
    for nu in (5,7,9):
        h=rng.integers(0,2,1<<nu); print(nu,fexcess(h,nu),excess(h,nu))
