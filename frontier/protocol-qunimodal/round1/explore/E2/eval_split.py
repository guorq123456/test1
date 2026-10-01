# False-positive / false-negative split over the full fit box (FP: predicts unimodal but is not)
import sys, importlib
from multiprocessing import Pool
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2/rules')
NAMES=sys.argv[1].split(',')
mods={n:importlib.import_module(n) for n in NAMES}
def work(line):
    x=line.split(); r,k=int(x[0]),int(x[1]); a=list(map(int,x[2:2+k])); m=int(x[2+k],16)
    out={}
    for n,M in mods.items():
        fp=fn=0
        if M.domain(r,a):
            for b in range(1,61):
                p=bool(M.predict(r,a,b)); t=bool((m>>(b-1))&1)
                if p and not t: fp+=1
                if t and not p: fn+=1
        out[n]=(fp,fn)
    return out
if __name__=='__main__':
    lines=open('/tmp/claude-0/qu/explore/E2/gt.txt').read().split('\n')[:-1]
    with Pool(4) as P: res=P.map(work, lines, chunksize=2000)
    for n in NAMES:
        print(n,"FP",sum(o[n][0] for o in res),"FN",sum(o[n][1] for o in res))
