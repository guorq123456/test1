# compare exact vs variants A,B,C on random families in the box (same generator as sweep.py)
import random, sys
from uinf import uinf
from rule_asym import asym_tops
from variants import tops_B, tops_C
from boxcheck import allowed
seed=int(sys.argv[1]); nfam=int(sys.argv[2]); rmin=int(sys.argv[3]); rmax=int(sys.argv[4]); useC=len(sys.argv)>5
random.seed(seed)
tot=0; err={'A':[0,0],'B':[0,0],'C':[0,0]}; bad=[]
for f in range(nfam):
    r=random.randint(rmin,rmax); p=random.randint(1,5)
    block=[random.randint(1,r-1) for _ in range(p)]
    if not any(2<=x<=r-2 for x in block): continue
    for m in range(1,140//p+1):
        s=block*m; k=len(s)
        if k<3 or not allowed(r,s): continue
        ex=uinf(r,s); tot+=1
        for name,fn in (('A',asym_tops),('B',tops_B))+((('C',tops_C),) if useC else ()):
            Xo,Xe,eo,ee=fn(r,s)
            err[name][0]+=(ex['e_odd']!=eo); err[name][1]+=(ex['e_even']!=ee)
            if name=='B' and (ex['e_odd']!=eo or ex['e_even']!=ee): bad.append((r,block,k,ex['e_odd'],eo,round(Xo,4),ex['e_even'],ee,round(Xe,4)))
print('seed',seed,'r',rmin,rmax,'points',tot,'errors(odd,even):',err)
for x in bad[:30]: print('B-miss',x)
