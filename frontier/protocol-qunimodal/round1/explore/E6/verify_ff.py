# Verify the first-failing-b ("slack") data of margins.c against the ground-truth checker uni:
# for each multiset with no a_i divisible by r, b=firstfail must be non-unimodal and
# b = bound .. firstfail-1 unimodal. Also prints the slack histogram per r.
import subprocess, sys, collections
r=int(sys.argv[1])
ff=subprocess.run(["./margins",str(r),"dump"],capture_output=True,text=True).stdout.split("\n")
lines=[];expect=[];hist=collections.Counter()
for L in ff:
    if not L.startswith("FF"): continue
    x=list(map(int,L.split()[1:])); R,k=x[0],x[1]; a=x[2:2+k]; f,bd=x[2+k],x[3+k]
    hist[f-bd if f>0 else None]+=1
    for b in range(bd,f+1):
        lines.append(f"{R} {k} {' '.join(map(str,a))} {b}"); expect.append(0 if b==f else 1)
out=subprocess.run(["/tmp/claude-0/qu/tools/uni"],input="\n".join(lines)+"\n",capture_output=True,text=True).stdout.split()
bad=sum(1 for e,o in zip(expect,out) if int(o)!=e)
print(f"r={r} multisets={sum(hist.values())} checked_lines={len(lines)} mismatches={bad} slack_hist={dict(sorted(hist.items(),key=lambda t:(t[0] is None,t[0])))}")
