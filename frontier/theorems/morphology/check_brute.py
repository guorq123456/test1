"""
Step 2a: reproduce stored OEIS terms by brute force directly from the definitions
(defs.py).  Only terms whose brute-force search space is <= LIMIT are computed.
"""
import sys
from defs import *

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 600000

data = {}
for line in open('/tmp/claude-0/deep/morphology/stripped_rel.txt'):
    a, s = line.split(' ', 1)
    data[a] = [int(t) for t in s.strip().strip(',').split(',')]


def antidiag(seq, n, k):
    """T(n,k), n,k>=1, for a table read by antidiagonals with n increasing
    inside each antidiagonal (T(1,1), T(1,2), T(2,1), T(1,3), T(2,2), T(3,1), ...)."""
    d = n + k - 1          # antidiagonal number, 1-based
    idx = (d - 1) * d // 2 + (n - 1)
    return seq[idx] if idx < len(seq) else None


report = []


def check(name, stored, computed):
    ok = stored == computed
    report.append((name, ok, stored, computed))
    print(('OK  ' if ok else 'FAIL'), name, stored, computed, flush=True)


# --- single sequences (offset 1) ---
peak_cols = {'A200880': 2, 'A200881': 3, 'A200882': 4, 'A200883': 5, 'A200884': 6, 'A200885': 7}
pv_cols = {'A200865': 2, 'A200866': 3, 'A200867': 4, 'A200868': 5, 'A200869': 6, 'A200870': 7}
for a, k in peak_cols.items():
    for n in range(1, 30):
        if (k + 1) ** (n + 2) > LIMIT:
            break
        check(f'{a}({n})', data[a][n - 1], A200886_T(n, k))
for a, k in pv_cols.items():
    for n in range(1, 30):
        if (k + 1) ** (n + 2) > LIMIT:
            break
        check(f'{a}({n})', data[a][n - 1], A200871_T(n, k))
# rows: A200887..A200892 = 0..n arrays of length 4..9 (offset 1 in n)
for j, a in enumerate(['A200887', 'A200888', 'A200889', 'A200890', 'A200891', 'A200892']):
    L = 4 + j
    for n in range(1, 30):
        if (n + 1) ** L > LIMIT:
            break
        check(f'{a}({n})', data[a][n - 1], A200886_T(L - 2, n))
for j, a in enumerate(['A200872', 'A200873', 'A200874', 'A200875', 'A200876', 'A200877']):
    L = 4 + j
    for n in range(1, 30):
        if (n + 1) ** L > LIMIT:
            break
        check(f'{a}({n})', data[a][n - 1], A200871_T(L - 2, n))
# tables
for n in range(1, 12):
    for k in range(1, 12):
        if (k + 1) ** (n + 2) > LIMIT:
            continue
        v = antidiag(data['A200886'], n, k)
        if v is not None:
            check(f'A200886({n},{k})', v, A200886_T(n, k))
        v = antidiag(data['A200871'], n, k)
        if v is not None:
            check(f'A200871({n},{k})', v, A200871_T(n, k))

# --- n X 1 nonzero family (offset 1) ---
nz_cols = {'A202882': 2, 'A203094': 3, 'A203184': 4, 'A203050': 5, 'A203059': 6, 'A202909': 7}
for a, K in nz_cols.items():
    for n in range(1, 30):
        if (K + 1) ** n > LIMIT:
            break
        check(f'{a}({n})', data[a][n - 1], nonzero_family_T(n, 1, K))
# 2-D tables of that family (a few entries, to confirm the reading of the definition)
nz_tabs = {'A202889': 2, 'A203101': 3, 'A203191': 4, 'A203057': 5, 'A203066': 6, 'A202916': 7}
for a, K in nz_tabs.items():
    for n in range(1, 8):
        for m in range(1, 8):
            if (K + 1) ** (n * m) > LIMIT:
                continue
            v = antidiag(data[a], n, m)
            if v is not None:
                check(f'{a}({n},{m})', v, nonzero_family_T(n, m, K))

# --- min-filter families, n X 1 and n X 2 ---
check_min = {'A217450': (2, 'hv', 1), 'A218051': (3, 'hvda', 1)}
for a, (K, nb, m) in check_min.items():
    for n in range(1, 30):
        if (K + 1) ** n > LIMIT:
            break
        check(f'{a}({n})', data[a][n - 1], minfilter_images(n, m, K, nb))
min_tabs = {'A217637': (1, 'hv'), 'A217457': (2, 'hv'), 'A218181': (3, 'hv'),
            'A218084': (1, 'hva'), 'A217645': (2, 'hva'), 'A218651': (3, 'hva'),
            'A217982': (1, 'hvda'), 'A217547': (2, 'hvda'), 'A218056': (3, 'hvda')}
for a, (K, nb) in min_tabs.items():
    for n in range(1, 25):
        for m in ((1, 2) if nb != 'hva' else (1,)):
            if (K + 1) ** (n * m) > LIMIT:
                continue
            v = antidiag(data[a], n, m)
            if v is not None:
                check(f'{a}({n},{m})', v, minfilter_images(n, m, K, nb))

# --- valid sliding-window min families, window 2 column ---
for a, K in (('A217883', 2), ('A217954', 3)):
    for n in range(1, 25):
        if (K + 1) ** (n + 1) > LIMIT:
            break
        v = antidiag(data[a], n, 2)
        if v is not None:
            check(f'{a}({n},2)', v, valid_window_min_images(n, 2, K))

bad = [r for r in report if not r[1]]
print('TOTAL checks', len(report), 'failures', len(bad))
