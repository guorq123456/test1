import subprocess, sys, time
F=[0,1]
for i in range(200): F.append(F[-1]+F[-2])
def fibo(m,n):
    num=1;den=1
    for k in range(1,n+1): num*=F[m+k]; den*=F[k]
    assert num%den==0; return num//den
pairs=[]
smin,smax=int(sys.argv[1]),int(sys.argv[2])
for s in range(smin,smax+1):
    for n in range(1,s//2+1): pairs.append((s-n,n))
for extra in sys.argv[3:]:
    m,n=map(int,extra.split(',')); pairs.append((m,n))
for m,n in pairs:
    t=time.time()
    out=subprocess.run(['./fibq',str(m),str(n)],capture_output=True,text=True).stdout.strip()
    ssum=int(out.split('sum=')[1],16)
    ok=(ssum==fibo(m,n))
    print(out.split(' sum=')[0], "SUMCHECK_OK" if ok else "SUMCHECK_FAIL", "%.1fs"%(time.time()-t), flush=True)
