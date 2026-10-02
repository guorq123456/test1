# Heuristic asymptotic slope of E_even(r,s,k) in k:  (s-1-2*beta)/r, beta>0 root of (1+b)ln(1+b)-b ln b = ln rho,
# rho = max_{1<=j<r} |sin(pi s j/r)/sin(pi j/r)|.  Compared with the observed secant slope (E_even(60)-E_even(k1))/(60-k1)
# where k1 = first k with E_even>0 (only pairs with E_even(60)>=8).
import math
from mpmath import mp, findroot, log, mpf
rows={}
for line in open('Einf_table.txt'):
    if line.startswith('#'): continue
    r,s,k,Ee,Eo=map(int,line.split()); rows[(r,s,k)]=Ee
def beta(rho):
    f=lambda b: (1+b)*log(1+b)-b*log(b)-log(rho)
    lo,hi=mpf('1e-12'),mpf(50)
    for _ in range(200):
        mid=(lo+hi)/2
        if f(mid)>0: hi=mid
        else: lo=mid
    return float((lo+hi)/2)
out=[]
for r in range(4,31):
    for s in range(2,r-1):
        if rows[(r,s,60)]<8: continue
        rho=max(abs(math.sin(math.pi*s*j/r)/math.sin(math.pi*j/r)) for j in range(1,r))
        b=beta(rho); pred=(s-1-2*b)/r
        k1=next(k for k in range(3,61) if rows[(r,s,k)]>0)
        obs=(rows[(r,s,60)]-rows[(r,s,k1)])/(60-k1)
        out.append((r,s,round(pred,4),round(obs,4),round(obs/pred,3)))
for x in out[:12]: print(x)
rat=[x[4] for x in out]
print('pairs',len(out),'obs/pred ratio: min %.3f max %.3f mean %.3f'%(min(rat),max(rat),sum(rat)/len(rat)))
