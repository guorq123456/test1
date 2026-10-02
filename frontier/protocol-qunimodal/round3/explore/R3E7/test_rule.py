# test rule_stab: (1) domain <=> stable(a) [Q2 conjecture], (2) predict vs ground truth uni for a in domain. fit box only.
import sys, random, subprocess
from core import *
import rule_stab, math
sys.path.insert(0,'/tmp/claude-0/qu/tools'); import gt_big
bigmeta=[]; bigerr=0
random.seed(int(sys.argv[1])); n=int(sys.argv[2]); rmax=int(sys.argv[3]); kmax=int(sys.argv[4]); amax=int(sys.argv[5])
lines=[]; meta=[]; q2bad=0; cnt=0; dom=0
while cnt<n:
    r=random.randint(3,rmax); k=random.randint(2,kmax)
    u=random.random()
    if u<0.3: s=[random.randint(1,r-1) for _ in range(k)]
    elif u<0.6:
        c=random.randint(1,r-1); s=[min(r-1,max(1,c+random.randint(-1,1))) for _ in range(k)]
    else:
        vals=random.sample(range(1,r),min(r-1,random.randint(2,4))); s=[random.choice(vals) for _ in range(k)]
    pz=random.random()
    a=sorted(x + r*(0 if random.random()<pz else random.randint(1,max(1,(amax-x)//r))) for x in s)
    if min(a)<2 or not in_box(r,a): continue
    R=Res(r,[x%r for x in a]); cnt+=1
    d=rule_stab.domain(r,a); st=R.stable(a)
    if d!=st: q2bad+=1
    if d:
        dom+=1
        F=sum(x//r for x in a)
        if sum(math.log2(x) for x in a)>120:
            if len(bigmeta)<300 and max(a)*k<6000:
                bs=list(range(1,F+R.T+3)); prof=gt_big.profile(r,a,bs)
                for b,t in zip(bs,prof):
                    bigmeta.append(1)
                    if t!=rule_stab.predict(r,a,b): bigerr+=1
        elif len(lines)<20000:
            for b in range(1,F+R.T+3):
                lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); meta.append(rule_stab.predict(r,a,b))
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
err=sum(1 for p,o in zip(meta,out) if p!=(o=='1'))
print("bigcheck (a,b)",len(bigmeta),"big errors",bigerr); print("instances",cnt,"in domain",dom,"domain!=stable(exact window)",q2bad,"uni-checked (a,b)",len(meta),"predict errors",err)
