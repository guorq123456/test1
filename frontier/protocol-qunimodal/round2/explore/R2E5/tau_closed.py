# verify closed form: tau_t = (2/r) sum_{j=1}^{r-1} sin(pi j/r) * sigma_j^k * sin(pi j (k(s-1)+1-2t)/r),
#   sigma_j = sin(pi j s/r)/sin(pi j/r)   (checked with 60-digit mpmath against exact integers)
from mpmath import mp, sin, pi, mpf, nint
from rule_allequal_middle import _tau
mp.dps=80
bad=0;tot=0
for r in range(4,31):
    for s in range(2,r-1):
        for k in (3,7,20,41,60):
            T=_tau(r,s,k)
            for t in range(r):
                v=mpf(2)/r*sum(sin(pi*j/r)*(sin(pi*j*s/r)/sin(pi*j/r))**k*sin(pi*j*(k*(s-1)+1-2*t)/r) for j in range(1,r))
                tot+=1
                if int(nint(v))!=T[t] or abs(v-T[t])>mpf('1e-20'): bad+=1
print('tau closed form checks',tot,'mismatches',bad)
