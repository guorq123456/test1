# Embed (1,y,z)~(x,u,v) equal-sum/prod/residue triples into four-middle instances (same k);
# both instances then have identical r, k, residue multiset, F, D, Gamma vector, tau.  Compare U.
import sys, random, json
from core import U, inv
seed=int(sys.argv[1]); tries=int(sys.argv[2]); rmax=int(sys.argv[3])
random.seed(seed)
trip=[tuple(map(int,l.split())) for l in open('coll1_all.txt')]
cand=[]
for r in range(4,rmax+1):
    for y,z,x,u,v in trip:
        X=(1,y,z); Y=(x,u,v)
        if any(t%r==0 for t in X+Y): continue
        if sorted(t%r for t in X)==sorted(t%r for t in Y):
            cand.append((r,X,Y))
print('candidate (r,pair):',len(cand))
fo=open(f'emb1_{seed}.jsonl','w'); found=0; tested=0
for t in range(tries):
    r,X,Y=random.choice(cand)
    mid=lambda s: 2<=s<=r-2
    m=sum(1 for q in X if mid(q%r))
    if m>4: continue
    W=[]
    for _ in range(4-m):
        s=random.randint(2,r-2); W.append(r*random.randint(0,3)+s)
    for _ in range(random.randint(0,10)):
        s=random.choice([1,r-1]); n=random.randint(0 if s==r-1 else 1, 4); W.append(r*n+s)
    a=sorted(list(X)+W); b=sorted(list(Y)+W)
    if len(a)>19 or max(b)>400 or max(a)>400: continue
    tested+=1
    ua=U(r,a)[0]; ub=U(r,b)[0]
    if ua!=ub:
        found+=1
        assert inv(r,a)==inv(r,b)
        fo.write(json.dumps(dict(r=r,a=a,b=b,Ua=ua,Ub=ub))+'\n'); fo.flush()
        print(r,a,ua[-3:],len(ua),'|',b,ub[-3:],len(ub))
print('tested',tested,'found',found)
