# Evaluate additional candidate rules over the full fit box against gt.txt (same protocol as eval_rules.py)
import sys, importlib
from multiprocessing import Pool
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2/rules')
NAMES=sys.argv[1].split(',')
mods={n:importlib.import_module(n) for n in NAMES}
def work(line):
    x=line.split(); r,k=int(x[0]),int(x[1]); a=list(map(int,x[2:2+k])); m=int(x[2+k],16)
    out={}
    for n,M in mods.items():
        if not M.domain(r,a): out[n]=(0,0); continue
        err=sum(1 for b in range(1,61) if bool(M.predict(r,a,b)) != bool((m>>(b-1))&1))
        out[n]=(60,err)
    return (r,k,out)
if __name__=='__main__':
    lines=open('/tmp/claude-0/qu/explore/E2/gt.txt').read().split('\n')[:-1]
    with Pool(4) as P: res=P.map(work, lines, chunksize=2000)
    for n in NAMES:
        c=sum(o[n][0] for _,_,o in res); e=sum(o[n][1] for _,_,o in res)
        byr=[(r,sum(o[n][1] for rr,_,o in res if rr==r)) for r in range(2,7)]
        byk=[(k,sum(o[n][1] for _,kk,o in res if kk==k)) for k in range(1,9)]
        print(n,"instances_in_domain",c,"errors",e,"by r",byr,"by k",byk)
