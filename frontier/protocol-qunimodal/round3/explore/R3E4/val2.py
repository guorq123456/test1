import random, sys
sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4'); sys.path.insert(0,'/tmp/claude-0/qu/tools')
from fpair import analyze
from gt_big import profile
random.seed(5); cnt=0
for it in range(300):
    r=random.randint(4,40); k=random.randint(2,10)
    a=sorted(random.randint(1,4*r) for _ in range(k))
    if any(x%r==0 for x in a): continue
    res=analyze(r,a); Nst,beta=res['Nstar'],res['beta']
    U=set(range(1,Nst+1))|set(range(Nst+2,beta+1,2))
    bs=list(range(1,min(beta+5,40)))
    pr=profile(r,a,bs); tru={b for b,p in zip(bs,pr) if p}
    if tru!=U & set(bs):
        cnt+=1
        if cnt<5: print(r,a,res, sorted(tru))
print(cnt)
