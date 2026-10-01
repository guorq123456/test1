# For families a=[s]*k (k<=8, in box), compute min slack of deep pairs (M-x >= 2r) at every b<=60,
# and max |delta| of Gamma, to see whether truncation at 2r is in danger as k grows.
import sys
sys.path.insert(0,'rules')
from common import gamma
from scond import Apoly
def eseq(r,a):
    A=Apoly(a); D=len(A)-1; G=gamma(r,a)
    L=D+3*r+5
    f=[(A[j] if j<=D else 0)-(A[j-1] if 0<=j-1<=D else 0) for j in range(L)]
    H=[0]*L
    for n in range(L): H[n]=f[n]+(H[n-r] if n>=r else 0)
    return (lambda y: G[y%r]-(H[y-r] if 0<=y-r<L else (0 if y-r<0 else H[D+1+((y-r-D-1)%r)]))),D,G
for r,s in [(4,2),(4,3),(5,2),(5,3),(6,3),(6,4),(6,2),(3,2)]:
    row=[]
    for k in range(1,9):
        e,D,G=eseq(r,[s]*k)
        dmax=max(abs(G[i]-G[(i+1)%r]) for i in range(r))
        mins=None
        for b in range(1,61):
            M=D+1-r*(b-1)
            for x in range(-3*r, (M+1)//2+1):
                if 2*x<M and M-x>=2*r and M-x<(D+1+r)/2+1:
                    d=e(x)-e(M-x)
                    mins=d if mins is None else min(mins,d)
        row.append((k,dmax,mins))
    print("r",r,"s",s,"(k, max|delta|, min deep-pair slack):",row)
