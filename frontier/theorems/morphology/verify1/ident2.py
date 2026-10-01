import sys, time
sys.path.insert(0,'.')
from fast import *
t=time.time(); n1=n2=0; bad=[]
for k in range(0, 151):
    Nmax = 1000 if k <= 8 else 250
    a = A_seq(Nmax, k); b = B_seq(Nmax+1, k)
    for N in range(0, Nmax+1):
        n1 += 1
        if a[N] != b[N+1]: bad.append(('T1', k, N))
print('T1 done', n1, time.time()-t, flush=True)
for k in range(0, 31):
    Nmax = 1000 if k <= 4 else (400 if k<=10 else 150)
    c = C_seq(Nmax, k); d = D_seq(Nmax+1, k)
    for N in range(1, Nmax+1):
        n2 += 1
        if c[N] != d[N+1]: bad.append(('T2', k, N))
print('T2 done', n2, time.time()-t, 'bad', bad[:10], len(bad))
