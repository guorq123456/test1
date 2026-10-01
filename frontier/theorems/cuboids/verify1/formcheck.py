from math import comb
import gzip
def T(j): return j*(j+1)//2
def ceil2(a): return -((-a)//2)
def F(n): return (n-4)*T(ceil2(n-4))
def G(n):
    m=(n-1)//2
    return comb(m,2)+m*(m-1)*(m-2)+(comb(m,2) if n%2==0 else 0)
def B(n):
    v=(n-4)*(2*(n-4)*(n-1)-(2*n-5)*(-1)**n+3)
    assert v%16==0; return v//16
N=3000
assert all(F(n)==G(n)==B(n) for n in range(1,N+1))
for n in range(1,N+1):
    m=(n-1)//2
    if n==2*m+1: assert 2*F(n)==m*(m-1)*(2*m-3)
    else: assert F(n)==m*(m-1)**2
print("F(1..8)",[F(n) for n in range(1,9)])
def pmul(p,q):
    r=[0]*(len(p)+len(q)-1)
    for i,a in enumerate(p):
        for j,b in enumerate(q): r[i+j]+=a*b
    return r
den=pmul(pmul([1,1],[1,1]),pmul([1,1],pmul(pmul([1,-1],[1,-1]),pmul([1,-1],[1,-1]))))
seq=[0]+[F(n) for n in range(1,N+1)]
prod=[sum(den[i]*seq[k-i] for i in range(len(den)) if k-i>=0) for k in range(N+1)]
num=[0,0,0,0,0,1,1,4]+[0]*(N+1-8)
assert prod==num, "gf"
print("gf ok to",N)
sig=[1,3,-3,-3,3,1,-1]
a=seq
ok=[n for n in range(8,N+1) if a[n]==sum(sig[i]*a[n-1-i] for i in range(7))]
assert ok==list(range(8,N+1))
print("recurrence ok 8..",N,"; at n=7 rhs (a(0)=0) =",sum(sig[i]*a[6-i] for i in range(7)),"vs a(7)=",a[7])
st={}
for line in gzip.open('/tmp/claude-0/oeis/stripped.gz','rt'):
    if line.startswith(('A386884 ','A178312 ','A384311 ')):
        k,v=line.split(' ',1); st[k]=[int(t) for t in v.strip().strip(',').split(',')]
d=st['A386884']; assert all(d[i]==F(i+1) for i in range(len(d))), "A386884 data"; print("A386884 stored",len(d),"ok")
d=st['A178312']; assert all(d[i]==F(i+4) for i in range(len(d))); print("A178312 stored",len(d),"ok")
bf=[tuple(map(int,l.split())) for l in open('b178312.txt') if l.strip() and not l.startswith('#')]
assert all(v==F(k+4) for k,v in bf); print("A178312 bfile",len(bf),"ok, max k",bf[-1][0])
rows=[tuple(map(int,l.split())) for l in open('strict_types_1_200.txt')]
bad=[(n,v,F(n)) for n,v in rows if v!=F(n)]
print("strict type counts rows",len(rows),"max n",rows[-1][0],"mismatches",bad[:5])
