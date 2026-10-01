# Cross-check C plane simulator vs b-files (right readout, and left readout = reversal by symmetry is
# checked against the b-files too), then compare rule 451 vs rule 193 for n <= 1000.
from repro import bfile, readouts
R = {code: [l.strip() for l in open(f'/tmp/claude-0/deep/mathar-ca/verify1/rerun/r{code}.txt')] for code in (451,193)}
N = len(R[451])-1
dec = lambda s: int(s)            # FromDigits[...,10] of the digit string
for A, code, side in [('282297',451,'R'),('282295',451,'L'),('279721',193,'R'),('279720',193,'L')]:
    b = bfile(A)
    v = [dec(s if side=='R' else s[::-1]) for s in R[code][:len(b)]]
    print('A'+A, 'C-plane sim reproduces all', len(b), 'b-file terms:', v==b)
# also cross-check C plane vs numpy torus replica (n<=126) for both sides
for code in (451,193):
    r,l = readouts(code)
    print(code, 'C plane == numpy torus replica (n<=126):', all(int(R[code][n])==r[n] and int(R[code][n][::-1])==l[n] for n in range(127)))
# also check left readout equals reversed right readout in the torus replica (D4 symmetry)
eq = [n for n in range(N+1) if R[451][n]==R[193][n]]
ne = [n for n in range(N+1) if R[451][n]!=R[193][n]]
print('N =', N)
print('n with equal readouts:', eq[:40], '... count', len(eq))
print('n with different readouts: first', ne[:10], 'count', len(ne))
print('n>=26 all different:', all(n in set(ne) for n in range(26, N+1)))
n=26
print('stage 26 rule 451 x=0..26:', R[451][n]); print('stage 26 rule 193 x=0..26:', R[193][n])
print('positions x where they differ at n=26:', [x for x in range(n+1) if R[451][n][x]!=R[193][n][x]])
