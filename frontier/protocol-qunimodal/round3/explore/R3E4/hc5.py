# Hill-climb (with mild annealing) on gap=umin-vmin (S2 failure needs gap>=4) for fixed r.
import sys,random,json,time,math; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpv import fast, margin
r=int(sys.argv[1]); k=int(sys.argv[2]); seed=int(sys.argv[3]); init=sys.argv[4]; secs=float(sys.argv[5])
amax=int(sys.argv[6]) if len(sys.argv)>6 else 3*r
random.seed(seed)
def ok(a): return all(x%r!=0 and 1<=x<=amax for x in a)
def init_a():
    if init=='unif': return [random.randint(2,min(amax,r-2)) for _ in range(k)]
    if init=='conc':
        s0=random.uniform(0.05,0.95); return [max(2,int(r*s0)+random.randint(-r//50,r//50)) for _ in range(k)]
    if init=='lift':
        return [random.randint(2,r-2)+r*random.randint(1,max(1,amax//r-1)) for _ in range(k)]
    if init=='wide': return [random.randint(2,amax) for _ in range(k)]
def obj(a):
    try: m,x=margin(r,a)
    except Exception: return -1e9,None
    if m is None: return -1e9,None
    return m,x
a=init_a()
while not ok(a): a=init_a()
cur,cx=obj(a); best=cur; bestx=cx; besta=list(a)
t0=time.time(); it=0; T=0.3
log=open(f'/tmp/claude-0/qu/explore3/R3E4/hc5_{r}_{k}_{seed}_{init}.jsonl','w')
while time.time()-t0<secs:
    it+=1
    b=list(a); m=random.random()
    if m<0.6:
        i=random.randrange(len(b)); b[i]+=random.choice([-1,1])*random.choice([1,1,2,3,5,max(1,r//200),max(1,r//50),max(1,r//10)])
    elif m<0.8:
        i=random.randrange(len(b)); b[i]=random.randint(2,amax)
    elif m<0.9 and len(b)>4: b.pop(random.randrange(len(b)))
    else: b.append(random.choice(b)+random.randint(-3,3))
    if not ok(b) or sum(x-1 for x in b)>4_000_000: continue
    v,x=obj(b)
    if v<=-1e9: continue
    if v>=cur or random.random()<math.exp((v-cur)/T):
        a=b; cur=v; cx=x
        if v>best:
            best=v; bestx=x; besta=sorted(b)
            log.write(json.dumps(dict(it=it,margin=v,obj2=x['umin']-x['Nstar'],gap=x['gap'],Nstar=x['Nstar'],beta=x['beta'],F=x['F'],kappa=x.get('kappa'),Cv=x['Cv'],Cu=x['Cu'],a=besta))+'\n'); log.flush()
        if not x['S2']:
            log.write(json.dumps(dict(S2FAIL=True,a=sorted(b),x={kk:vv for kk,vv in x.items()}))+'\n'); log.flush()
print(r,k,seed,init,'iters',it,'best',best,bestx['Nstar'],bestx['beta'],bestx.get('kappa'),len(besta))
