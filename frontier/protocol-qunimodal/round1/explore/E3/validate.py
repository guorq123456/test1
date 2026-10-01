# Validate enum.c output against ground-truth checker /tmp/claude-0/qu/tools/uni on a random sample (all inside fit box).
import random, subprocess
random.seed(12345)
recs=[]
for r in range(2,7):
    with open(f'box_r{r}.txt') as f:
        lines=f.readlines()
    for ln in random.sample(lines,4000):
        x=list(map(int,ln.split())); k=x[1]; a=x[2:2+k]; m=x[2+k]
        for b in random.sample(range(1,61),3):
            recs.append((r,k,a,b,(m>>(b-1))&1))
inp=''.join(f"{r} {k} {' '.join(map(str,a))} {b}\n" for r,k,a,b,_ in recs)
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=inp,capture_output=True,text=True).stdout.split()
bad=sum(1 for (rec,o) in zip(recs,out) if int(o)!=rec[4])
print('checked',len(recs),'mismatches',bad, 'unimodal in sample', sum(int(o) for o in out))
