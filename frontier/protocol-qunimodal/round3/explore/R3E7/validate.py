# validate core.U_of against ground truth /tmp/claude-0/qu/tools/uni (in box), and up-ray monotonicity
import random, subprocess, sys
from core import *
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 1)
lines=[]; meta=[]
for it in range(400):
    r=random.randint(2,12); k=random.randint(1,7)
    a=sorted(random.choice([x for x in range(2,60) if x%r]) for _ in range(k))
    if not in_box(r,a): continue
    R=Res(r,[x%r for x in a]); F=sum(x//r for x in a)
    U=set(R.U_of(a)); Bmax=F+R.T+3
    for b in range(1,Bmax+1):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); meta.append((r,tuple(a),b,b in U))
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
bad=[m for m,o in zip(meta,out) if (o=='1')!=m[3]]
print("checked",len(meta),"mismatches",len(bad),bad[:5])
