import random
from lib4 import U
from pairs import S2_from_pairs
random.seed(3);mm=0;n=0
for it in range(400):
    r=random.choice([4,5,6]); k=random.randint(2,9)
    a=sorted(random.randint(2,40) for _ in range(k))
    if any(x%r==0 for x in a): continue
    u=U(r,a); N,b=S2_from_pairs(r,a)
    pred=list(range(1,N+1))+list(range(N+2,b+1,2))
    n+=1
    if pred!=u: mm+=1; print(r,a,u,N,b)
print(n,mm)
