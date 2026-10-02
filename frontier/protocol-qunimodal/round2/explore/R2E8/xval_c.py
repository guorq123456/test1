# cross-validate ufast (U bits and H1 prediction) against core.Uset and rule_H1.bstar on random instances
import random,sys,subprocess
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *; import rule_H1
random.seed(5); lines=[]; insts=[]
for _ in range(3000):
    r=random.randint(2,20); a=sorted(random.randint(1,40) for _ in range(random.randint(1,6)))
    if any(x%r==0 for x in a): continue
    insts.append((r,a)); lines.append(f"{r} {len(a)} "+' '.join(map(str,a)))
out=subprocess.run(['./ufast'],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd='/tmp/claude-0/qu/explore2/R2E8').stdout.strip().split('\n')
bad=0
for (r,a),o in zip(insts,out):
    T6,F,Bh,bits=o.split(); T6=int(T6)
    U=Uset(r,a,T6+3); ub=''.join('1' if b in U else '0' for b in range(1,T6+4))
    if ub!=bits or int(Bh)!=rule_H1.bstar(r,a): bad+=1
print("n",len(insts),"bad",bad)
