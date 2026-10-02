# data3: n>=2 for r=9..30 (all a<=100), k=3..60.  lines: r s n k F T6 U
import sys,os
from core import Uset_fast
os.makedirs('data3',exist_ok=True)
r=int(sys.argv[1])
with open(f'data3/U_r{r}.txt','w') as f:
    for s in range(2,r-1):
        for n in range(2,100):
            a=n*r+s
            if a>100: break
            for k in range(3,61):
                U,F,T6=Uset_fast(r,[a]*k,extra=2)
                f.write(f"{r} {s} {n} {k} {F} {T6} {' '.join(map(str,U))}\n"); f.flush()
