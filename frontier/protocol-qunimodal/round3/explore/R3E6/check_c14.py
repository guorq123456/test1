# Check that the (ii) j=0 test is needed: r=25, a=(12,26,33,67,69,99).
import sys; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E6')
src=open('/tmp/claude-0/qu/explore3/R3E6/eval_candidates2.py').read().split('C=[')[0]
exec(src)
import rule_gen as RG
from core import U
r,a=25,[12,26,33,67,69,99]
u,T6,_=U(r,a)
print('U',u,'T6',T6)
print('rule_gen',[b for b in range(1,T6+3) if RG.predict(r,a,b)])
print('C14 noii',[b for b in range(1,T6+3) if gen_noii(r,a,b)])
