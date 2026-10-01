import sys; sys.path.insert(0,'.')
from mine import minfilter2d_count, hardin2d_count
from fast import D_seq, B_seq
def rb(a):
    d={}
    for line in open('bf/b%d.txt'%a):
        s=line.split()
        if len(s)>=2 and not line.startswith('#'): d[int(s[0])]=int(s[1])
    return d
def antidiag_index(n,k):
    d=n+k; return (d-1)*(d-2)//2 + n
res=[]
for K,a,nb in [(1,217637,'hv'),(1,218084,'hva'),(1,217982,'hvda'),(2,217457,'hv'),(2,217645,'hva'),(2,217547,'hvda'),(3,218181,'hv'),(3,218651,'hva'),(3,218056,'hvda')]:
    b=rb(a); D=D_seq(12,K)
    for (n,m) in [(n,1) for n in range(1,9)]+[(n,2) for n in range(1,6)]+[(2,3),(3,2),(3,3)]:
        if (K+1)**(n*m)>6e5: continue
        v=minfilter2d_count(n,m,K,nb); t=b.get(antidiag_index(n,m))
        res.append((a,n,m,v,t,v==t, (v==D[n]) if (m==1 or nb=='hvda') else None))
for K,a in [(2,202889),(3,203101),(4,203191)]:
    b=rb(a); B=B_seq(12,K)
    for (n,m) in [(n,1) for n in range(1,9)]+[(2,2),(3,2),(2,3)]:
        if (K+1)**(n*m)>6e5: continue
        v=hardin2d_count(n,m,K); t=b.get(antidiag_index(n,m))
        res.append((a,n,m,v,t,v==t,(v==B[n]) if m==1 else None))
for r in res: print(r)
print('table mismatches', sum(1 for r in res if not r[5]), 'reduction mismatches', sum(1 for r in res if r[6] is False))
