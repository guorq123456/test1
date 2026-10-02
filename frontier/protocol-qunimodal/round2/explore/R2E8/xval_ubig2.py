# Cross-validate ubig on large-product instances (prod a_i >= 2^127): base-like tuples and random big tuples.
import random,sys,subprocess
sys.path.insert(0,'/tmp/claude-0/qu/tools'); sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
import gt_big, rule_H1
random.seed(int(sys.argv[1])); insts=[]; lines=[]
for t in range(int(sys.argv[2])):
    r=random.randint(4,30)
    if t%2==0:
        a=[random.randint(2,r-2) for _ in range(3)]+[r-1]*random.randint(20,37)
    else:
        a=[random.choice([x for x in range(1,101) if x%r]) for _ in range(random.randint(25,40))]
    a=sorted(a); insts.append((r,a)); lines.append(f"{r} {len(a)} "+' '.join(map(str,a)))
out=subprocess.run(['./ubig'],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd='/tmp/claude-0/qu/explore2/R2E8').stdout.strip().split('\n')
bad=0; big=0; ovf=0; n=0
for (r,a),o in zip(insts,out):
    if o=='OVERFLOW': ovf+=1; continue
    T6,F,Bh,bits=o.split(); T6=int(T6); n+=1
    prod=1
    for x in a: prod*=x
    if prod>=2**127: big+=1
    prof=gt_big.profile(r,a,list(range(1,T6+4)))
    ub=''.join('1' if u else '0' for u in prof)
    if ub!=bits: bad+=1; print("BAD",r,a,bits,ub)
print("n",n,"overflow-skipped",ovf,"with prod>=2^127",big,"bad",bad)
