# validate wheel candidate count: odd m in (529, X] with J(p,m)=1 for all p<=23
from sympy import jacobi_symbol
X=3*10**6
P=[2,3,5,7,11,13,17,19,23]
c=0
for m in range(531, X+1, 2):
    if all(jacobi_symbol(p,m)==1 for p in P): c+=1
print(c)
