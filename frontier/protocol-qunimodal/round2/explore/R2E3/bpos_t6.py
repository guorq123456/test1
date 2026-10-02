# Compare B_pos (positivity threshold) with T6 and with B*=max U; where is i* (first negative g) relative to tail start D-r+2?
import sys, random
sys.path.insert(0,'.')
from tcrit import poly_a, F_of
from s2check import Uset
from posparity import Bpos
from collections import Counter
def T6(a,r):
    al=poly_a(a); D=len(al)-1
    G=[sum(al[t::r]) for t in range(r)]
    mu=next(t for t in range(r) if all(G[s]>=G[s+1] for s in range(t,r-1)))
    return 1+(D+1-2*mu)//r
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); ex=[]
for it in range(N):
    r=random.randint(2,12); k=random.randint(1,9)
    a=sorted(random.randint(1,random.choice([r-1,2*r,4*r,60])) for _ in range(k))
    if any(x%r==0 for x in a): continue
    U,t=Uset(r,a); bp,istar,D=Bpos(a,r); T=T6(a,r)
    key=('Bpos==T6' if bp==T else 'Bpos<T6' if bp<T else 'Bpos>T6??', 'i* in tail' if istar>=D-r+2 else 'i* before tail')
    c[key]+=1
    if bp<T and len(ex)<6: ex.append((r,a,U,'F',F_of(r,a),'Bpos',bp,'T6',T))
for k_,v in sorted(c.items()): print(k_,v)
for e in ex: print(e)
