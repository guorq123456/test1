# Candidate C1 error count: per (r,s), best-fit (alpha,gamma) minimizing #k in 3..60 with E_even != 2*max(0,floor(alpha*k+gamma)).
# Reports total minimal error count over all 378 (r,s) pairs (each pair fitted with its own 2 free reals => 756 free params).
from z3 import Real, Optimize, If, And, Sum, sat
from flat import flat_fast
toterr=0; pairs=0; worst=[]
for r in range(4,31):
    for s in range(2,r-1):
        Ev=[]
        for k in range(3,61):
            E=flat_fast(r,s,k); ev=[e for e in E if e%2==0]
            Ev.append(max(ev)//2 if ev else 0)
        al,ga=Real('al'),Real('ga'); O=Optimize()
        for k,h in zip(range(3,61),Ev):
            if h>0: O.add_soft(And(al*k+ga>=h, al*k+ga<h+1))
            else: O.add_soft(al*k+ga<1)
        O.check(); m=O.model()
        a=m.eval(al); g=m.eval(ga)
        from fractions import Fraction
        A=Fraction(str(a.as_fraction())); G=Fraction(str(g.as_fraction()))
        import math
        err=sum(1 for k,h in zip(range(3,61),Ev) if max(0,math.floor(A*k+G))!=h)
        toterr+=err; pairs+=1
        if err: worst.append((err,r,s))
print('pairs',pairs,'total mispredicted k-values with best per-pair Beatty fit:',toterr)
print('pairs with errors',len(worst),'max err',max(worst) if worst else None)
