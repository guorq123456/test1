# n=0 rows: excess pattern (B*-1) and holes, for r in args, compared to flat
import sys
from flat import flat_U
def rows(path,r):
    D={}
    for line in open(path):
        x=list(map(int,line.split())); _,s,n,k,F,T6=x[:6]; U=x[6:]
        if n==0: D[(s,k)]=U
    return D
for r in map(int,sys.argv[1:]):
    try: D=rows(f'data/U_r{r}.txt',r)
    except FileNotFoundError: D=rows(f'data2/U_r{r}.txt',r)
    for s in range(2,r-1):
        row=[]
        for k in range(3,61):
            if (s,k) not in D: continue
            U=D[(s,k)]; e=max(U)-1; miss=[x-1 for x in range(1,max(U)+1) if x not in U]
            E=flat_U(r,s,k); ef=max(E) if E else 0
            row.append(f"{e}"+('' if not miss else 'm'+','.join(map(str,miss)))+('' if e==ef and (E==list(range(1,e+1)) if not miss else True) else f"[{ef}]"))
        print(f"r={r} s={s} n=0:",' '.join(row))
