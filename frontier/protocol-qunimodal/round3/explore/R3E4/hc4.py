# Hill-climb to MINIMIZE kappa = ln(y_{N*}/y_{N*+2}) at the binding pair (model: S2 can fail only if kappa < ~1),
# subject to N*>=5 (resolved geometry). Records obj2 too.
import sys,random,json,time,math; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpv import fast
r=int(sys.argv[1]); k=int(sys.argv[2]); seed=int(sys.argv[3]); amax=int(sys.argv[4]); secs=float(sys.argv[5])
random.seed(seed)
def obj(a):
    x=fast(r,a)
    if x is None or x['Nstar']>=10**8 or x['Nstar']<5 or 'kappa' not in x: return -99,x
    return -x['kappa'],x
while True:
    a=[random.randint(2,amax) for _ in range(k)]
    if all(v%r for v in a):
        cur,cx=obj(a)
        if cur>-99: break
best=cur; T=0.1
log=open(f'/tmp/claude-0/qu/explore3/R3E4/hc4_{r}_{k}_{seed}_{amax}.jsonl','w')
t0=time.time(); it=0
while time.time()-t0<secs:
    it+=1; b=list(a); m=random.random()
    if m<0.7:
        i=random.randrange(len(b)); b[i]+=random.choice([-1,1])*random.choice([1,3,r//100+1,r//20+1,r//5])
    elif m<0.85: b[random.randrange(len(b))]=random.randint(2,amax)
    elif m<0.93 and len(b)>4: b.pop(random.randrange(len(b)))
    else: b.append(random.randint(2,amax))
    if not all(1<=v<=amax and v%r for v in b) or sum(v-1 for v in b)>2_000_000: continue
    v,x=obj(b)
    if v==-99: continue
    if v>=cur or random.random()<math.exp((v-cur)/T):
        a=b; cur=v
        if not x['S2']: log.write(json.dumps(dict(S2FAIL=True,a=sorted(b)))+'\n'); log.flush()
        if v>best:
            best=v; log.write(json.dumps(dict(it=it,kappa=-v,obj2=x['umin']-x['Nstar'],gap=x['gap'],Nstar=x['Nstar'],beta=x['beta'],F=x['F'],a=sorted(b)))+'\n'); log.flush()
print(r,k,seed,amax,'iters',it,'best kappa',-best)
