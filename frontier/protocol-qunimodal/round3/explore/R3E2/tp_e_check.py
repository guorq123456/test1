# Numerical sanity check of the proved statements TP_rho and E_rho (for ALL K>=? in the even family, no lower bound)
# and of the equivalence  O_rho <=> r(N*(rho)+5) > sigma+1-2 mu*_inf,  and  [ND_rho(K_j), j odd] <=> P_{j+1}(rho) unimodal.
import random,sys
from reslev import *
def Nstar(R,r):
    sigma=R.D; j=1
    while True:
        K=sigma+1-r*(j+2)
        if not R.ND(K): return j
        j+=2
random.seed(int(sys.argv[1])); n=int(sys.argv[2])
bad=dict(TP=0,Eall=0,Oeq=0,NDuni=0,Nstar_parity=0); cnt=0; slacks={}
for it in range(n):
    r=random.randint(2,40); k=random.randint(1,12)
    rho=sorted(random.randint(1,r-1) for _ in range(k))
    if not inbox(r,rho): continue
    if all(x==1 for x in rho): continue
    R=Res(r,rho); sigma=R.D
    try: mi=mustar_inf(r,k,R.tau)
    except ValueError: continue
    cnt+=1
    c=certificate(r,rho)
    if not c['TP']: bad['TP']+=1
    # E for all even j>=0 (no lower bound on K)
    for j in range(0,2*(sigma//r)+6,2):
        if not R.ND(sigma+1-r*(j+2)): bad['Eall']+=1; break
    ns=Nstar(R,r)
    if ns%2!=1: bad['Nstar_parity']+=1
    eq = r*(ns+5) > sigma+1-2*mi
    if eq != c['O']: bad['Oeq']+=1
    sl = ns - ((sigma+1-2*mi)//r - 4)
    slacks[sl]=slacks.get(sl,0)+1
    for j in range(1,ns+4,2):
        if R.ND(sigma+1-r*(j+2)) != R.unimodal(j+1): bad['NDuni']+=1; break
print('instances',cnt,'violations',bad)
print('slack N*-(floor(M/r)-4) distribution',sorted(slacks.items()))
