# Embed equal-(sum,prod,residue) 3-multiset pairs into four-middle instances; compare U.
# Same r, k, residue multiset, F, D, prod a_i => identical Gamma vector (and tau, mu, T6).
import sys, random, json, ast
from core import U, inv
r=int(sys.argv[1]); tries=int(sys.argv[2]); seed=int(sys.argv[3])
random.seed(seed)
pairs=[ast.literal_eval(l) for l in open(f'coll_r{r}.txt')]
mid=lambda s: 2<=s<=r-2
fo=open(f'emb_r{r}_{seed}.jsonl','w'); found=0; tested=0
for t in range(tries):
    lst=random.choice(pairs)
    X,Y=lst[0],lst[1]
    m=sum(1 for x in X if mid(x%r))
    if m>4: continue
    # others in X must be residue 1/r-1 or middle
    W=[]
    for _ in range(4-m):
        s=random.randint(2,r-2); W.append(r*random.randint(0,(400-s)//r if random.random()<0.3 else 3)+s)
    for _ in range(random.randint(0,8)):
        s=random.choice([1,r-1]); n=random.randint(0 if s==r-1 else 1, 4); W.append(r*n+s)
    a=sorted(list(X)+W); b=sorted(list(Y)+W)
    if len(a)>19: continue
    tested+=1
    ua=U(r,a)[0]; ub=U(r,b)[0]
    if ua!=ub:
        found+=1
        ia=inv(r,a); ib=inv(r,b)
        assert ia==ib, (ia,ib)
        fo.write(json.dumps(dict(r=r,a=a,b=b,Ua=ua,Ub=ub))+'\n'); fo.flush()
        print(r,a,ua[-3:],len(ua),'|',b,ub[-3:],len(ub))
print('r',r,'tested',tested,'found',found)
