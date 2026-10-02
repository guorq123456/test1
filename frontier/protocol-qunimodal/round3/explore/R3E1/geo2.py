"""Abstract log-concave palindromic A with unimodal e: alpha = linear ramp (x+1) for x<m, then geometric ratio (m+1)/m
up to the centre X, mirrored.  Exact integers.  Tests S2 shape and all framework properties (r<=120 only)."""
import sys
from geo_test import U_of, s2shape
from geo_check import checks
def alpha(m,G):
    J=G+1
    left=[(x+1)*m**J for x in range(m)]+[m**(J+1-j)*(m+1)**j for j in range(1,G+1)]
    return left+left[-2::-1]
if __name__=="__main__":
    bad=0; tot=0; shown=0
    for m in [2,3,5,8,13,20,30]:
        for G in [10,20,40,80]:
            al=alpha(m,G)
            for r in range(3,41):
                U=U_of(al,r,2*len(al)//r+6); tot+=1
                if not s2shape(U):
                    bad+=1
                    N=max(b for b in range(1,len(U)+2) if all(c in U for c in range(1,b+1)))
                    c=checks(al,r,(N+1)%2)
                    if shown<12: shown+=1; print("NOT S2: m",m,"G",G,"r",r,"D",len(al)-1,"U",U,{k:v for k,v in c.items() if k not in('tau','Gamma')})
    print("tested",tot,"non-S2",bad)
