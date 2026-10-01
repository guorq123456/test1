# Extra statistics on aggregate-key collisions: group sizes, and same check with trivial factors a_i=1 removed.
from load import load
from collections import defaultdict
recs=load()
FULL=(1<<60)-1
def run(keyf,name):
    G=defaultdict(lambda:[0,FULL,0])
    for r,a,m in recs:
        key=keyf(r,a); g=G[key]; g[0]|=m; g[1]&=m; g[2]+=1
    nonsing=sum(1 for g in G.values() if g[2]>1)
    inst_nonsing=sum(g[2]*60 for g in G.values() if g[2]>1)
    conf=sum(bin(g[0]&~g[1]).count('1') for g in G.values())
    # instances whose key conflicts
    print(f'{name}: groups(no b)={len(G)} keys(with b)={len(G)*60} nonsingleton groups={nonsing} instances in nonsingleton groups={inst_nonsing} inconsistent keys(with b)={conf}')
def agg(r,a):
    return (r,len(a),tuple(sorted(x%r for x in a)),sum(x//r for x in a),sum(x-1 for x in a))
def agg_nt(r,a):
    a=[x for x in a if x>1]
    return (r,len(a),tuple(sorted(x%r for x in a)),sum(x//r for x in a),sum(x-1 for x in a))
def full_nt(r,a):
    return (r,tuple(x for x in a if x>1))
run(agg,'aggregate key (r,k,res multiset,F,D)')
run(agg_nt,'aggregate key after dropping a_i=1')
run(full_nt,'polynomial identity (r, a without 1s) [sanity: must be 0]')
