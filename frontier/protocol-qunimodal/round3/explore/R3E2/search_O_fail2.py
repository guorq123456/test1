# In-box search for an O_rho failure: rho = rho' + m ones with k = 140 (mu*_inf is nonincreasing in k,
# so k=140 is the most favourable in-box choice).  Reports the minimal gap  mu*_inf(140) - u0  (O fails iff <= 0).
import random,sys
from reslev import *
def Nstar(R,r):
    sigma=R.D; j=1
    while True:
        K=sigma+1-r*(j+2)
        if not R.ND(K): return j
        j+=2
random.seed(int(sys.argv[1])); n=int(sys.argv[2])
tested=0;hits=0;best=None
for it in range(n):
    r=random.randint(3,60)
    mode=random.random()
    kp=random.randint(2,30)
    if mode<0.4: rp=[random.randint(2,max(2,r//4)) for _ in range(kp)]
    elif mode<0.7: rp=[random.randint(2,r-1) for _ in range(kp)]
    else: rp=[random.choice([2,r-1,r//2]) for _ in range(kp)]
    rp=sorted(rp)
    rho=[1]*(140-kp)+rp
    if not inbox(r,rho): continue
    R=Res(r,rp); sigma=R.D
    if sigma>3000: continue
    ns=Nstar(R,r); u0=(sigma+1-r*(ns+5))//2
    if u0<mu_neg(r,R.tau): continue
    tested+=1
    mi=mustar_inf(r,140,R.tau)
    g=mi-u0
    if best is None or g<best[0]: best=(g,r,rp,ns,sigma,mi,u0)
    if g<=0: hits+=1; print('HIT',r,rp,ns,sigma,mi,u0,flush=True)
print('tested(u0>=mu_neg)',tested,'hits',hits,'best gap',best)
