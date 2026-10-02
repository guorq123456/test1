# Verify witness pairs with ground-truth checker /tmp/claude-0/qu/tools/uni (b=1..T6+2) and print Gamma-level data.
import json, glob, subprocess
from core import inv, U
def gt(r,a,bs):
    lines='\n'.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}" for b in bs)+'\n'
    o=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=lines,capture_output=True,text=True).stdout.split()
    return [b for b,x in zip(bs,o) if x=='1']
n=0; ok=0
for fn in sorted(glob.glob('emb1_*.jsonl')):
    for l in open(fn):
        d=json.loads(l); r=d['r']; a=d['a']; b=d['b']
        _,T6,_=U(r,a)
        ga=gt(r,a,range(1,T6+3)); gb=gt(r,b,range(1,T6+3))
        Da,Fa,ta,Ga=inv(r,a); Db,Fb,tb,Gb=inv(r,b)
        same=(Da,Fa,ta,Ga)==(Db,Fb,tb,Gb) and len(a)==len(b) and sorted(x%r for x in a)==sorted(x%r for x in b)
        n+=1; ok+= (ga==d['Ua'] and gb==d['Ub'] and ga!=gb and same)
        print(r,len(a),a,'U=[1..%d]'%max(ga) if ga==list(range(1,max(ga)+1)) else ga,'|',b,'U=[1..%d]'%max(gb) if gb==list(range(1,max(gb)+1)) else gb,'D',Da,'F',Fa,'sameGamma',same)
print('pairs',n,'verified',ok)
