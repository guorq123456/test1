# One script producing the headline numbers (fit box: r=2..6, 2<=a_i<=12, r !| a_i, k<=8, b<=60).
# Requires data_r*.txt produced by ./enum r 8 (enum.c), cross-checked by verify_enum.py.
import sys; sys.path.insert(0,'rules')
from common import gamma
from load import load, uniset
from collections import Counter, defaultdict
for r in range(2,7):
    D_=load(r); nt=len(D_); nonmono=0; exc=Counter(); eqA=0; ltA=0; gtA=0; suff_fail=0
    res_map=defaultdict(set)
    for a,mask in D_:
        S=uniset(mask); B=max(S); Q=sum(x//r for x in a); Dg=sum(x-1 for x in a)
        if S!=list(range(1,B+1)): nonmono+=1
        if any(b not in S for b in range(1,Q+2)): suff_fail+=1
        exc[B-1-Q]+=1
        G=gamma(r,a); mu=r-1
        while mu>0 and G[mu-1]>=G[mu]: mu-=1
        BA=1+(Dg+1-2*mu)//r
        if B==BA: eqA+=1
        elif B<BA: ltA+=1
        else: gtA+=1
        res_map[tuple(sorted(x%r for x in a))].add(B-1-Q)
    amb=sum(1 for v in res_map.values() if len(v)>1)
    print(f"r={r}: tuples={nt} b-sets non-interval={nonmono} 'b<=1+Q not all unimodal'={suff_fail} "
          f"excess(B*-1-Q) dist={dict(sorted(exc.items()))} B*==B*_A:{eqA} B*<B*_A:{ltA} B*>B*_A:{gtA} "
          f"residue-classes={len(res_map)} ambiguous={amb}")
