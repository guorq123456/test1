# Survey of gap = umin - vmin (index units; S2 failure needs gap>=4) over families at r>=1000.
import sys,random,json,time; sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E4')
from fpv import fast
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 1)
out=open('/tmp/claude-0/qu/explore3/R3E4/survey1.jsonl','a')
def gen():
    fam=random.choice(['unif','conc','lift','mixpm1','smallparts','bimodal'])
    r=random.choice([1000,1500,2000,3000,5000,8000,12000])
    if fam=='unif':
        k=random.choice([5,8,12,20,40,80]); a=[random.randint(2,r-2) for _ in range(k)]
    elif fam=='conc':
        k=random.choice([5,8,12,20,40,80,150]); s0=random.uniform(0.03,0.97); sp=random.choice([0,0.002,0.01,0.05])
        a=[min(r-2,max(2,int(r*(s0+random.uniform(-sp,sp))))) for _ in range(k)]
    elif fam=='lift':
        k=random.choice([5,8,12,20,40]); s0=random.uniform(0.03,0.97); sp=random.choice([0.002,0.01,0.05,0.3])
        a=[min(r-2,max(2,int(r*(s0+random.uniform(-sp,sp)))))+r*random.randint(1,2) for _ in range(k)]
    elif fam=='mixpm1':
        km=random.randint(4,12); kp=random.choice([5,20,60])
        a=[random.randint(2,r-2) for _ in range(km)]+[random.choice([1,r-1,r+1,2*r-1]) for _ in range(kp)]
    elif fam=='smallparts':
        s=random.choice([2,3,4,5,7,10,20]); m=int(random.uniform(0.2,3)*(r/s)**2/ (s*s/4) )
        m=max(4,min(m,3000)); a=[s]*m
    else:
        k1=random.randint(2,30); k2=random.randint(2,30); s1=random.uniform(0.02,0.98); s2=random.uniform(0.02,0.98)
        a=[max(2,min(r-2,int(r*s1)+random.randint(-3,3))) for _ in range(k1)]+[max(2,min(r-2,int(r*s2)+random.randint(-3,3))) for _ in range(k2)]
    a=[x for x in a if x%r!=0]
    return fam,r,sorted(a)
t0=time.time()
while time.time()-t0<float(sys.argv[2]) if len(sys.argv)>2 else 600:
    fam,r,a=gen()
    if sum(x-1 for x in a)>3_000_000 or len(a)<4: continue
    try: res=fast(r,a)
    except Exception as e: continue
    if res is None or res['Nstar']>=10**8: continue
    res['fam']=fam; res['a']=a
    out.write(json.dumps(res)+'\n'); out.flush()
