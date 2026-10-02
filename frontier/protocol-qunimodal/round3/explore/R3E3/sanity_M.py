# check M = (1+q)(1+q+q^2)A' - [p(1+q+q^2)+s(1+q)(1+2q)]A >= 0 coefficientwise (p=#parts=2, s=#parts>=3)
import random
from lib4 import polyA
random.seed(4); bad=0
for it in range(3000):
    k=random.randint(1,25); a=[random.choice([2,2,3,3,4,5,7,8,9,11,15,30]) for _ in range(k)]
    p=a.count(2); s=k-p; c=polyA(a); D=len(c)-1
    al=lambda x: c[x] if 0<=x<=D else 0
    for j in range(-1,D+3):
        M=(j+1)*al(j+1)+(2*j-k)*al(j)+(2*j-2-p-3*s)*al(j-1)+(j-2-p-2*s)*al(j-2)
        if M<0: bad+=1; print(a,j,M); break
print("violations",bad)
