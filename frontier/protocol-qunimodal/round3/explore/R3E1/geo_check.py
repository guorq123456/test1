"""For the geometric abstract S2 counterexamples, check the exact properties used by the class-pair framework:
log-concavity of alpha, unimodality of e (delta on left half), Wintner sign pattern of tau for F parity (N*+1 mod 2),
cyclic unimodality of Gamma.  Prints all checks."""
import sys
from fractions import Fraction
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import times_b, unimodal
from geo_test import U_of, s2shape
from lp_sign import pattern
def checks(al,r,Fpar):
    D=len(al)-1; X=D//2
    lc=all(al[x]**2>=al[x-1]*al[x+1] for x in range(1,D))
    alx=al+[0]; dl=[alx[x]-(alx[x-1] if x else 0) for x in range(D+2)]
    left=dl[:(D+1)//2+1] if (D+1)%2 else dl[:(D+1)//2]
    def unimod(s):
        i=0
        while i+1<len(s) and s[i]<=s[i+1]: i+=1
        while i+1<len(s) and s[i]>=s[i+1]: i+=1
        return i==len(s)-1
    eu=unimod(left)
    tau=[sum(dl[x] for x in range(D+2) if x%r==t) for t in range(r)]
    pat=pattern(r,X,Fpar,D=D)
    sg=all(s*tau[t]>=0 for t,s in pat)
    Gam=[sum(al[x] for x in range(D+1) if x%r==t) for t in range(r)]
    # cyclic unimodal: some rotation is unimodal
    cu=any(unimod(Gam[i:]+Gam[:i]) for i in range(r))
    return dict(logconcave=lc,e_unimodal=eu,sign_lemma=sg,Gamma_cyc_unimodal=cu,tau=tau,Gamma=Gam)
if __name__=="__main__":
    for m,X,r in [(8,40,3),(13,40,4),(20,20,5),(13,160,4)]:
        al=[(m+1)**(X-abs(x-X))*m**abs(x-X) for x in range(2*X+1)]
        U=U_of(al,r,2*(2*X)//r+6); N=max(b for b in range(1,len(U)+2) if all(c in U for c in range(1,b+1)))
        c=checks(al,r,(N+1)%2)
        print("m",m,"X",X,"r",r,"U",U,"N*",N,{k:v for k,v in c.items() if k not in('tau','Gamma')},"tau",[float(Fraction(t,c['Gamma'][0])) for t in c['tau']])
