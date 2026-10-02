# As generic_cu.py but additionally require A log-concave.  Do (E)+(CU)+(LC) suffice for the S2 shape?
import random, sys
from collections import Counter
from generalA import U_of
from generic_cu import randA, cu_center, Bpos_of
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); ex=[]
for it in range(N):
    r=random.randint(2,7); D=random.randint(3,36); A=randA(D,random.randint(1,6))
    if not all(A[i]*A[i]>=A[i-1]*A[i+1] for i in range(1,len(A)-1)): c['notLC']+=1; continue
    cs=cu_center(A,r)
    if not cs: c['noCU']+=1; continue
    bp=Bpos_of(A,r)
    if bp is None: c['div']+=1; continue
    U=U_of(A,r,(D+1)//r+4)
    S=set(U); full=set(range(1,bp+1))
    sh='S2shape' if (S==full or S==full-{bp-1}) else 'FAIL'
    c[sh]+=1
    if sh=='FAIL' and len(ex)<6: ex.append((r,A,U,bp,cs))
print(c)
for e in ex: print(e)
