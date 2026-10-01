# Functional-dependence test: is critical B a function of a given tuple of statistics?
# For each statistic tuple, count the number of statistic-classes containing >1 distinct B value,
# and the number of multisets in such conflicting classes.
import collections
rows=[l.rstrip('\n').split('\t') for l in open('/tmp/claude-0/qu/explore/E8/data.tsv')]
D=[(tuple(map(int,a.split(','))),int(B)) for a,bs,B,t in rows]
def cnt(a,f): return sum(1 for x in a if f(x))
S={
 'T': lambda a:(sum(x//3 for x in a),),
 'M': lambda a:(sum(x-1 for x in a),),
 'k': lambda a:(len(a),),
 'T,n2': lambda a:(sum(x//3 for x in a),cnt(a,lambda x:x%3==2)),
 'T,[n2>=6]': lambda a:(sum(x//3 for x in a),cnt(a,lambda x:x%3==2)>=6),
 'T,n1': lambda a:(sum(x//3 for x in a),cnt(a,lambda x:x%3==1)),
 'T,k': lambda a:(sum(x//3 for x in a),len(a)),
 'M,n2': lambda a:(sum(x-1 for x in a),cnt(a,lambda x:x%3==2)),
 'M,n2 mod 6': lambda a:(sum(x-1 for x in a),cnt(a,lambda x:x%3==2)%6),
 'M,n2 mod 3': lambda a:(sum(x-1 for x in a),cnt(a,lambda x:x%3==2)%3),
 'T,n2 mod 6': lambda a:(sum(x//3 for x in a),cnt(a,lambda x:x%3==2)%6),
 'sum a': lambda a:(sum(a),),
 'sum a, k': lambda a:(sum(a),len(a)),
 'T, counts mod 6 classes(1,2,4,5)': lambda a:(sum(x//3 for x in a),)+tuple(cnt(a,lambda x,c=c:x%6==c) for c in (1,2,4,5)),
 'T, counts mod 9 classes': lambda a:(sum(x//3 for x in a),)+tuple(cnt(a,lambda x,c=c:x%9==c) for c in (1,2,4,5,7,8)),
 'T, #1,#2,#4,#5': lambda a:(sum(x//3 for x in a),)+tuple(cnt(a,lambda x,c=c:x==c) for c in (1,2,4,5)),
 'T, min a': lambda a:(sum(x//3 for x in a),min(a)),
 'T, #(a_i>=2)': lambda a:(sum(x//3 for x in a),cnt(a,lambda x:x>=2)),
}
for name,f in S.items():
    cls=collections.defaultdict(set); mem=collections.defaultdict(int)
    for a,B in D: cls[f(a)].add(B); mem[f(a)]+=1
    bad=[c for c in cls if len(cls[c])>1]
    print(f"{name:38s} classes={len(cls):6d} conflicting_classes={len(bad):5d} multisets_in_conflict={sum(mem[c] for c in bad)}")
