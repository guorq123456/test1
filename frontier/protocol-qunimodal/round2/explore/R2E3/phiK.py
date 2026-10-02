# For given (r,a), compute set of all integers K (any residue) where phi(K) holds:
# phi(K): T_x >= T_{K-x} for all x < K/2.
import sys, random
sys.path.insert(0,'.')
from tcrit import TS, F_of
def phi(t,K):
    for y in range(max(K//2+1,-2*t.r-abs(K)), t.H+1):
        x=K-y
        if x>=y: continue
        if t.T(x)<t.T(y): return False
    return True
def failK(r,a):
    t=TS(r,a)
    R=1+sum(x%r-1 for x in a)
    lo=-2*t.H-3*r; hi=2*t.H+2
    fails=[K for K in range(lo,hi+1) if not phi(t,K)]
    return t,R,fails
if __name__=='__main__':
    r=int(sys.argv[1]); a=list(map(int,sys.argv[2:]))
    t,R,f=failK(r,a)
    print("D",t.D,"H",t.H,"R",R,"F",F_of(r,a))
    print("fail K:",f)
    print("fail K - R by residue:")
    for rho in range(r):
        print(rho, [(K-R)//r for K in f if (K-R)%r==rho])
