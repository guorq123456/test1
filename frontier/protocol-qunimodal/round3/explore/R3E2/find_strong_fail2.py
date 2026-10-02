import random
from reslev import *
random.seed(1)
found=0;tested=0
for it in range(4000):
    r=random.randint(6,30); kp=random.randint(4,14)
    rho=sorted(random.randint(2,r-1) for _ in range(kp))
    c=certificate(r,rho,strong=True); tested+=1
    if not (c['TP'] and c['E'] and c['O']):
        found+=1
        if found<=15: print(r,rho,c,flush=True)
print('tested',tested,'strongfail',found)
