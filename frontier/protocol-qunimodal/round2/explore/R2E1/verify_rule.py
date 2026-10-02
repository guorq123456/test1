# Verify rule_threads.predict against ground truth /tmp/claude-0/qu/tools/uni (inside fit box).
import sys, random, itertools, subprocess
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from rule_threads import predict
from core import in_box
random.seed(17); lines=[]; preds=[]
# exhaustive small
for r in range(2,8):
    for k in range(1,5):
        for a in itertools.combinations_with_replacement(range(1,2*r+2),k):
            for b in range(1,7):
                lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); preds.append(predict(r,list(a),b))
# random larger
for it in range(4000):
    r=random.randint(2,30); k=random.randint(1,12)
    a=sorted(random.randint(1,40) for _ in range(k)); b=random.randint(1,12)
    if not in_box(r,a): continue
    lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); preds.append(predict(r,a,b))
out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
bad=sum(1 for x,p in zip(out,preds) if (x=='1')!=p)
print("cases",len(preds),"mismatches",bad,"positives",sum(preds))
