# For each r, tabulate B-F (and non-monotone flag) against S=sum over a_i of (a_i mod r - 1) [excess], counting only a_i mod r>=1
import collections
tab=collections.defaultdict(collections.Counter)
for L in open('/tmp/claude-0/qu/explore/E7/tuples.txt'):
    x=list(map(int,L.split())); r,k=x[0],x[1]; a=tuple(x[2:2+k]); m=x[2+k]
    F=sum(v//r for v in a)
    S=sum(v%r-1 for v in a)
    B=0
    while B<60 and (m>>B)&1: B+=1
    nm = bin(m).count('1')!=B
    tab[(r,S)][(B-F, 'NM' if nm else '')]+=1
for k in sorted(tab): print(k, dict(tab[k]))
