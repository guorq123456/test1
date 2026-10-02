# check fast cyclic tau in rule_T15 against direct linear computation (base.py) on box instances
import random,sys
sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E5')
from rule_T15 import _Bstar
from base import params
random.seed(3); bad=0
for _ in range(3000):
    r=random.randint(4,40); n=random.randint(0,20); ms=sorted(random.randint(2,r-2) for _ in range(3))
    if _Bstar(r,ms+[r-1]*n)!=params(ms,n,r)[6]: bad+=1
print("mismatch",bad)
