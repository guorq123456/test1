"""survey3 columns on the three known pair-local failure instances."""
from winx import InstX
from survey3 import row
for f in ["r8595","r12552","r15167_Fodd"]:
    v=open("/tmp/claude-0/qu/synth/r2/inst_ki_fail_%s.txt"%f).read().split()
    print(f,*row(InstX(int(v[1]),sorted(map(int,v[2:])))),flush=True)
