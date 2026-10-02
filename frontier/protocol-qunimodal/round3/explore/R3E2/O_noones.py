# O_rho for residue multisets with NO residue-1 parts (k = k'), random, in the fit box.
# Uses the proved equivalence  O_rho <=> r(N*(rho)+5) > sigma+1-2 mu*_inf  (Lemma 3 of proof_TPE.txt) and records slack.
import random,sys
from reslev import *
def Nstar(R,r):
    sigma=R.D; j=1
    while True:
        if not R.ND(sigma+1-r*(j+2)): return j
        j+=2
random.seed(int(sys.argv[1])); n=int(sys.argv[2])
tested=0;fails=[];sl={}
for it in range(n):
    r=random.randint(3,60); kp=random.randint(2,40)
    mode=random.random()
    if mode<0.5: rp=[random.randint(2,r-1) for _ in range(kp)]
    else: rp=[random.randint(2,max(2,r//3)) for _ in range(kp)]
    rp=sorted(rp)
    if not inbox(r,rp): continue
    R=Res(r,rp); sigma=R.D
    if sigma>2500: continue
    ns=Nstar(R,r); mi=mustar_inf(r,kp,R.tau)
    s=ns-((sigma+1-2*mi)//r-4); sl[s]=sl.get(s,0)+1; tested+=1
    if not (r*(ns+5) > sigma+1-2*mi): fails.append((r,rp)); print('O FAIL (no ones)',r,rp,ns,sigma,mi,flush=True)
print('tested',tested,'O failures',len(fails),'slack dist',sorted(sl.items()))
