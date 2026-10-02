# Random structured-family sampler for S2 violations. usage: sampler.py family seed n
# families: two (two distinct values), mid (all middle residues), near (a_i = c*r +- small, plus >=3 middle),
#           comp (r in {12,24,30}, random), wide (random r 4..30, random k<=40, a<=100), equalp (equal plus one perturbed)
import sys,random,json
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E4')
from core import analyze,nmiddle,in_box
def gen(fam,rng):
    if fam=='comp': r=rng.choice([12,24,30])
    else: r=rng.randint(4,30)
    mids=[v for v in range(2,101) if 2<=v%r<=r-2]
    k=rng.randint(3,40)
    if fam=='two':
        x=rng.choice(mids); y=rng.choice([v for v in range(2,101) if v%r and v!=x]); m=rng.randint(3,k) if k>=3 else 3
        a=[x]*m+[y]*(k-m)
    elif fam=='mid':
        a=[rng.choice(mids) for _ in range(k)]
    elif fam=='near':
        m=rng.randint(3,k); a=[rng.choice(mids) for _ in range(m)]
        for _ in range(k-m):
            c=rng.randint(1,100//r) ; e=rng.choice([1,-1,2,-2]); v=c*r+e
            if 1<=v<=100 and v%r: a.append(v)
    elif fam=='equalp':
        x=rng.choice(mids); a=[x]*k; i=rng.randrange(k); a[i]=max(1,min(100,x+rng.choice([-1,1,-r,r,2,-2])))
        if a[i]%r==0: a[i]+=1
    elif fam=='smallmid':  # middle residues only, small values (r..2r range): low D, many b's
        a=[rng.choice([v for v in range(2,min(100,3*r)) if 2<=v%r<=r-2]) for _ in range(k)]
    else:
        a=[]
        while len(a)<k:
            v=rng.randint(2,100)
            if v%r: a.append(v)
    return r,sorted(a)
if __name__=='__main__':
    fam=sys.argv[1]; seed=int(sys.argv[2]); n=int(sys.argv[3]); rng=random.Random(seed)
    cnt=dict(n=0,gap=0,interval=0,viol=0,short=0)
    with open(f'samp_{fam}_{seed}.out','w') as f:
        while cnt['n']<n:
            r,a=gen(fam,rng)
            if not in_box(r,a) or any(x%r==0 for x in a) or nmiddle(r,a)<3: continue
            z=analyze(r,a); cnt['n']+=1; cnt[z['shape'] if z['shape']!='bad' else 'viol']+=0
            if z['shape'] in('gap','interval'): cnt[z['shape']]+=1
            if z['Bstar']<z['T6']: cnt['short']+=1
            if (not z['holds']) or z['beyondT6']:
                cnt['viol']+=1; f.write(json.dumps(dict(VIOL=True,r=r,a=a,z={k:v for k,v in z.items()}))+'\n'); f.flush()
            elif z['shape']=='gap': f.write(json.dumps(dict(r=r,a=a,F=z['F'],T6=z['T6'],B=z['Bstar']))+'\n')
    print(fam,seed,json.dumps(cnt))
