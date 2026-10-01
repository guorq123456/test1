# Generates proof_aggregate_collision.txt: explicit certificate that unimodality is not a function of
# (r, k, b, multiset of a_i mod r, F, D) -- nor of the same statistics computed after deleting trivial factors a_i=1.
import sys; sys.path.insert(0,'/tmp/claude-0/qu/tools')
from uni_ref import poly, unimodal
r,b=6,4
A1=(2,3,4,4,4,4,4,8); A2=(2,2,3,4,4,4,4,10)
def stats(a): return dict(k=len(a),res=sorted(x%r for x in a),F=sum(x//r for x in a),D=sum(x-1 for x in a),ones=sum(1 for x in a if x==1))
c1=poly(r,list(A1),b); c2=poly(r,list(A2),b)
assert stats(A1)==stats(A2) and unimodal(c1) and not unimodal(c2)
N=len(c1)-1
inc=all(c1[i]<=c1[i+1] for i in range(N//2)); 
L=[]
L.append('STATEMENT. There is no function g with: P(r;a;b) unimodal <=> g(r,k,b,{a_i mod r},F,D)=1, where F=sum floor(a_i/r), D=sum(a_i-1).')
L.append('The same holds for the statistics computed on the nontrivial factors only (a_i>1), since the witness below has no a_i=1.')
L.append('')
L.append(f'Lemma 1. a=(2,3,4,4,4,4,4,8) and a\'=(2,2,3,4,4,4,4,10), r=6, have identical statistics: {stats(A1)} vs {stats(A2)}.')
L.append('  Check: residues of a: 2,3,4,4,4,4,4,(8 mod 6=2) -> {2,2,3,4,4,4,4,4}; of a\': 2,2,3,4,4,4,4,(10 mod 6=4) -> {2,2,3,4,4,4,4,4}.')
L.append('  F: only 8 and 10 are >=6, each floor 1 -> F=1 for both. D: sum(a)=33 for both, k=8 -> D=25.')
L.append('')
L.append(f'Lemma 2. With b=4, P(q)=prod[a_i]_q [4]_(q^6) has degree {N} and coefficients c_0..c_{N}:')
L.append('  '+' '.join(map(str,c1)))
L.append(f'  The sequence is palindromic (c_i=c_{{N-i}}: {c1==c1[::-1]}) and c_i<=c_(i+1) for i=0..{N//2-1}: {inc}; hence weakly unimodal with mode at {N//2}.')
L.append('')
L.append(f'Lemma 3. With b=4, P\'(q)=prod[a\'_i]_q [4]_(q^6) has coefficients:')
L.append('  '+' '.join(map(str,c2)))
i=next(i for i in range(1,N) if c2[i-1]>c2[i]<c2[i+1])
L.append(f'  c\'_{i-1}={c2[i-1]} > c\'_{i}={c2[i]} < c\'_{i+1}={c2[i+1]}. A strict interior local minimum rules out weak unimodality:')
L.append(f'  if the mode m>={i}, then c\'_{i-1}<=c\'_{i} is required (false); if m<={i-1}, then c\'_{i}>=c\'_{i+1} is required (false).')
L.append('')
L.append('Conclusion. The two parameter sets share (r,k,b,{a_i mod r},F,D) and also these statistics on nontrivial factors, but differ in unimodality. QED.')
L.append('Coefficients are reproducible with /tmp/claude-0/qu/tools/uni_ref.py poly(6,a,4) (exact integer arithmetic); also checked by /tmp/claude-0/qu/tools/uni.')
open('proof_aggregate_collision.txt','w').write('\n'.join(L)+'\n')
print('\n'.join(L[:6])); print('...',L[-4:])
