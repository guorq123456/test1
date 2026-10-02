import random, subprocess, sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from core import *
random.seed(1)
lines=[];exp=[]
for _ in range(3000):
    r=random.randint(2,9); k=random.randint(1,6)
    a=sorted(random.randint(1,14) for _ in range(k)); b=random.randint(1,8)
    A=poly_a(a);D=len(A)-1
    g=gseq(A,r,(D+r*(b-1))//2+2)
    exp.append(1 if unimodal_g(g,r,D,b) else 0)
    lines.append(f"{r} {k} {' '.join(map(str,a))} {b}")
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
bad=sum(1 for x,y in zip(out,exp) if int(x)!=y)
print("mismatches",bad,"of",len(exp))
