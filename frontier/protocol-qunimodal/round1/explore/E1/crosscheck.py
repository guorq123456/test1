# Cross-check prior rule against ground-truth checker /tmp/claude-0/qu/tools/uni on whole fit box (r=3, no a_i divisible by 3)
import subprocess
from common import box_instances
lines=[];pred=[]
for a in box_instances():
    S=sum(1 for x in a if x%3==2); F=sum(x//3 for x in a)
    for b in range(1,61):
        lines.append("3 %d %s %d"%(len(a)," ".join(map(str,a)),b)); pred.append(1 if b<=F+1+2*(S//6) else 0)
out=subprocess.run(["/tmp/claude-0/qu/tools/uni"],input="\n".join(lines)+"\n",capture_output=True,text=True).stdout.split()
assert len(out)==len(lines)
err=sum(1 for o,p in zip(out,pred) if int(o)!=p)
print("instances",len(lines),"errors vs ground truth",err)
