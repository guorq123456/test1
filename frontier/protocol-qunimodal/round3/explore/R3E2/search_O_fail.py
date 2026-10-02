# Search, inside the fit box, for rho = rho' + m ones (k = k'+m <= 140) violating O_rho.
# O_rho fails iff some odd j with ND_rho(K_j) false has K_j >= 2 mu*_inf + 3r.
# N*(rho) = least odd j with ND_rho(K_j) false (independent of m).
import random,sys
from reslev import *
def Nstar(R,r):
    sigma=R.D; j=1
    while True:
        K=sigma+1-r*(j+2)
        if not R.ND(K): return j
        j+=2
        if j>10*sigma//r+20: return None
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 0)
hits=0;tested=0;minslack=None
for it in range(int(sys.argv[2]) if len(sys.argv)>2 else 3000):
    r=random.randint(4,120); kp=random.choice([3,6,7,8,9,10,12])
    rp=sorted(random.randint(2,r-1) for _ in range(kp))
    R=Res(r,rp); sigma=R.D
    ns=Nstar(R,r)
    if ns is None: continue
    u0=(sigma+1-r*(ns+5))//2   # O fails iff mu*_inf <= u0
    if u0< -r: continue
    tested+=1
    # largest m allowed in box
    for m in [140-kp]:
        rho=[1]*m+rp
        if not inbox(r,rho): continue
        mi=mustar_inf(r,len(rho),R.tau)
        sl=mi-u0
        if minslack is None or sl<minslack[0]: minslack=(sl,r,rp,m,mi,u0,ns,sigma)
        if mi<=u0:
            hits+=1; print('O FAIL',r,rp,'m',m,'mu*_inf',mi,'u0',u0,'N*',ns,'sigma',sigma,flush=True)
print('tested',tested,'hits',hits,'min (mu*_inf-u0) at k=140:',minslack)
