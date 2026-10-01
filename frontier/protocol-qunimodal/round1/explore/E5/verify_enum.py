# cross-check enum output with ground-truth checker on random sample
import random, subprocess
random.seed(1)
lines=[]
for r in range(2,7):
    L=open(f'data_r{r}.txt').read().split('\n'); L=[l for l in L if l]
    lines+=random.sample(L,min(400,len(L)))
qs=[];exp=[]
for l in lines:
    x=list(map(int,l.split())); r,k=x[0],x[1]; a=x[2:2+k]; m=x[2+k]
    for b in random.sample(range(1,61),6):
        qs.append(f"{r} {k} {' '.join(map(str,a))} {b}"); exp.append((m>>(b-1))&1)
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(qs)+'\n',capture_output=True,text=True).stdout.split()
bad=sum(int(o)!=e for o,e in zip(out,exp))
print("checked",len(qs),"mismatches",bad)
