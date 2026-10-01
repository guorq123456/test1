# Independent (simple) implementation: numpy object-dtype convolution + full unimodality test.
import itertools, numpy as np, sys
from collections import defaultdict
def qint(a,r=1):
    p=np.zeros(r*(a-1)+1,dtype=object); p[::r]=1; return p
def unimodal(c):
    i=0;n=len(c)
    while i+1<n and c[i]<=c[i+1]: i+=1
    while i+1<n and c[i]>=c[i+1]: i+=1
    return i==n-1
def poly(a,b,r):
    p=np.array([1],dtype=object)
    for x in a: p=np.convolve(p,qint(x))
    return np.convolve(p,qint(b,r))
if __name__=='__main__':
    r=int(sys.argv[1]); K=int(sys.argv[2]); A=int(sys.argv[3]); Bx=int(sys.argv[4])
    agg=defaultdict(lambda:[0,0])
    suff=[]
    for k in range(1,K+1):
        for a in itertools.combinations_with_replacement([x for x in range(2,A+1) if x%r],k):
            F=sum(x//r for x in a); res=tuple(sorted(x%r for x in a))
            for b in range(2,F+2+Bx):
                u=unimodal(list(poly(a,b,r)))
                if b<=1+F:
                    if not u: suff.append((a,b))
                else:
                    key=(k,res,b-F-2); agg[key][1]+=1; agg[key][0]+=u
    print("suff failures",suff)
    for key in sorted(agg):
        uu,tot=agg[key]
        if uu: print(key,"unimodal %d/%d"%(uu,tot))
