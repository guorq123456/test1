import sys; sys.path.insert(0,'/home/user/test1/minimizer-frontier')
import numpy as np
from pnu import excess
def runs(b):
    """list of (char, start, length)"""
    out=[]; i=0
    while i<len(b):
        j=i
        while j<len(b) and b[j]==b[i]: j+=1
        out.append((b[i],i,j-i)); i=j
    return out
def edges(b):
    """rising edges with context: list of dict(i=index of 0, ctx=(c,a,b,d), trunc flags)"""
    R=runs(b); E=[]
    for k in range(len(R)-1):
        if R[k][0]=='0':
            a=R[k][2]; bb=R[k+1][2]; i=R[k][1]+a-1
            c=R[k-1][2] if k>=1 else 0
            d=R[k+2][2] if k+2<len(R) else 0
            ta=(k==0); tb=(k+1==len(R)-1)
            E.append(dict(i=i,a=a,b=bb,c=c,d=d,ta=ta,tb=tb,k=k,R=R))
    return E
def make_h(nu, select, noedge=lambda b:b.count('1')%2):
    h=np.zeros(1<<nu,dtype=np.int64); amb=0
    for W in range(1<<nu):
        b=format(W,f'0{nu}b'); E=edges(b)
        if not E: h[W]=noedge(b); continue
        v=select(b,E)
        h[W]=v
    return h
def argmax_parity(E, key, tie=None):
    best=max(key(e) for e in E); T=[e for e in E if key(e)==best]
    ps={e['i']%2 for e in T}
    if len(ps)==1: return ps.pop()
    return tie(T) if tie else None
def profile(hf, nus=(3,5,7,9,11,13)):
    return [excess(hf(nu),nu) for nu in nus]
