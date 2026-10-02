# validate core.margins against ground truth /tmp/claude-0/qu/tools/uni
import random,subprocess,sys
sys.path.insert(0,'.')
from core import *
random.seed(1)
lines=[];exp=[]
for _ in range(3000):
    r=random.randint(2,12); k=random.randint(1,7)
    a=sorted(random.randint(1,30) for _ in range(k))
    bmax=random.randint(1,15)
    m=margins(r,a,bmax)
    for b in range(1,bmax+1):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); exp.append(m[b][0])
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
bad=sum(1 for e,o in zip(exp,out) if int(e)!=int(o))
print("cases",len(exp),"mismatches",bad)
