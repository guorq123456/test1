# Candidate C1: quasi-linear (Beatty) closed form  E_even(r,s,k) = 2*max(0, floor(alpha*k+gamma))  with 2 free reals per (r,s), k=3..60.
# Checks feasibility with z3 for each (r,s); counts (r,s) pairs for which no (alpha,gamma) reproduces the data, and the
# minimal number of k-values that must be dropped (greedy lower bound not computed; we report infeasible pairs).
from z3 import Real, Solver, sat, Int
from flat import flat_fast
bad=0; tot=0; badlist=[]
for r in range(4,31):
    for s in range(2,r-1):
        Ev=[]
        for k in range(3,61):
            E=flat_fast(r,s,k); ev=[e for e in E if e%2==0]
            Ev.append(max(ev)//2 if ev else 0)
        # only use k where Ev>0 (positive part) plus the constraint that floor<=0 before
        al,ga=Real('al'),Real('ga'); S=Solver()
        for k,h in zip(range(3,61),Ev):
            if h>0: S.add(al*k+ga>=h, al*k+ga<h+1)
            else: S.add(al*k+ga<1)
        tot+=1
        if S.check()!=sat: bad+=1; badlist.append((r,s))
print('(r,s) pairs',tot,'with no exact Beatty fit of E_even over k=3..60:',bad)
print('examples',badlist[:20])
