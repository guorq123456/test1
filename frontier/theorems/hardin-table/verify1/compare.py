import os
def T(n,k):
    small={(1,1):16,(1,2):39,(1,3):69,(2,1):39,(2,2):58,(2,3):70,(3,1):69,(3,2):73,(3,3):85}
    if n<=3 and k<=3: return small[(n,k)]
    if k>=4 and n>=2: return 9*2**(n-1)+9*2**(k-1)+12
    if n==1 and k>=4: return 9*2**(k-1)+37
    if k==1 and n>=4: return 9*2**(n-1)+37
    if k==2 and n>=4: return 9*2**(n-1)+36
    if k==3 and n>=4: return 9*2**(n-1)+49
    raise Exception((n,k))
tm={}
for f in os.listdir('tmout'):
    if not f.endswith('.txt'): continue
    w,m=f[:-4].split('_'); w=int(w[1:]); m=int(m[1:])
    for line in open('tmout/'+f):
        p=line.split()
        if len(p)<4: continue
        n,k,v=int(p[0]),int(p[1]),int(p[2])
        key=(n,k) if m==0 else (k,n)
        tm.setdefault(key,[]).append(v)
bad=0; twice=0
for key,vs in tm.items():
    if len(set(vs))>1: print('internal disagreement',key,vs); bad+=1
    if len(vs)>1: twice+=1
    if vs[0]!=T(*key): print('THEOREM MISMATCH',key,vs[0],T(*key)); bad+=1
print('TM entries',len(tm),'computed twice',twice,'bad',bad)
# coverage
ks=sorted(tm); print('max n',max(a for a,b in ks),'max k',max(b for a,b in ks))
def rb(f):
    d={}
    for line in open(f):
        line=line.strip()
        if not line or line.startswith('#'): continue
        i,v=line.split()[:2]; d[int(i)]=int(v)
    return d
b=rb('bfiles/b253435.txt'); badb=0; cov=0
for idx,v in b.items():
    # find s with (s-2)(s-1)/2 < idx <= (s-1)s/2
    s=2
    while (s-1)*s//2 < idx: s+=1
    n=idx-(s-2)*(s-1)//2; k=s-n
    if T(n,k)!=v: badb+=1; print('bfile mismatch',idx,n,k,v,T(n,k))
    if (n,k) in tm:
        cov+=1
        if tm[(n,k)][0]!=v: print('TM vs bfile mismatch',n,k)
print('A253435 bfile terms',len(b),'theorem mismatches',badb,'also computed by my TM',cov,'max antidiag',s)
spec={'253152':lambda n:T(n,1),'253428':lambda n:T(n,n),'253429':lambda n:T(n,2),'253430':lambda n:T(n,3),
 '253431':lambda n:T(n,4),'253432':lambda n:T(n,5),'253433':lambda n:T(n,6),'253434':lambda n:T(n,7),
 '253436':lambda n:T(2,n),'253437':lambda n:T(3,n),'253438':lambda n:T(4,n),'253439':lambda n:T(5,n),'253440':lambda n:T(6,n),'253441':lambda n:T(7,n)}
for a,fn in spec.items():
    d=rb('bfiles/b%s.txt'%a); bd=[i for i,v in d.items() if fn(i)!=v]
    # also row 1 = A253152
    print('A'+a,len(d),'mismatches',bd[:5])
d=rb('bfiles/b253152.txt'); print('A253152 as row 1 mismatches',[i for i,v in d.items() if T(1,i)!=v][:5])
