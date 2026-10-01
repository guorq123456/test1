"""structure_count.py -- counts A386884(n) from the structure theorem (Theorem 2 of proof.md)
and compares with (i) the closed form (n-4)*T(ceil((n-4)/2)) = A178312(n-4),
(ii) the type-by-type count C(m,2)+m(m-1)(m-2)+[n even]C(m,2), (iii) the stored OEIS terms,
(iv) the exact sets of shapes found by the direct brute force brute4b.c (n <= NB).
Usage: python3 structure_count.py NMAX NB"""
import sys, subprocess, gzip
from math import comb

def shapes_from_params(n):
    """All sets {{s,t,n},{n-s,t,n},{s',n-t,n},{n-s',n-t,n}} with 1<=t<=n-1,
    s,s' in [1,n-1]\\{t,n-t}, having 4 pairwise distinct shapes."""
    out = set()
    for t in range(1, n):
        u = n - t
        good = [s for s in range(1, n) if s != t and s != u]
        for s in good:
            A = tuple(sorted((s, t, n))); B = tuple(sorted((n - s, t, n)))
            for s2 in good:   # note: [1,n-1]\{u, n-u} = [1,n-1]\{t,n-t}
                C = tuple(sorted((s2, u, n))); D = tuple(sorted((n - s2, u, n)))
                S = frozenset((A, B, C, D))
                if len(S) == 4:
                    out.add(S)
    return out

def T(m): return m * (m + 1) // 2
def ceil_half(k): return -((-k) // 2)
def closed(n): return (n - 4) * T(ceil_half(n - 4))
def typecount(n):
    m = (n - 1) // 2
    return comb(m, 2) + m * (m - 1) * (m - 2) + (comb(m, 2) if n % 2 == 0 else 0)
def A178312(k):
    c = ceil_half(k); return k * c * (c + 1) // 2

def oeis_terms(anum):
    with gzip.open('/tmp/claude-0/oeis/stripped.gz', 'rt') as f:
        for line in f:
            if line.startswith(anum):
                return [int(x) for x in line.split(',')[1:-1]]

if __name__ == '__main__':
    NMAX = int(sys.argv[1]); NB = int(sys.argv[2])
    db = oeis_terms('A386884'); db2 = oeis_terms('A178312')
    print('A386884 stored terms:', len(db), ' A178312 stored terms:', len(db2))
    ok = True
    for n in range(1, NMAX + 1):
        sets = shapes_from_params(n)
        c = len(sets)
        checks = [c == closed(n), c == typecount(n)]
        if n >= 4: checks.append(c == A178312(n - 4))
        if n - 4 >= 0 and n - 4 < len(db2): checks.append(c == db2[n - 4])
        if n - 1 < len(db): checks.append(c == db[n - 1])
        if n <= NB:
            res = subprocess.run(['./brute4b', str(n), '1', '1'], capture_output=True, text=True).stdout.split('\n')
            bsets = set()
            for line in res:
                line = line.strip()
                if line.startswith('{'):
                    trip = line.strip('{}').replace('),(', ')|(').split('|')
                    bsets.add(frozenset(tuple(int(v) for v in tr.strip('()').split(',')) for tr in trip))
            checks.append(bsets == sets)
        if not all(checks):
            ok = False; print('MISMATCH at n =', n, c, closed(n), typecount(n), checks)
    print('all checks passed for n = 1 ..', NMAX, '(sets compared with brute force for n <=', NB, '):', ok)
