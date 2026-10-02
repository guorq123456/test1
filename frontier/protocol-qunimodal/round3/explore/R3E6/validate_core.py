# Validate core.U against ground truth /tmp/claude-0/qu/tools/uni on random small instances (in box).
import random, subprocess
from core import U
random.seed(1)
lines=[]; meta=[]
for _ in range(400):
    r=random.randint(4,20); k=random.randint(2,9)
    a=sorted(random.randint(1,60) for _ in range(k))
    if any(x%r==0 for x in a): continue
    u,T6,mu=U(r,a)
    for b in range(1,T6+3):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); meta.append(b in u)
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
bad=sum(1 for o,m in zip(out,meta) if (o=='1')!=m)
print("cases",len(meta),"mismatch",bad)
