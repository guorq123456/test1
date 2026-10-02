# print the shape-'other' (non-S2-shape, parity ignored) instances among random symmetric log-concave A
import random, sys
from generalA import *
from collections import Counter
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter()
for it in range(N):
    r=random.randint(2,7); D=random.randint(2,30); A=randLC(D)
    if A is None or not is_lc(A) or A!=A[::-1] or divisible_by_r(A,r): continue
    U=U_of(A,r,(D+1)//r+4); sh=shape(U,T6(A,r)).split('_')[0]; c[sh]+=1
    if sh=='other': print(r,A,U)
print(c)
