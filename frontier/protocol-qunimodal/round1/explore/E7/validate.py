# validate scan output against ground-truth checker /tmp/claude-0/qu/tools/uni on a random sample
import random, subprocess
random.seed(1)
lines=open('/tmp/claude-0/qu/explore/E7/tuples.txt').read().split('\n')[:-1]
sample=random.sample(lines,3000)
inp=[];exp=[]
for L in sample:
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=x[2:2+k]; m=x[2+k]
    for b in random.sample(range(1,61),5):
        aa=a if a else [1]
        inp.append(f"{r} {len(aa)} {' '.join(map(str,aa))} {b}")
        exp.append((m>>(b-1))&1)
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(inp)+'\n',capture_output=True,text=True).stdout.split()
bad=sum(int(o)!=e for o,e in zip(out,exp))
print("checked",len(exp),"mismatches",bad)
