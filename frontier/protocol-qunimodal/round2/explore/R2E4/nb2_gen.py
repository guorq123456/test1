# Two-change neighborhoods: for a random sample of known gap instances, emit random modifications
# changing two entries (each: +-1, +-r, or random value), staying in the fit box, r∤a_i, >=3 middle.
import sys,random,glob
rng=random.Random(int(sys.argv[1])); S=int(sys.argv[2]); M=int(sys.argv[3])
src=[]
for f in ['nb_gap_gaps.txt','two_gaps.txt']+glob.glob('rand_*.gap'):
    for l in open(f):
        x=list(map(int,l.split('|')[0].split())); src.append((x[0],x[2:]))
rng.shuffle(src)
for r,a in src[:S]:
    c=0; tries=0
    while c<M and tries<50*M:
        tries+=1; b=list(a)
        for _ in range(2):
            i=rng.randrange(len(b)); m=rng.random()
            b[i]= b[i]+rng.choice([-1,1]) if m<0.4 else (b[i]+rng.choice([-r,r]) if m<0.7 else rng.randint(1,100))
        if any(v<1 or v>100 or v%r==0 for v in b): continue
        if sum(1 for v in b if 2<=v%r<=r-2)<3: continue
        if len(b)>40 and len(set(b))>1: continue
        print(r,len(b),*sorted(b)); c+=1
