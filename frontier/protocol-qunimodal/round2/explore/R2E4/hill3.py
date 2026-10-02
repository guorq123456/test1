# Hill climbing on the descent-count monotonicity relations (stronger than S2):
#  M2: nneg(b) >= nneg(b-2);  P1: nneg(b+1) <= nneg(b) for b-1-F odd.
# score = min( min_b [nneg(b)-nneg(b-2)] over b with nneg(b-2)>0 , min_{b odd-type, nneg(b)>0} [nneg(b)-nneg(b+1)] )
# negative score = relation broken (reported); S2 violation reported as VIOL. Lower is better.
# usage: hill3.py seed restarts iters rlist kmax amax
import sys,random,json,subprocess
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E4')
from hill2 import valid,mutate
P=subprocess.Popen(['/tmp/claude-0/qu/explore2/R2E4/s2big'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,env={'NNEG':'1'})
def ev(r,a):
    P.stdin.write(f"{r} {len(a)} {' '.join(map(str,a))}\n"); P.stdin.flush()
    line=P.stdout.readline(); rest=line.split('|')[1].split()
    F,T6,Bs,shape,par=map(int,rest[:5]); nn=[int(x) for x in rest[6].strip(',').split(',')]
    if 'VIOL' in line: return -1e9,line.strip()
    N={F+1+j:v for j,v in enumerate(nn)}
    for b in range(max(1,F-1),F+1): N[b]=0
    m2=min((N[b]-N[b-2] for b in N if b-2 in N and N[b-2]>0),default=99)
    p1=min((N[b]-N[b+1] for b in N if b>F and (b-1-F)%2==1 and b+1 in N and N[b]>0),default=99)
    return min(m2,p1)-0.001*(T6-F),line.strip()
if __name__=='__main__':
    seed=int(sys.argv[1]); R=int(sys.argv[2]); iters=int(sys.argv[3]); rlist=[int(x) for x in sys.argv[4].split(',')]; kmax=int(sys.argv[5]); amax=int(sys.argv[6])
    rng=random.Random(seed); tot=0; allbest=[]; broken=[]
    for rs in range(R):
        r=rng.choice(rlist)
        while True:
            k=rng.randint(3,kmax); a=sorted(rng.randint(1,amax) for _ in range(k))
            if valid(r,a,kmax,amax): break
        sc,ln=ev(r,a); best=(sc,ln); tot+=1
        for it in range(iters):
            b=mutate(r,a,rng,amax)
            if not valid(r,b,kmax,amax): continue
            s2,l2=ev(r,b); tot+=1
            if s2<-1: print('VIOL',l2,flush=True)
            if s2<-0.5 and len(broken)<20: broken.append(l2)
            if s2<=sc or rng.random()<0.03: a,sc=b,s2
            if s2<best[0]: best=(s2,l2)
        allbest.append(best)
    allbest.sort()
    print(json.dumps(dict(seed=seed,evals=tot,nbroken=len(broken),broken=[x[:250] for x in broken[:5]],best=[(s,l[:250]) for s,l in allbest[:5]])))
