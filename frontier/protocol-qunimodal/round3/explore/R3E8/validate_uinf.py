# Validate uinf.py against ground truth /tmp/claude-0/qu/tools/uni on random large-part instances in the fit box.
import random, subprocess, sys
from uinf import uinf
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 1)
lines=[];meta=[]
ntest=0
while ntest<300:
    r=random.randint(4,12); k=random.randint(2,9)
    s=[random.randint(1,r-1) for _ in range(k)]
    nm=sum(1 for x in s if 2<=x<=r-2)
    S=sum(s); L0=max(1,(S-k+3-r)//2)
    a=[]
    for x in s:
        q=random.randint((L0+r-1)//r+0,(L0+r-1)//r+2)
        v=q*r+x
        while v<L0: v+=r
        a.append(v)
    if max(a)>400 or sum(a)>1500: continue
    a.sort(); F=sum(v//r for v in a)
    res=uinf(r,[v%r for v in a])
    bmax=F+res['T']+3
    for b in range(1,bmax+1):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}")
        pred = (b<=F+1) or ((b-F) in res['Uinf'])
        meta.append((r,tuple(a),b,pred))
    ntest+=1
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
err=sum(1 for (m,o) in zip(meta,out) if m[3]!=(o=='1'))
print('instances',ntest,'checks',len(meta),'errors',err)
for (m,o) in zip(meta,out):
    if m[3]!=(o=='1'): print(m,o); break
