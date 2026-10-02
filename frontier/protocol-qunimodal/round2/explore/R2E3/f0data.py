# Distribution of U for residue-only instances (all a_i < r, so F=0) via exact tcrit (validated).
import sys, itertools
from collections import Counter
sys.path.insert(0,'.')
from s2check import Uset
r=int(sys.argv[1]); k=int(sys.argv[2])
c=Counter(); ex={}
for a in itertools.combinations_with_replacement(range(1,r),k):
    U,t=Uset(r,list(a)); key=tuple(U); c[key]+=1
    ex.setdefault(key,a)
for key,v in sorted(c.items()): print(key,v,"e.g.",ex[key])
