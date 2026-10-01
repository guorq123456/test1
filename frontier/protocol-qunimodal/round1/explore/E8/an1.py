# Compare critical B(a) with conjectured 1+sum floor(a_i/3)
import collections
rows=[l.rstrip('\n').split('\t') for l in open('data.tsv')]
D=[(tuple(map(int,a.split(','))),int(B)) for a,bs,B,t in rows]
c=collections.Counter()
for a,B in D:
    S=1+sum(x//3 for x in a)
    c[(len(a),B-S)]+=1
for k in range(1,9):
    print(k,{d:c[(k,d)] for (kk,d) in sorted(c) if kk==k})
