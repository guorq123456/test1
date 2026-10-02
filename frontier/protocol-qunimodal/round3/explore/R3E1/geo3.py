"""Abstract: A = (two-sided geometric with linear ramp, see geo2.alpha) * prod [w_i]_q  (log-concave, palindromic).
Search for S2 failures with larger N*.  r<=120 only.  Prints failures with N*, beta and framework checks."""
import sys, random
from geo2 import alpha
from geo_test import U_of, s2shape
from geo_check import checks
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a
def mul(p,q):
    out=[0]*(len(p)+len(q)-1)
    for i,x in enumerate(p):
        if x:
            for j,y in enumerate(q): out[i+j]+=x*y
    return out
if __name__=="__main__":
    rng=random.Random(int(sys.argv[1]) if len(sys.argv)>1 else 0)
    tot=bad=0; best={}
    for it in range(int(sys.argv[2]) if len(sys.argv)>2 else 300):
        m=rng.choice([5,8,13,20,30,50]); G=rng.choice([5,10,20,40])
        ws=[rng.randint(2,40) for _ in range(rng.randint(1,4))]
        al=mul(alpha(m,G),poly_a(ws))
        r=rng.randint(3,40)
        if any(w%r==0 for w in ws): continue
        U=U_of(al,r,2*len(al)//r+6); tot+=1
        if not s2shape(U):
            bad+=1
            N=max(b for b in range(1,len(U)+2) if all(c in U for c in range(1,b+1)))
            c=checks(al,r,(N+1)%2)
            if N not in best or bad<40:
                best[N]=1
                print("NOT S2: m",m,"G",G,"ws",ws,"r",r,"D",len(al)-1,"N*",N,"U",U[:12],{k:v for k,v in c.items() if k not in('tau','Gamma')},flush=True)
    print("tested",tot,"non-S2",bad)
