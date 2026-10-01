# Tabulate excess E=B-(1+sum floor(a_i/3)) vs (n1,n2) = counts of a_i = 1,2 mod 3
import collections
rows=[l.rstrip('\n').split('\t') for l in open('data.tsv')]
D=[(tuple(map(int,a.split(','))),int(B)) for a,bs,B,t in rows]
c=collections.defaultdict(collections.Counter)
for a,B in D:
    S=1+sum(x//3 for x in a)
    n1=sum(1 for x in a if x%3==1); n2=len(a)-n1
    c[(n1,n2)][B-S]+=1
for key in sorted(c): 
    if any(d!=0 for d in c[key]): print(key,dict(c[key]))
print('--- mixed keys:')
for key in sorted(c):
    if len(c[key])>1: print(key,dict(c[key]))
