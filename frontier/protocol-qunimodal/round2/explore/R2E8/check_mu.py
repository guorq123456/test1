# sanity: rule_H1's tau-based mu/T6 equals core.stats (Gamma based)
import random,sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *; import rule_H1
random.seed(3); bad=0
for _ in range(3000):
    r=random.randint(2,12); a=sorted(random.randint(1,30) for _ in range(random.randint(1,6)))
    if any(x%r==0 for x in a): continue
    D,F,Gam,mu,T6=stats(r,a)
    tau=rule_H1._tau(r,a); tg=[Gam[t]-Gam[t-1] for t in range(r)]
    if tau!=tg: bad+=1
print("tau mismatches",bad)
