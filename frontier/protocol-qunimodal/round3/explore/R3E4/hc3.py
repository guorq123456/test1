# Hill-climb on residue vectors for small k with fixed lifts (lifted regime), objective obj2=umin-N* (S2 fails iff >=4).
import sys,random,json,time,math; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpv import fast
r=int(sys.argv[1]); k=int(sys.argv[2]); seed=int(sys.argv[3]); L=int(sys.argv[4]); extra=int(sys.argv[5]); secs=float(sys.argv[6])
random.seed(seed)
def build(rho): 
    a=[x+L*r for x in rho]; a[0]+=extra*r; return sorted(a)
def obj(rho):
    x=fast(r,build(rho))
    if x is None or x['Nstar']>=10**8: return -1,None
    return x['umin']-x['Nstar'],x
rho=[random.randint(2,r-2) for _ in range(k)]
cur,cx=obj(rho); best=cur; T=0.05
log=open(f'/tmp/claude-0/qu/explore3/R3E4/hc3_{r}_{k}_{seed}_{L}_{extra}.jsonl','w')
t0=time.time(); it=0
while time.time()-t0<secs:
    it+=1; b=list(rho); i=random.randrange(k)
    if random.random()<0.85: b[i]+=random.choice([-1,1])*random.choice([1,2,5,r//500+1,r//100+1,r//20+1])
    else: b[i]=random.randint(2,r-2)
    if not all(2<=x<=r-2 for x in b): continue
    v,x=obj(b)
    if v<0: continue
    if v>=cur or random.random()<math.exp((v-cur)/T):
        rho=b; cur=v
        if not x['S2']: log.write(json.dumps(dict(S2FAIL=True,a=build(b)))+'\n'); log.flush()
        if v>best:
            best=v; log.write(json.dumps(dict(it=it,obj2=v,gap=x['gap'],Nstar=x['Nstar'],beta=x['beta'],F=x['F'],kappa=x.get('kappa'),Cv=x['Cv'],Cu=x['Cu'],a=build(b)))+'\n'); log.flush()
print(r,k,seed,L,extra,'iters',it,'best',best)
