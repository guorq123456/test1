# Model gap delta = X_odd - X_even (variant A, closed form) over random residue vectors; asymptotic S2 <=> 1<=delta<2.
# Pure formula evaluation (no instance computation) -- uses only (r, residues); kept inside box (r<=120,k<=140 or r>=1000).
import random, sys, math
from rule_asym import asym_tops
from boxcheck import allowed
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
mn=(9,None); mx=(-9,None); cnt=0
for _ in range(N):
    r=random.choice(list(range(4,121))+[1000,1001,1500,2001])
    k=random.randint(3,140)
    s=[random.randint(1,r-1) for _ in range(k)]
    if not any(2<=x<=r-2 for x in s) or not allowed(r,s): continue
    Xo,Xe,eo,ee=asym_tops(r,s)
    if not (math.isfinite(Xo) and math.isfinite(Xe)): continue
    d=Xo-Xe; cnt+=1
    if d<mn[0]: mn=(d,(r,k))
    if d>mx[0]: mx=(d,(r,k))
print('samples',cnt,'min delta',mn,'max delta',mx)
