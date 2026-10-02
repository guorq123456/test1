# For each instance: B_pos (positivity threshold, i* = first negative g) and the set of b<=B_pos where Cmp(b) fails,
# Cmp(b): g_i >= g_{i-rb} for rb <= i <= N_b/2.  Also record whether rb <= N_b/2 (Cmp nonvacuous) at b=B_pos, B_pos-3.
import sys, random, itertools
sys.path.insert(0,'.')
from tcrit import F_of
from posparity import gseq
from collections import Counter
def analyze(a,r):
    g,D=gseq(a,r)
    def G(n):
        if n<0: return 0
        if n<len(g): return g[n]
        return g[len(g)-r+((n-(len(g)-r))%r)]
    istar=next(i for i in range(len(g)) if g[i]<0)
    bp=1
    while D+r*bp<2*istar: bp+=1
    fails=[]
    for b in range(1,bp+1):
        N=D+r*(b-1)
        if any(G(i)<G(i-r*b) for i in range(r*b,N//2+1)): fails.append(b)
    return bp,fails,D
if __name__=='__main__':
    random.seed(int(sys.argv[1])); N=int(sys.argv[2]); c=Counter(); ex=[]
    for it in range(N):
        r=random.randint(2,14); k=random.randint(1,10)
        a=sorted(random.randint(1,random.choice([r-1,2*r,4*r,60])) for _ in range(k))
        if any(x%r==0 for x in a): continue
        bp,fails,D=analyze(a,r)
        key=tuple(bp-b for b in fails); c[key]+=1
        if key and len(ex)<8: ex.append((r,a,bp,fails))
    for k_,v in sorted(c.items()): print("B_pos - failing b:",k_,v)
    for e in ex: print(e)
