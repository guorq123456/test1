# Cross-check the Python rule files against the ground-truth checker on a random sample of the fit box
# (includes a_i=1 entries and multiples of r), plus all 85 non-monotone instances and their b+1 neighbours.
import random, subprocess, sys
sys.path.insert(0,'/tmp/claude-0/qu/explore/E7/rules')
import rule_exact, rule_threshold, rule_conj
random.seed(7)
inst=[]
for _ in range(20000):
    r=random.randint(2,6); k=random.randint(1,8)
    a=sorted(random.randint(1,12) for _ in range(k)); b=random.randint(1,60)
    inst.append((r,a,b))
import re
for L in open('/tmp/claude-0/qu/explore/E7/nonmono.txt'):
    m=re.match(r'r=(\d+) a=\[(.*)\] first_fail_b=(\d+)',L)
    r=int(m.group(1)); a=list(map(int,m.group(2).split(','))); b0=int(m.group(3))
    for b in (b0-1,b0,b0+1,b0+2): inst.append((r,a,b))
inp='\n'.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}" for r,a,b in inst)+'\n'
truth=list(map(int,subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=inp,capture_output=True,text=True).stdout.split()))
for name,mod in [('EXACT',rule_exact),('THRESH',rule_threshold),('CONJ',rule_conj)]:
    e=sum(int(mod.predict(r,a,b))!=t for (r,a,b),t in zip(inst,truth))
    print(name,"errors",e,"of",len(inst))
