import sys,time; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpair import levels
for f in ['inst_ki_fail_r8595.txt','inst_ki_fail_r12552.txt','inst_ki_fail_r15167_Fodd.txt','inst_ki_fail.txt']:
    x=list(map(int,open('/tmp/claude-0/qu/synth/r2/'+f).read().split()))
    W,r,a=x[0],x[1],x[2:]
    res=levels(r,a); info=res.pop('info'); print(f,res)
