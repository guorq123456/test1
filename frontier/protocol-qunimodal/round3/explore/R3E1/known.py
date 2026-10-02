"""Witness test on the three known pair-local-failure instances (r=8595, 12552, 15167)."""
from winx import InstX
from survey2 import witnesses
for f in ["r8595","r12552","r15167_Fodd"]:
    v=open("/tmp/claude-0/qu/synth/r2/inst_ki_fail_%s.txt"%f).read().split()
    r=int(v[1]); a=sorted(map(int,v[2:]))
    print(f,*witnesses(InstX(r,a)),flush=True)
