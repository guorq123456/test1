# Generic e with d_0=1 (alpha_0=1), unimodal positive half, adversarial random shapes.
import random, sys
from generic_e import U_of_d, shape
from collections import Counter
def rand_d(D, mode):
    H=(D+1)//2 + (0 if (D+1)%2==0 else 1)
    p=random.randint(0,H-1)
    vals=[0]*H
    # increasing part m=0..p starting at 1
    v=1; vals[0]=1
    for m in range(1,p+1):
        v+=random.randint(0,mode); vals[m]=v
    for m in range(p+1,H):
        v=max(0,v-random.randint(0,mode)); vals[m]=v
    d=[0]*(D+2)
    for m in range(H): d[m]=vals[m]; d[D+1-m]=-vals[m]
    if (D+1)%2==0: d[(D+1)//2]=0
    return d
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); mode=int(sys.argv[3])
c=Counter(); ex=[]
for it in range(N):
    r=random.randint(2,7); D=random.randint(2,40)
    d=rand_d(D,mode)
    U=U_of_d(r,d,(D+1)//r+4)
    sh=shape(U); c[sh]+=1
    if sh=='other' and len(ex)<6: ex.append((r,d[:(D+3)//2],U))
print(c)
for e in ex: print(e)
