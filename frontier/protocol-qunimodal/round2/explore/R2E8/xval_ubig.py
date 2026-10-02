# Cross-validate ubig (256-bit) against tools/gt_big.py (exact Python big ints) and rule_H1.bstar.
import random,sys,subprocess
sys.path.insert(0,'/tmp/claude-0/qu/tools'); sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
import gt_big, rule_H1
from core import stats
random.seed(int(sys.argv[1])); insts=[]; lines=[]
for _ in range(int(sys.argv[2])):
    r=random.randint(2,30); k=random.randint(1,40)
    a=sorted(random.randint(1,random.choice([5,12,30])) for _ in range(k))
    if any(x%r==0 for x in a): continue
    insts.append((r,a)); lines.append(f"{r} {k} "+' '.join(map(str,a)))
out=subprocess.run(['./ubig'],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd='/tmp/claude-0/qu/explore2/R2E8').stdout.strip().split('\n')
bad=0; big=0; ovf=0
for (r,a),o in zip(insts,out):
    if o=='OVERFLOW': ovf+=1; continue
    T6,F,Bh,bits=o.split(); T6=int(T6)
    prod=1
    for x in a: prod*=x
    if prod>=2**127: big+=1
    prof=gt_big.profile(r,a,list(range(1,T6+4)))
    ub=''.join('1' if u else '0' for u in prof)
    if ub!=bits or int(Bh)!=rule_H1.bstar(r,a) or T6!=stats(r,a)[4]: bad+=1
print("n",len(insts),"overflow-skipped",ovf,"with prod>=2^127",big,"bad",bad)
