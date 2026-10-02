# Random sampling of the 3-middle class for r in [R0,R1]; record (r,a,U,T6,F,mu).
import random, sys, pickle
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
seed=int(sys.argv[1]); n=int(sys.argv[2]); R0=int(sys.argv[3]); R1=int(sys.argv[4]); MAXO=int(sys.argv[5]); FMAX=int(sys.argv[6])
random.seed(seed); rows=[]
for _ in range(n):
    r=random.randint(R0,R1)
    mids=[random.randint(2,r-2) for _ in range(3)]
    n1=random.randint(0,MAXO); nm=random.randint(0,MAXO)
    a=[m+r*random.randint(0,FMAX) for m in mids]
    a+= [1+r*random.randint(1,FMAX) for _ in range(n1)]
    a+= [r-1+r*random.randint(0,FMAX) for _ in range(nm)]
    a=[x for x in a if x<=100]
    a=sorted(a)
    if len(middle(r,a))!=3: continue
    D,F,Gam,mu,T6=stats(r,a); U=Uset(r,a)
    rows.append((r,tuple(a),tuple(U),T6,F,mu))
pickle.dump(rows,open(f'samp_{seed}_{n}_{R0}_{R1}_{MAXO}_{FMAX}.pkl','wb'))
print(len(rows))
