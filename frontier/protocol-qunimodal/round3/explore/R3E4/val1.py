# validate fpair against brute force ground truth in the fit box (r<=120 small instances, k<20)
import random, subprocess, sys
sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpair import analyze
random.seed(5)
lines=[];meta=[]
for it in range(300):
    r=random.randint(4,40); k=random.randint(2,10)
    a=sorted(random.randint(1,4*r) for _ in range(k))
    if any(x%r==0 for x in a): continue
    res=analyze(r,a)
    Nst,beta=res['Nstar'],res['beta']
    U=set(range(1,Nst+1))|set(range(Nst+2,beta+1,2))
    for b in range(1,min(beta+5,40)):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); meta.append((b in U))
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
mis=sum(1 for o,m in zip(out,meta) if (o=='1')!=m)
print(len(lines),'tests, mismatches',mis)
