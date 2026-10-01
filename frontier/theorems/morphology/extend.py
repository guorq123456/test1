"""
Step 2b: compare the fast exact counts (dp.py) with every OEIS b-file of the
families (n up to 210, tables up to 9999 entries), check the identities
far beyond, and write extended terms to extended_terms.txt.
"""
from dp import *

BD = '/tmp/claude-0/deep/morphology/bfiles/'


def bfile(a):
    d = {}
    for line in open(BD + 'b' + a[1:] + '.txt'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        n, v = line.split()[:2]
        d[int(n)] = int(v)
    return d


fails = 0
nchecks = 0


def cmp(name, b, f):
    global fails, nchecks
    bad = [n for n in b if f(n) != b[n]]
    nchecks += len(b)
    fails += len(bad)
    print(f'{name}: {len(b)} b-file terms, mismatches {len(bad)}', bad[:5], flush=True)


NMAX = 400
peak = {2: 'A200880', 3: 'A200881', 4: 'A200882', 5: 'A200883', 6: 'A200884', 7: 'A200885'}
nz = {2: 'A202882', 3: 'A203094', 4: 'A203184', 5: 'A203050', 6: 'A203059', 7: 'A202909'}
pv = {2: 'A200865', 3: 'A200866', 4: 'A200867', 5: 'A200868', 6: 'A200869', 7: 'A200870'}
mf = {2: 'A217450', 3: 'A218051'}

out = open('/tmp/claude-0/deep/morphology/extended_terms.txt', 'w')
for k in range(1, 8):
    A = A_all(NMAX + 3, k)
    A2 = A_all_fast(NMAX + 3, k)
    B = B_all_fast(NMAX + 4, k)
    C = C_all_fast(NMAX + 3, k)
    D = D_all(NMAX + 4, k)
    V = V_all(NMAX + 3, k)
    assert A == A2
    # Theorem 1:  A(N) = B(N+1) for all N >= 0 ;  Corollary: V(N) = A(N)
    t1 = all(A[N] == B[N + 1] for N in range(0, NMAX + 3))
    tv = all(A[N] == V[N] for N in range(0, NMAX + 3))
    # Theorem 2:  C(N) = D(N+1) for all N >= 1
    t2 = all(C[N] == D[N + 1] for N in range(1, NMAX + 3))
    print(f'k={k}: Thm1 A(N)=B(N+1) for N<={NMAX+2}: {t1};  V(N)=A(N): {tv};  Thm2 C(N)=D(N+1) for 1<=N<={NMAX+2}: {t2}')
    nchecks += 3 * (NMAX + 2)
    if not (t1 and t2 and tv):
        fails += 1
    if k in peak:
        cmp(peak[k], bfile(peak[k]), lambda n: A[n + 2])
        cmp(nz[k], bfile(nz[k]), lambda n: B[n])
        cmp(pv[k], bfile(pv[k]), lambda n: C[n + 2])
    if k in mf:
        cmp(mf[k], bfile(mf[k]), lambda n: D[n])
    out.write(f'# k={k}\n')
    out.write(f'A(N,{k}) N=0..60 (no interior strict peak; A200886 col {k}: T(n,{k})=A(n+2)): {A[:61]}\n')
    out.write(f'B(M,{k}) M=0..61 (M X 1, nonzero <= some neighbour): {B[:62]}\n')
    out.write(f'C(N,{k}) N=0..60 (no interior strict peak/valley; A200871 col {k}): {C[:61]}\n')
    out.write(f'D(M,{k}) M=0..61 (clipped 3-window min-filter images): {D[:62]}\n')
    out.write(f'A({NMAX},{k}) = {A[NMAX]}\nB({NMAX+1},{k}) = {B[NMAX+1]}\nC({NMAX},{k}) = {C[NMAX]}\nD({NMAX+1},{k}) = {D[NMAX+1]}\n')

# Larger alphabets for Theorem 2 (subset construction stays small: k^2+3k+1 states)
for k in range(8, 21):
    C = C_all_fast(80, k)
    D = D_all(81, k)
    t2 = all(C[N] == D[N + 1] for N in range(1, 81))
    A = A_all_fast(80, k)
    B = B_all_fast(81, k)
    V = V_all(80, k)
    t1 = all(A[N] == B[N + 1] == V[N] for N in range(0, 81))
    nchecks += 240
    if not (t1 and t2):
        fails += 1
    print(f'k={k}: Thm1 (N<=80) {t1}  Thm2 (N<=80) {t2}')

# Whole tables A200886 and A200871 (b-files up to 9999 entries = antidiagonals up to 141)
tb = {'A200886': (A_all_fast, B_all_fast), 'A200871': (C_all_fast, None)}
for a in ('A200886', 'A200871'):
    b = bfile(a)
    maxidx = max(b)
    # antidiagonal reading: index i (1-based) -> (n,k)
    pos = {}
    i = 1
    d = 1
    while i <= maxidx:
        for n in range(1, d + 1):
            k = d + 1 - n
            pos[i] = (n, k)
            i += 1
            if i > maxidx:
                break
        d += 1
    ks = sorted({k for (n, k) in pos.values()})
    cache = {}
    cacheB = {}
    for k in ks:
        nmax = max(n for (n, kk) in pos.values() if kk == k)
        cache[k] = (A_all_fast if a == 'A200886' else C_all_fast)(nmax + 2, k)
        if a == 'A200886':
            cacheB[k] = B_all_fast(nmax + 3, k)
    cmp(a + ' (whole table)', b, lambda i: cache[pos[i][1]][pos[i][0] + 2])
    if a == 'A200886':
        ok = all(cache[k][n + 2] == cacheB[k][n + 3] for (n, k) in pos.values())
        nchecks += len(pos)
        if not ok:
            fails += 1
        print('A200886 whole b-file range: T(n,k) = B(n+3,k) (n X 1 0..k nonzero family):', ok)
    if a == 'A200871':
        # Theorem 2 over the part of the table where the subset construction is cheap
        ok = True
        cnt = 0
        for k in ks:
            if k > 30:
                continue
            nmax = max(n for (n, kk) in pos.values() if kk == k)
            D = D_all(nmax + 3, k)
            ok &= all(cache[k][n + 2] == D[n + 3] for n in range(1, nmax + 1))
            cnt += nmax
        nchecks += cnt
        if not ok:
            fails += 1
        print(f'A200871 b-file range with k<=30 ({cnt} entries): T(n,k) = D(n+3,k):', ok)

# Rows: A200887..A200892 = A200886 rows 2..7 (length 4..9), A200872..A200877 = A200871 rows
rows_p = ['A200887', 'A200888', 'A200889', 'A200890', 'A200891', 'A200892']
rows_v = ['A200872', 'A200873', 'A200874', 'A200875', 'A200876', 'A200877']
for j in range(6):
    L = 4 + j
    bp = bfile(rows_p[j])
    bv = bfile(rows_v[j])
    vals_p = {n: A_all_fast(L, n)[L] for n in bp}
    vals_b = {n: B_all_fast(L + 1, n)[L + 1] for n in bp}
    vals_v = {n: C_all_fast(L, n)[L] for n in bv}
    cmp(rows_p[j], bp, lambda n: vals_p[n])
    cmp(rows_v[j], bv, lambda n: vals_v[n])
    ok = all(vals_p[n] == vals_b[n] for n in bp)
    nchecks += len(bp)
    if not ok:
        fails += 1
    print(f'  row identity {rows_p[j]}(n) = #(length {L+1} words over 0..n, nonzero <= some neighbour), n<=210:', ok)
    ok = True
    for n in bv:
        if n <= 40:
            ok &= vals_v[n] == D_all(L + 1, n)[L + 1]
    print(f'  row identity {rows_v[j]}(n) = #(clipped 3-min images of length {L+1} over 0..n), n<=40:', ok)
    if not ok:
        fails += 1

print('TOTAL comparisons', nchecks, 'failures', fails)
