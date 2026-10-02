import random,subprocess
from lib4 import *
random.seed(1); bad=0; tot=0
lines=[];exp=[]
for it in range(300):
    r=random.randint(2,7); k=random.randint(1,6); a=[random.randint(1,20) for _ in range(k)]
    if any(x%r==0 for x in a): continue
    u=U(r,a)
    D=sum(x-1 for x in a)
    for b in range(1,D//r+4):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); exp.append(1 if b in u else 0)
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
print(len(lines), sum(1 for x,y in zip(out,exp) if int(x)!=y))
