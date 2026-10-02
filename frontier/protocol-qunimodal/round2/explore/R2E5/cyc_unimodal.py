# Check "cyclic unimodality" of residue sums Gamma_t of [s]^k: tau_t >= 0 for all t with (D+1-r)/2 < t < (D+1)/2 (as integers, mod r),
# D = k(s-1).  (Lemma 11 => S2(i) for E_inf whenever this holds.)  Range r<=30, middle s, 3<=k<=60.
from rule_allequal_middle import _tau
bad=0;tot=0;ex=[]
for r in range(4,31):
    for s in range(2,r-1):
        for k in range(3,61):
            D=k*(s-1); tau=_tau(r,s,k)
            for y in range(1,r):
                if (D+1-y)%2: continue
                t=((D+1-y)//2)%r
                tot+=1
                if tau[t]<0: bad+=1; ex.append((r,s,k,y))
print('positions checked',tot,'negative',bad, ex[:10])
