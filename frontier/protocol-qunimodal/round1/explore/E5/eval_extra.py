# random in-box instances INCLUDING a_i=1 and a_i divisible by r; ground truth from tools/uni
import random, subprocess, importlib.util, sys
random.seed(11)
inst=[]
for _ in range(20000):
    r=random.randint(2,6); k=random.randint(1,8)
    a=sorted(random.choice([1,1,random.randint(1,12)]) if random.random()<0.3 else random.randint(1,12) for _ in range(k))
    b=random.randint(1,25) if random.random()<0.8 else random.randint(1,60)
    inst.append((r,a,b))
# extra: all-ones and near-trivial
for r in range(2,7):
    for k in range(1,9):
        for b in range(1,8): inst.append((r,[1]*k,b)); inst.append((r,[1]*(k-1)+[2],b))
inp='\n'.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}" for r,a,b in inst)+'\n'
gt=list(map(int,subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=inp,capture_output=True,text=True).stdout.split()))
for f in sys.argv[1:]:
    spec=importlib.util.spec_from_file_location("rule",f); R=importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
    err=0;n=0;ex=[]
    for (r,a,b),g in zip(inst,gt):
        if not R.domain(r,a): continue
        n+=1
        if bool(R.predict(r,a,b))!=bool(g): err+=1; ex.append((r,a,b,g))
    print(f,"instances",n,"errors",err,ex[:5])
