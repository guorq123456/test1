import sys, re
sys.path.insert(0,'.')
from fast import A_seq, B_seq, C_seq, D_seq
import sympy as sp
x, n, k = sp.symbols('x n k')
NMAX = 400
seqs = {}
for kk, a in zip(range(2,8), [200880,200881,200882,200883,200884,200885]):
    s = A_seq(NMAX+3, kk); seqs[a] = {i: s[i+2] for i in range(1, NMAX+1)}
for kk, a in zip(range(2,8), [202882,203094,203184,203050,203059,202909]):
    s = B_seq(NMAX, kk); seqs[a] = {i: s[i] for i in range(1, NMAX+1)}
for kk, a in zip(range(2,8), [200865,200866,200867,200868,200869,200870]):
    s = C_seq(NMAX+3, kk); seqs[a] = {i: s[i+2] for i in range(1, NMAX+1)}
for kk, a in [(2,217450),(3,218051)]:
    s = D_seq(NMAX, kk); seqs[a] = {i: s[i] for i in range(1, NMAX+1)}
MR = 120
for r, a in zip(range(2,8), [200887,200888,200889,200890,200891,200892]):
    seqs[a] = {m: A_seq(r+2, m)[r+2] for m in range(1, MR+1)}
for r, a in zip(range(2,8), [200872,200873,200874,200875,200876,200877]):
    seqs[a] = {m: C_seq(r+2, m)[r+2] for m in range(1, MR+1)}
colA = {kk: {i: v for i, v in enumerate(A_seq(NMAX+3, kk)[3:], start=1)} for kk in range(1,8)}
colC = {kk: {i: v for i, v in enumerate(C_seq(NMAX+3, kk)[3:], start=1)} for kk in range(1,8)}
rowA = {r: {m: A_seq(r+2, m)[r+2] for m in range(0, MR+1)} for r in range(1,8)}
rowC = {r: {m: C_seq(r+2, m)[r+2] for m in range(0, MR+1)} for r in range(1,8)}

def check_rec(seq, rhs, lo=None):
    terms = re.findall(r'([+-]?\s*\d*)\s*\*?\s*a\(n-(\d+)\)', rhs)
    co = {}
    for c, d in terms:
        c = c.replace(' ', '')
        c = 1 if c in ('', '+') else (-1 if c == '-' else int(c))
        co[int(d)] = c
    dmax = max(co)
    start = lo if lo is not None else min(seq) + dmax
    ns = [m for m in seq if m >= start]
    bad = [m for m in ns if seq[m] != sum(c*seq[m-d] for d, c in co.items())]
    return (len(bad) == 0, len(ns), co, start)
def check_gf(seq, expr):
    e = sp.sympify(expr.replace('^', '**'))
    num, den = sp.fraction(sp.together(e))
    P = sp.Poly(sp.expand(num), x); Q = sp.Poly(sp.expand(den), x)
    q = [int(c) for c in reversed(Q.all_coeffs())]; p = [int(c) for c in reversed(P.all_coeffs())]
    c0 = q[0]
    # series of p/q
    M = max(seq) + 1
    s = [0]*M
    for i in range(M):
        t = (p[i] if i < len(p) else 0)
        for j in range(1, min(i, len(q)-1)+1): t -= q[j]*s[i-j]
        assert t % c0 == 0
        s[i] = t // c0
    ok = all(s[m] == seq[m] for m in seq) and s[0] == 0
    return ok, len(seq), P.degree(), Q.degree()
def check_poly(seq, expr, var):
    e = sp.sympify(expr.replace('^', '**'), locals={var: sp.Symbol(var)})
    v = sp.Symbol(var)
    ok = all(e.subs(v, m) == seq[m] for m in seq)
    return ok, len(seq), sp.Poly(sp.expand(e), v).degree()

results = []
cur = None
for line in open('allF.txt'):
    line = line.rstrip('\n')
    m = re.match(r'%F (A\d+) (.*)', line); a = int(m.group(1)[1:]); body = m.group(2)
    body_nocredit = re.sub(r'\s*-\s*_[^_]+_.*$', '', body).strip()
    if 'Empirical for columns' in body or 'Empirical for rows' in body or body.startswith('Conjectures from') or body.strip() == '(End)':
        continue
    body2 = body_nocredit.replace('(End)', '').strip().rstrip('.').strip()
    mk = re.match(r'k=(\d+): a\(n\) = (.*)', body2)
    mr = re.match(r'n=(\d+): a\(k\) = (.*)', body2)
    if mk:
        kk = int(mk.group(1)); seq = colA[kk] if a == 200886 else colC[kk]
        ok, cnt, co, st = check_rec(seq, mk.group(2)); results.append((a, 'col k=%d rec' % kk, ok, cnt, 'order %d from n=%d' % (max(co), st))); continue
    if mr:
        r = int(mr.group(1)); seq = rowA[r] if a == 200886 else rowC[r]
        ok, cnt, deg = check_poly(seq, mr.group(2), 'k'); results.append((a, 'row n=%d poly' % r, ok, cnt, 'deg %d (N=%d), checked k=0..%d' % (deg, r+2, MR))); continue
    seq = seqs[a]
    if 'g.f.' in body2 or 'G.f.' in body2:
        expr = body2.split(':', 1)[1] if body2.count(':') == 1 else body2.split(':')[-1]
        ok, cnt, dp, dq = check_gf(seq, expr.strip()); results.append((a, 'gf', ok, cnt, 'degP %d degQ %d' % (dp, dq))); continue
    mm = re.match(r'(?:Empirical: )?a\(n\) = (.*)', body2)
    if mm:
        rhs = mm.group(1)
        if 'a(n-' in rhs:
            lo = None
            mf = re.search(r'for n>(\d+)', rhs)
            if mf: lo = int(mf.group(1)) + 1; rhs = rhs[:mf.start()]
            ok, cnt, co, st = check_rec(seq, rhs, lo); results.append((a, 'rec', ok, cnt, 'order %d from n=%d' % (max(co), st)))
        else:
            ok, cnt, deg = check_poly(seq, rhs, 'n'); results.append((a, 'poly', ok, cnt, 'deg %d' % deg))
        continue
    results.append((a, 'UNPARSED: ' + body2, None, 0, ''))
for r in results: print(r)
print('total formulas', len(results), 'ok', sum(1 for r in results if r[2]), 'fail', sum(1 for r in results if r[2] is False), 'unparsed', sum(1 for r in results if r[2] is None))
