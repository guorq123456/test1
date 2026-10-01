# y* = max{y in Z : d_y < tau_y}; candidate rule b_max = floor((D+1-2y*)/r)-1 (exact in regime K<=0)
import sys, itertools, random
sys.path.insert(0,'/tmp/claude-0/qu/explore/E2')
from core import *
def ystar(r,a):
    D=sum(x-1 for x in a); tt=tau(r,a)
    if all(v==0 for v in tt): return None
    d=dseq(r,a,D+2+r)
    best=None
    for y in range(-r, D+2):
        dy = d[y] if y>=0 else 0
        if dy < tt[y%r]: best=y
    return best
def bmax_formula(r,a):
    D=sum(x-1 for x in a); y=ystar(r,a)
    if y is None: return 10**9
    return (D+1-2*y)//r - 1
if __name__=='__main__':
    random.seed(2)
    stats={}
    fails=[]
    for r in range(2,7):
        for k in range(1,9):
            combos=list(itertools.combinations_with_replacement(range(1,13),k))
            if len(combos)>1500: combos=random.sample(combos,1500)
            for a in combos:
                a=list(a)
                if any(x%r==0 for x in a): continue
                y=ystar(r,a); bf=bmax_formula(r,a)
                U=[b for b in range(1,61) if truth(r,a,b)]
                bm=max(U) if U else 0
                down = U==list(range(1,bm+1))
                key=(r,k)
                s=stats.setdefault(key,[0,0,0,0])
                s[0]+=1
                if y is not None and y>=0: s[1]+=1
                if not down: s[2]+=1
                if bm!=min(bf,60) or not down: s[3]+=1; fails.append((r,a,y,bf,bm,U[:5] if not down else None))
    for key in sorted(stats): print(key, "n=%d ystar>=0:%d nondown:%d formula_fail:%d"%tuple(stats[key]))
    print(fails[:40])
