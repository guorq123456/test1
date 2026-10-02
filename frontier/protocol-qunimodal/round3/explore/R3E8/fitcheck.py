# Instance-level check of rule_asym.predict and rule_B.predict vs ground truth /tmp/claude-0/qu/tools/uni
# (ground truth: exact big-integer /tmp/claude-0/qu/tools/gt_big.py)
# on random in-box instances inside domain (large parts, a_i<=400), all b in [1, F+T+3].
import random, subprocess, sys
import rule_asym, rule_B
from boxcheck import allowed
seed=int(sys.argv[1]); N=int(sys.argv[2]); random.seed(seed)
RMIN,RMAX=(int(sys.argv[3]),int(sys.argv[4])) if len(sys.argv)>4 else (4,40)
lines=[]; meta=[]; ni=0; tries=0
while ni<N and tries<10**6:
    tries+=1
    r=random.randint(RMIN,RMAX); k=random.randint(3,40)
    s=[random.randint(1,r-1) for _ in range(k)]
    if not any(2<=x<=r-2 for x in s) or not allowed(r,s): continue
    S=sum(s); L0=max(1,(S-k+3-r)//2)
    q0=(L0+r-1)//r
    a=sorted(q*r+x for x in s for q in [random.randint(q0,q0+1)])
    a=sorted(v if v>=L0 else v+r for v in a)
    if max(a)>400 or not rule_asym.domain(r,a) or sum(a)>4000: continue
    F=sum(v//r for v in a); T=1+(S-k+1)//r
    for b in range(1,F+T+4):
        lines.append(f"{r} {k} {' '.join(map(str,a))} {b}"); meta.append((r,a,b))
    ni+=1
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import profile
out=[]; cur=None
groups={}
for (r,a,b) in meta: groups.setdefault((r,tuple(a)),[]).append(b)
gt={}
for (r,a),bs in groups.items():
    for b,v in zip(bs,profile(r,list(a),bs)): gt[(r,a,b)]=v
out=['1' if gt[(r,tuple(a),b)] else '0' for (r,a,b) in meta]
eA=eB=0; badk={}
for (r,a,b),o in zip(meta,out):
    g=(o=='1')
    pa=rule_asym.predict(r,a,b); pb=rule_B.predict(r,a,b)
    if pa!=g: eA+=1
    if pb!=g: eB+=1; badk[len(a)]=badk.get(len(a),0)+1
print('seed',seed,'instances',ni,'checks',len(meta),'errA',eA,'errB',eB,'B-errors by k',sorted(badk.items()))
