# first k (3..60) with nonempty excess set: flat (n>=1) and n=0, for r<=30
import glob
from flat import flat_fast
D0={}
for f in glob.glob('data/U_r*.txt')+glob.glob('data2/U_r*.txt'):
    for line in open(f):
        x=list(map(int,line.split())); r,s,n,k,F,T6=x[:6]; U=x[6:]
        if n==0: D0[(r,s,k)]=max(U)-1
for r in range(4,31):
    row=[]
    for s in range(2,r-1):
        kf=next((k for k in range(3,61) if flat_fast(r,s,k)),None)
        k0=next((k for k in range(3,61) if D0.get((r,s,k),0)>0),None)
        row.append(f"s{s}:{kf}/{k0}")
    print(f"r={r}",' '.join(row))
