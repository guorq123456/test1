from math import comb
import itertools
def readb(fn):
    d={}
    for line in open(fn):
        line=line.strip()
        if not line or line[0]=='#': continue
        k,v=line.split()[:2]; d[int(k)]=int(v)
    return d
a = {int(l.split()[0]):int(l.split()[1]) for l in open('a_dp.txt')}
N = max(a)
bA = readb('b225034.txt')
assert all(a[k]==v for k,v in bA.items()), "bfile mismatch"
print("A225034 b-file agrees, n<=", max(bA))
bf = {int(l.split()[0]):int(l.split()[1]) for l in open('bf.out')}
assert all(a[k]==v for k,v in bf.items()); print("brute force agrees n<=",max(bf))

# (1) inverse binomial transform form, and positive sum, and coefficient form
for n in range(1,N+1):
    s = sum((-1)**(n-1-k)*comb(n-1,k)*comb(2*k+3,k+1) for k in range(n))
    assert s==a[n], n
print("(1a) inverse binomial formula ok n<=",N)
for n in range(1,N+1):
    s = sum(comb(n-1,j)*comb(j+3,n-j) for j in range(n))
    assert s==a[n], n
print("(1b) positive sum ok n<=",N)
