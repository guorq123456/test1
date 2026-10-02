import sys
from collections import defaultdict
def load(r):
    D={}
    for line in open(f'data/U_r{r}.txt'):
        x=list(map(int,line.split()))
        r_,s,n,k,F,T6=x[:6]; U=x[6:]
        D[(s,n,k)]=(F,T6,U)
    return D
def desc(F,T6,U):
    # describe U as: B*-F, interval?, missing
    Bs=max(U)
    miss=[b for b in range(1,Bs+1) if b not in U]
    e=Bs-1-F
    return e, [m-1-F for m in miss], T6-1-F
if __name__=='__main__':
    r=int(sys.argv[1])
    D=load(r)
    for s in range(2,r-1):
        print('== r',r,'s',s)
        ns=sorted(set(n for (s_,n,k) in D if s_==s))
        for n in ns:
            row=[]
            for k in range(3,61):
                if (s,n,k) in D:
                    e,m,e6=desc(*D[(s,n,k)])
                    row.append(f"{e}" + ("" if not m else "m"+",".join(map(str,m))))
            print(f"n={n}:", ' '.join(row))
