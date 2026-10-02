# For each instance: B_main (max of U with b-F odd), B_off (max of U with b-F even, 0 if none)
import sys, itertools
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import *
C=Counter()
for r in range(4,9):
    vals=[x for x in range(2,2*r+3) if x%r]
    for k in range(1,7):
        for a in itertools.combinations_with_replacement(vals,k):
            a=list(a); U=U_set(r,a); F=sum(x//r for x in a)
            Bm=max([b for b in U if (b-F)%2==1],default=0)
            Bo=max([b for b in U if (b-F)%2==0],default=0)
            C[Bm-Bo]+=1
print(C)
