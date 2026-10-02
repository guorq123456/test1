# compare data2 (n in {0,1}, r=9..30) with flat prediction; counts mismatches separately for n=0 and n>=1
import sys
from flat import flat_fast as flat_U
cache={}
def pred(r,s,n,k):
    if (r,s,k) not in cache: cache[(r,s,k)]=flat_U(r,s,k)
    F=k*n
    return list(range(1,F+2))+[F+1+e for e in cache[(r,s,k)]]
tot={0:0,1:0}; mm={0:0,1:0}
for r in range(int(sys.argv[1]),int(sys.argv[2])+1):
    for line in open(f'data2/U_r{r}.txt'):
        x=list(map(int,line.split())); _,s,n,k,F,T6=x[:6]; U=x[6:]
        key=0 if n==0 else 1
        tot[key]+=1
        if U!=pred(r,s,n,k):
            mm[key]+=1
            if key==1: print('n>=1 MISMATCH',r,s,n,k,U,pred(r,s,n,k))
print('n=0: lines',tot[0],'mismatch vs flat',mm[0]); print('n>=1: lines',tot[1],'mismatch vs flat',mm[1])
