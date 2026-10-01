# Holdout as full b-profiles: for each tuple (r,a), unimodality for every b in 1..Bmax, Bmax = D//r + 6
import random, json, subprocess, sys
rnd=random.Random(int(sys.argv[1])); out=sys.argv[2]; S=json.loads(sys.argv[3])
tuples=[]
for stratum,cfg in S.items():
    for _ in range(cfg['n']):
        r=rnd.choice(cfg['r']); k=rnd.randint(*cfg['k']); lo,hi=cfg['a']; kind=cfg.get('kind','random')
        pick=lambda: rnd.randint(lo,hi)
        if kind=='coprime':
            a=[]
            while len(a)<k:
                x=pick()
                if x%r: a.append(x)
        elif kind=='random': a=[pick() for _ in range(k)]
        elif kind=='equal':
            x=pick()
            while x%r==0: x=pick()
            a=[x]*k
        elif kind=='two':
            u=pick(); v=pick()
            while u%r==0: u=pick()
            while v%r==0: v=pick()
            a=[rnd.choice((u,v)) for _ in range(k)]
        elif kind=='ones':
            m=[]
            while len(m)<rnd.randint(1,4):
                x=pick()
                if x%r: m.append(x)
            a=[1]*rnd.randint(1,k)+m
        elif kind=='multiple':
            a=[]
            while len(a)<k-1:
                x=pick()
                if x%r: a.append(x)
            a.append(r*rnd.randint(1,max(1,hi//r)))
        tuples.append((stratum,r,sorted(a)))
lines=[];idx=[]
for ti,(s,r,a) in enumerate(tuples):
    D=sum(x-1 for x in a); B=D//r+6
    for b in range(1,B+1): lines.append(f"{r} {len(a)} {' '.join(map(str,a))} {b}\n"); idx.append(ti)
res=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=''.join(lines),capture_output=True,text=True).stdout.split()
prof=[[] for _ in tuples]
for ti,u in zip(idx,res): prof[ti].append(u=='1')
from collections import Counter
st=Counter(); nonmono=0
with open(out,'w') as f:
    for (s,r,a),p in zip(tuples,prof):
        f.write(json.dumps({'stratum':s,'r':r,'a':a,'profile':p})+'\n')
        st[(s,'inst')]+=len(p); st[(s,'nonuni')]+=p.count(False)
        # non-monotone in b?
        seen_false=False
        for u in p:
            if not u: seen_false=True
            elif seen_false: nonmono+=1; break
print('tuples',len(tuples),'instances',len(res),'tuples non-monotone in b:',nonmono)
for s in S: print(f"{s:12s} instances {st[(s,'inst')]:7d} non-unimodal {st[(s,'nonuni')]:7d}")
