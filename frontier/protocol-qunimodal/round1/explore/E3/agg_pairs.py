# Step 1 of path A2'/H1': look for pairs with identical aggregate statistics
# (r, k, b, multiset of a_i mod r, F=sum floor(a_i/r), D=sum(a_i-1)) but different unimodality.
from load import load
from collections import defaultdict
recs=load()
FULL=(1<<60)-1
G=defaultdict(lambda:[0,FULL,0,[]])  # OR, AND, count, members
for r,a,m in recs:
    res=tuple(sorted(x%r for x in a)); F=sum(x//r for x in a); D=sum(x-1 for x in a)
    key=(r,len(a),res,F,D)
    g=G[key]; g[0]|=m; g[1]&=m; g[2]+=1; g[3].append((a,m))
ninst=len(recs)*60
nkeys=len(G)*60
conf_b=0; conf_groups=0; inst_in_conf=0
byr=defaultdict(int); byk=defaultdict(int)
examples=[]
for key,(o,an,c,mem) in G.items():
    cb=o & ~an
    if cb:
        conf_groups+=1
        nb=bin(cb).count('1'); conf_b+=nb; byr[key[0]]+=nb; byk[key[1]]+=nb
        inst_in_conf+=nb*c
        if len(examples)<10000:
            b=(cb & -cb).bit_length()
            yes=[a for a,m in mem if (m>>(b-1))&1]; no=[a for a,m in mem if not (m>>(b-1))&1]
            examples.append((key,b,yes[0],no[0]))
print('instances in box',ninst)
print('distinct (r,a) records',len(recs))
print('distinct aggregate keys (with b)',nkeys)
print('aggregate keys (with b) that are inconsistent',conf_b)
print('aggregate groups (without b) with >=1 inconsistent b',conf_groups)
print('instances lying in inconsistent keys',inst_in_conf)
print('inconsistent keys by r',dict(sorted(byr.items())))
print('inconsistent keys by k',dict(sorted(byk.items())))
# smallest examples: minimize k then max a then b
examples.sort(key=lambda e:(e[0][1],max(e[2]+e[3]),e[1]))
for e in examples[:25]:
    key,b,y,n=e
    print(f'r={key[0]} k={key[1]} res={key[2]} F={key[3]} D={key[4]} b={b}: unimodal a={y}  NOT unimodal a={n}')
