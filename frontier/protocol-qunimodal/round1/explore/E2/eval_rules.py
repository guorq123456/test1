# Evaluate every candidate rule over the FULL fit box (r 2..6, k<=8, a_i<=12, b<=60) against gt.txt.
# For speed, each rule's predicted b-set per (r,a) is computed by calling the rule's own predict() for every b,
# with a cheap pre-filter only for E2_exact: none (all b evaluated). Uses 4 processes.
import sys, importlib
from multiprocessing import Pool
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2/rules')
NAMES=['baseline_conj','E2_exact','E2_threshold','E2_residue','E2_closed_small']
mods={n:importlib.import_module(n) for n in NAMES}
def work(line):
    x=line.split(); r,k=int(x[0]),int(x[1]); a=list(map(int,x[2:2+k])); m=int(x[2+k],16)
    out={}
    for n,M in mods.items():
        dom=M.domain(r,a)
        if not dom: out[n]=(0,0); continue
        err=0
        for b in range(1,61):
            if bool(M.predict(r,a,b)) != bool((m>>(b-1))&1): err+=1
        out[n]=(60,err)
    return (r,k,out)
if __name__=='__main__':
    lines=open('/tmp/claude-0/qu/explore/E2/gt.txt').read().split('\n')[:-1]
    with Pool(4) as P:
        res=P.map(work, lines, chunksize=2000)
    tot={n:[0,0] for n in NAMES}; byr={}
    for r,k,out in res:
        for n,(c,e) in out.items():
            tot[n][0]+=c; tot[n][1]+=e
            s=byr.setdefault((n,r),[0,0]); s[0]+=c; s[1]+=e
    for n in NAMES:
        print(n,"instances_in_domain",tot[n][0],"errors",tot[n][1], " by r:",[(r,byr[(n,r)][1]) for r in range(2,7)])
