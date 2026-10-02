"""Exact unimodality profile b=1..B of A(q)[b]_{q^r} for an arbitrary palindromic A given by left-half delta (D even)."""
import sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import times_b, unimodal
def alpha_from_delta(dl):
    X=len(dl)-1; D=2*X
    al=[0]*(D+1); s=0
    for x in range(X+1): s+=dl[x]; al[x]=s
    for x in range(X+1,D+1): al[x]=al[D-x]
    return al
def profile(dl,r,B):
    al=alpha_from_delta(dl); assert unimodal(al)
    return [b for b in range(1,B+1) if unimodal(times_b(al,r,b))]
if __name__=="__main__":
    dl=[1]*14+[2]*5
    print(alpha_from_delta(dl)); print("U (b<=30):",profile(dl,6,30))
