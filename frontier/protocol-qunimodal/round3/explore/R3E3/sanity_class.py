# check: for r=4, x_{n*+1} and gap g=x_{n*+1}-x_{n*+2} satisfy: sigma odd -> g=2, x==(sigma-1)/2 mod 4;
# sigma even -> (g=1, x==sigma/2+3 mod 4) or (g=3, x==sigma/2 mod 4)
import random
from lib4 import in_box
from pairs import pair_data
random.seed(11); bad=0; n=0
for it in range(3000):
    k=random.randint(1,25); a=sorted(random.choice([x for x in range(1,50) if x%4]) for _ in range(k))
    if not in_box(4,a): continue
    sig=sum(x%4-1 for x in a)
    for p in pair_data(4,a):
        m=p['nstar']
        if m is None: continue
        n+=1; x=p['x'](m+1); g=x-p['x'](m+2)
        ok = (g==2 and (x-(sig-1)//2)%4==0) if sig%2 else ((g==1 and (x-sig//2-3)%4==0) or (g==3 and (x-sig//2)%4==0))
        if not ok: bad+=1
print(n,bad)
