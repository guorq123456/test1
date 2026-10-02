"""Abstract test: two-sided geometric palindromic A (alpha_x = (m+1)^j m^(X-j), j = X-|x-X|), log-concave exactly.
Compute U(b<=Bmax) and check S2 shape (U = [1,B] or [1,B]minus{B-1}).  r<=120 only."""
import sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import times_b, unimodal
def U_of(al,r,Bmax):
    return [b for b in range(1,Bmax+1) if unimodal(times_b(al,r,b))]
def s2shape(U):
    if not U: return True
    B=max(U); S=set(U)
    return S==set(range(1,B+1)) or S==set(range(1,B+1))-{B-1}
if __name__=="__main__":
    bad=0; tot=0
    for m in [1,2,3,5,8,13,20]:
        for X in [20,40,80,160]:
            al=[(m+1)**(X-abs(x-X))*m**abs(x-X) for x in range(2*X+1)]
            for r in range(3,61):
                U=U_of(al,r,2*(2*X)//r+6); tot+=1
                if not s2shape(U):
                    bad+=1
                    if bad<=15: print("NOT S2: m",m,"X",X,"r",r,"U",U)
    print("tested",tot,"non-S2",bad)
