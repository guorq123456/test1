import sys,time,random; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpv import fast
from fpair import analyze, levels
for f in ['inst_ki_fail_r8595.txt','inst_ki_fail_r12552.txt','inst_ki_fail_r15167_Fodd.txt','inst_ki_fail.txt']:
    x=list(map(int,open('/tmp/claude-0/qu/synth/r2/'+f).read().split()))
    W,r,a=x[0],x[1],x[2:]
    t=time.time(); res=fast(r,a); print(f,res,time.time()-t)
random.seed(7); bad=0
for it in range(400):
    r=random.randint(4,60); k=random.randint(2,12)
    a=sorted(random.randint(1,5*r) for _ in range(k))
    if any(x%r==0 for x in a): continue
    p=fast(r,a); q=analyze(r,a)
    if (p['Nstar'],p['beta'])!=(q['Nstar'],q['beta']): bad+=1; print(r,a,p,q)
print('mismatch fast vs loop',bad)
