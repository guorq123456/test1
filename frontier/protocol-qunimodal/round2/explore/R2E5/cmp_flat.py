# compare data U with flat-regime prediction; report mismatches per (r,s,n)
import sys
from flat import flat_U
from collections import defaultdict
cache={}
def pred(r,s,n,k):
    if (r,s,k) not in cache: cache[(r,s,k)]=flat_U(r,s,k)
    F=k*n
    return list(range(1,F+2))+[F+1+e for e in cache[(r,s,k)]]
for r in map(int,sys.argv[1:]):
    mm=defaultdict(list); tot=defaultdict(int)
    for line in open(f'data/U_r{r}.txt'):
        x=list(map(int,line.split())); _,s,n,k,F,T6=x[:6]; U=x[6:]
        tot[(s,n)]+=1
        if U!=pred(r,s,n,k): mm[(s,n)].append(k)
    for key in sorted(tot):
        if mm[key]: print(r,key,'mismatch k:',mm[key])
    print(r,'total lines',sum(tot.values()),'mismatching lines',sum(len(v) for v in mm.values()))
