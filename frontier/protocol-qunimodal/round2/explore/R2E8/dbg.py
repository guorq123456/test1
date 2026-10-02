import random,sys,subprocess
sys.path.insert(0,'/tmp/claude-0/qu/tools'); sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
import gt_big, rule_H1
from core import stats
random.seed(1); 
for _ in range(600):
    r=random.randint(2,30); k=random.randint(1,40)
    a=sorted(random.randint(1,random.choice([5,12,30])) for _ in range(k))
    if any(x%r==0 for x in a): continue
    o=subprocess.run(['./ubig'],input=f"{r} {k} "+' '.join(map(str,a))+'\n',capture_output=True,text=True).stdout.split()
    T6=int(o[0]); prof=''.join('1' if u else '0' for u in gt_big.profile(r,a,list(range(1,T6+4))))
    if prof!=o[3] or int(o[2])!=rule_H1.bstar(r,a) or T6!=stats(r,a)[4]:
        print(r,a,o,prof,rule_H1.bstar(r,a),stats(r,a)[4]); break
