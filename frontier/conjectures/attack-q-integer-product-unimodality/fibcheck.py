import subprocess, sys
sys.path.insert(0,'/tmp/claude-0/conj/scout-enum/fib')
from qfib import qfib
F=[0,1]
for i in range(200): F.append(F[-1]+F[-2])
def fibo(m,n):
    num=1;den=1
    for k in range(1,n+1): num*=F[m+k]; den*=F[k]
    assert num%den==0; return num//den
bad=0
for s in range(2,15):
    for n in range(1,s):
        m=s-n
        out=subprocess.run(['./fibq',str(m),str(n),'/tmp/claude-0/conj/attack-q-integer-product-unimodality/dump.txt'],capture_output=True,text=True).stdout
        ssum=int(out.split('sum=')[1],16)
        c=[int(x) for x in open('dump.txt')]
        p=list(qfib(m,n))
        ok = ssum==fibo(m,n) and c==p[:len(c)] and len(c)==(len(p)-1)//2+1
        # unimodality from python
        i=0
        while i+1<len(p) and p[i]<=p[i+1]: i+=1
        while i+1<len(p) and p[i]>=p[i+1]: i+=1
        um = (i==len(p)-1)
        if not ok or (('NOT' in out)==um): bad+=1; print("MISMATCH",m,n,out,len(c),len(p))
print("small cross-check mismatches:",bad)
