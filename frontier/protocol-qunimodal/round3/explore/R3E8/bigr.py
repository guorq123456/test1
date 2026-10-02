# r>=1000 families: exact chain tops vs variants A,B (and C if asked), k = m*len(block), m in range(m0,m1,step)
import sys, time
from uinf import uinf
from rule_asym import asym_tops
from variants import tops_B, tops_C
r=int(sys.argv[1]); m0,m1,st=map(int,sys.argv[2].split(',')); useC=sys.argv[3]=='C'; block=list(map(int,sys.argv[4:]))
assert r>=1000
err={'A':[0,0],'B':[0,0],'C':[0,0]}; n=0
for m in range(m0,m1,st):
    s=block*m; k=len(s)
    if k<3: continue
    t0=time.time(); ex=uinf(r,s); n+=1
    row=[k,ex['e_odd'],ex['e_even'],ex['T']]
    for name,fn in (('A',asym_tops),('B',tops_B))+((('C',tops_C),) if useC else ()):
        Xo,Xe,eo,ee=fn(r,s)
        err[name][0]+=(ex['e_odd']!=eo); err[name][1]+=(ex['e_even']!=ee)
        row+=[name,eo,ee]+([round(Xo,4),round(Xe,4)] if Xo is not None else [])
    print(*row,'%.1fs'%(time.time()-t0),flush=True)
print('r',r,'block',block,'points',n,'errors(odd,even)',err)
