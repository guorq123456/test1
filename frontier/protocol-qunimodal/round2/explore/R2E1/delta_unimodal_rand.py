# Random test: delta=(1-q)A weakly unimodal on [0,(D+1)/2]? (k<=40, a<=100)
import sys, random
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import poly_a
from delta_unimodal import is_unimodal
random.seed(int(sys.argv[1]))
bad=0
for it in range(int(sys.argv[2])):
    k=random.randint(2,40); amax=random.choice([3,4,6,10,20,50,100])
    a=sorted(random.randint(2,amax) for _ in range(k))
    if random.random()<0.3:
        # mixtures of small and large
        a=sorted([random.randint(2,4) for _ in range(random.randint(1,20))]+[random.randint(20,100) for _ in range(random.randint(1,5))])
    A=poly_a(a);D=len(A)-1
    dl=[A[j]-(A[j-1] if j>0 else 0) for j in range(0,(D+1)//2+1)]
    if not is_unimodal(dl):
        bad+=1; print("BAD",a)
print("done bad",bad)
