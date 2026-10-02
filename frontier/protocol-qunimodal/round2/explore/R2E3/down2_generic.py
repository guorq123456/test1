# Check Lemma 2 (U(b) => U(b-2)) on generic odd e with unimodal nonneg positive half (generators from generic_e*.py),
# and also count how often S2-(A) [U(b) with b odd-type => U(b+1)] and (B) [U(b)=>U(b-3)] fail for generic e
# (no F available for generic e, so (A) is tested in the parity-free form: max of the two parity chains differ by 1 or 3).
import random, sys
from generic_e import U_of_d
import generic_e, importlib
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
def rd(D,mode):
    H=(D+1)//2 + (0 if (D+1)%2==0 else 1)
    p=random.randint(0,H-1); vals=[0]*H; v=1; vals[0]=1
    for m in range(1,p+1): v+=random.randint(0,mode); vals[m]=v
    for m in range(p+1,H): v=max(0,v-random.randint(0,mode)); vals[m]=v
    d=[0]*(D+2)
    for m in range(H): d[m]=vals[m]; d[D+1-m]=-vals[m]
    if (D+1)%2==0: d[(D+1)//2]=0
    return d
viol2=0; tot=0; bad_chain=0
for it in range(N):
    r=random.randint(2,7); D=random.randint(2,40)
    d=rd(D,random.randint(1,4)) if it%2 else generic_e.rand_d(D)
    bmax=(D+1)//r+6
    U=set(U_of_d(r,d,bmax))
    for b in range(3,bmax+1):
        tot+=1
        if b in U and b-2 not in U: viol2+=1; print("VIOL",r,d,sorted(U))
    if U:
        ev=[b for b in U if b%2==0]; od=[b for b in U if b%2]
        if ev and od and abs(max(ev)-max(od)) not in (1,3): bad_chain+=1
        if ev and od and abs(max(ev)-max(od))==3 and min(max(ev),max(od))+1 in U: pass
print("pairs tested",tot,"violations of U(b)=>U(b-2):",viol2,"; instances with parity-chain maxima differing by not 1 or 3:",bad_chain,"of",N)
