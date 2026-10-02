# table of flat-regime excess sets E_inf(r,s,k) for r<=Rmax, k<=60 (these equal U-(kn+1) for n>=1 instances in the fit box)
import sys
from flat import flat_U
Rmax=int(sys.argv[1]) if len(sys.argv)>1 else 12
for r in range(4,Rmax+1):
    for s in range(2,r-1):
        row=[]
        for k in range(3,61):
            E=flat_U(r,s,k)
            Em=max(E) if E else 0
            miss=[x for x in range(1,Em+1) if x not in E]
            row.append(str(Em)+('' if not miss else 'm'+','.join(map(str,miss))))
        print(f"r={r} s={s}:",' '.join(row))
