# random families (r,block) in the fit box; compare exact vs closed form at every k=m*len(block)<=140
import random, sys
from uinf import uinf
from rule_asym import asym_tops
from boxcheck import allowed
seed=int(sys.argv[1]); nfam=int(sys.argv[2]); rmin=int(sys.argv[3]); rmax=int(sys.argv[4])
random.seed(seed)
tot=0; errE=0; erro=0; erre=0; bad=[]
for f in range(nfam):
    r=random.randint(rmin,rmax); p=random.randint(1,5)
    block=[random.randint(1,r-1) for _ in range(p)]
    if not any(2<=x<=r-2 for x in block): continue
    for m in range(1,140//p+1):
        s=block*m; k=len(s)
        if k<3 or not allowed(r,s): continue
        ex=uinf(r,s); Xo,Xe,eo,ee=asym_tops(r,s)
        tot+=1
        a=(ex['e_odd']!=eo); b=(ex['e_even']!=ee)
        erro+=a; erre+=b; errE+=a
        if a or b: bad.append((r,block,k,ex['e_odd'],eo,round(Xo,4),ex['e_even'],ee,round(Xe,4)))
print('seed',seed,'r',rmin,rmax,'points',tot,'E-err',errE,'eodd-err',erro,'eeven-err',erre)
for x in bad[:40]: print(x)
