# Hill climbing toward an S2 violation using exact evaluator s2big (NNEG mode).
# usage: hill2.py seed n_restarts iters rlist(comma) kmax amax
# score = -1 if S2 violated; else min over flips b in (B*,T6] that would violate S2 if b joined U
#   (all such b except B*+2 when U is an interval) of nneg(b) = #descents of P in first half; minus 0.001*(T6-F).
import sys,random,json,subprocess,os
MODE=os.environ.get('MODE','A')  # A: all violating flips; B: exclude the parity flip b=B*+1
P=subprocess.Popen(['/tmp/claude-0/qu/explore2/R2E4/s2big'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,env={'NNEG':'1'})
def ev(r,a):
    P.stdin.write(f"{r} {len(a)} {' '.join(map(str,a))}\n"); P.stdin.flush()
    line=P.stdout.readline()
    rest=line.split('|')[1].split()
    F,T6,Bs,shape,par=map(int,rest[:5]); pat=rest[5]; nn=[int(x) for x in rest[6].strip(',').split(',')]
    viol='VIOL' in line
    if viol: return -1.0,line.strip()
    cand=[b for b in range(Bs+1,T6+1) if not(shape==0 and b==Bs+2) and not (MODE=='B' and b==Bs+1)]
    s=min((nn[b-F-1] for b in cand),default=1e6)
    return s-0.001*(T6-F),line.strip()
def valid(r,a,kmax,amax):
    return 3<=len(a)<=kmax and all(1<=x<=amax and x%r for x in a) and sum(1 for x in a if 2<=x%r<=r-2)>=3
def mutate(r,a,rng,amax):
    a=list(a); m=rng.random()
    if m<0.3: i=rng.randrange(len(a)); a[i]+=rng.choice([-1,1])
    elif m<0.45: i=rng.randrange(len(a)); a[i]+=rng.choice([-r,r])
    elif m<0.6: i=rng.randrange(len(a)); a[i]=rng.randint(1,amax)
    elif m<0.7: a.append(rng.choice(a) if rng.random()<0.5 else rng.randint(1,amax))
    elif m<0.8 and len(a)>3: a.pop(rng.randrange(len(a)))
    else:
        i,j=rng.randrange(len(a)),rng.randrange(len(a)); t=rng.choice([1,2,r//2 or 1]); a[i]+=t; a[j]-=t
    return sorted(a)
if __name__=='__main__':
    seed=int(sys.argv[1]); R=int(sys.argv[2]); iters=int(sys.argv[3]); rlist=[int(x) for x in sys.argv[4].split(',')]; kmax=int(sys.argv[5]); amax=int(sys.argv[6])
    rng=random.Random(seed); tot=0; allbest=[]
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
            if s2<0: print('VIOL',l2,flush=True); best=(s2,l2); break
            if s2<=sc or rng.random()<0.03: a,sc=b,s2
            if s2<best[0]: best=(s2,l2)
        allbest.append(best)
        if best[0]<0: break
    allbest.sort()
    print(json.dumps(dict(seed=seed,evals=tot,best=allbest[:5])))
