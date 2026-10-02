# Verify core.Uset against ground-truth checker tools/uni on random instances in the fit box.
import random, subprocess, sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
random.seed(1)
lines=[];keys=[]
for _ in range(400):
    r=random.randint(2,9); k=random.randint(1,5)
    a=sorted(random.randint(1,25) for _ in range(k))
    U=Uset(r,a,bmax=12)
    for b in range(1,13):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); keys.append(b in U)
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
bad=sum(1 for o,kk in zip(out,keys) if (o=='1')!=kk)
print("checked",len(lines),"mismatches",bad)
