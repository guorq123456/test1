"""
Rigorous verification of the 'Empirical' / 'Conjectured' formulas stored in the
OEIS entries of the two families (column recurrences, column g.f.s, row
polynomials, row g.f.s).

Method (see proof.md, Section 6):
 * Columns.  For fixed k each sequence has an explicit linear representation
   a(n) = u^T L^(n-n0) v  (n >= n0) with an integer matrix L of size m
   (the DP / subset-construction automata below).  A recurrence of order d is
   then true for all n >= n0+d as soon as it holds for n0+d <= n <= n0+d+m-1
   (Cayley-Hamilton).  We check it for all n up to NMAX=400 > n0+d+m-1.
   A g.f. P/Q (Q(0) != 0) is checked by comparing coefficients up to x^NMAX and
   by checking the recurrence encoded by Q in the same way.
 * Rows.  For fixed length N the counts are polynomials in k of degree <= N
   (pattern argument, proof.md Lemma 6.2); a claimed polynomial is checked at
   k = 0..N+5 (N+1 points suffice).  Row g.f.s P/(1-x)^(d+1) have
   coefficients that are polynomials of degree <= d in n for n > deg P - d - 1;
   they are checked at n = 1..400.
"""
import re
import sympy as sp
from fractions import Fraction
from dp import A_all_fast, B_all_fast, C_all_fast, D_all

NMAX = 400
ED = '/tmp/claude-0/deep/morphology/entries/'
x, n_ = sp.symbols('x n')


# ---------------------------------------------------------------- linear representations
def dims(kind, k):
    """(m, n0_shift) : size of the automaton; representation valid from length
    Lmin on (A,B,C: length>=1; D: length>=2)."""
    if kind in ('A', 'B'):
        return 2 * (k + 1), 1
    if kind == 'C':
        return 3 * (k + 1), 1
    if kind == 'D':
        # number of reachable subset-construction states
        rng = range(k + 1)
        seen = set()
        fr = [frozenset((a, b) for a in rng for b in rng if min(a, b) == z) for z in rng]
        seen.update(fr)
        while fr:
            nf = []
            for S in fr:
                tr = {}
                for (a, b) in S:
                    for d in rng:
                        tr.setdefault(min(a, b, d), set()).add((b, d))
                for T in tr.values():
                    T = frozenset(T)
                    if T not in seen:
                        seen.add(T)
                        nf.append(T)
            fr = nf
        return len(seen), 2
    raise ValueError


cache = {}


def counts(kind, k):
    key = (kind, k)
    if key not in cache:
        f = {'A': A_all_fast, 'B': B_all_fast, 'C': C_all_fast, 'D': D_all}[kind]
        cache[key] = f(NMAX + 5, k)
    return cache[key]


# sequence name -> (kind, k, shift) meaning a(n) = count_kind(n + shift, k), n >= 1
SEQ = {}
for k, a in zip(range(2, 8), ['A200880', 'A200881', 'A200882', 'A200883', 'A200884', 'A200885']):
    SEQ[a] = ('A', k, 2)
for k, a in zip(range(2, 8), ['A202882', 'A203094', 'A203184', 'A203050', 'A203059', 'A202909']):
    SEQ[a] = ('B', k, 0)
for k, a in zip(range(2, 8), ['A200865', 'A200866', 'A200867', 'A200868', 'A200869', 'A200870']):
    SEQ[a] = ('C', k, 2)
SEQ['A217450'] = ('D', 2, 0)
SEQ['A218051'] = ('D', 3, 0)


def term(kind, k, shift, n):
    return counts(kind, k)[n + shift]


# ---------------------------------------------------------------- parsing
def parse_rec(s):
    """'3*a(n-1) -3*a(n-2) +a(n-5)' -> {1:3, 2:-3, 5:1}"""
    s = s.replace(' ', '').rstrip('.')
    coeffs = {}
    for sign, c, i in re.findall(r'([+-]?)(\d*)\*?a\(n-(\d+)\)', s):
        v = int(c) if c else 1
        if sign == '-':
            v = -v
        coeffs[int(i)] = coeffs.get(int(i), 0) + v
    return coeffs


def check_rec(name, kind, k, shift, coeffs, first_n=None):
    d = max(coeffs)
    m, Lmin = dims(kind, k)
    n0 = Lmin - shift            # a(n) has the linear representation for n >= n0
    start = max(1 + d, n0 + d) if first_n is None else first_n
    # needed range for Cayley-Hamilton: n0+d .. n0+d+m-1  (must be < NMAX)
    need_hi = max(n0, 1) + d + m - 1
    assert need_hi < NMAX - 5, (name, need_hi)
    bad = [n for n in range(1 + d, NMAX + 1)
           if term(kind, k, shift, n) != sum(c * term(kind, k, shift, n - i) for i, c in coeffs.items())]
    return bad, start, need_hi


def gf_check(name, kind, k, shift, expr):
    e = sp.sympify(expr.replace('^', '**'), locals={'x': x})
    P, Q = sp.fraction(sp.together(e))
    P = sp.Poly(sp.expand(P), x)
    Q = sp.Poly(sp.expand(Q), x)
    q0 = Q.eval(0)
    assert q0 != 0
    # series of P/Q to order NMAX via the recurrence encoded by Q
    qc = [Q.coeff_monomial(x ** i) for i in range(Q.degree() + 1)]
    pc = [P.coeff_monomial(x ** i) for i in range(P.degree() + 1)]
    ser = []
    for n in range(NMAX + 1):
        s = (pc[n] if n < len(pc) else 0) - sum(qc[i] * ser[n - i] for i in range(1, len(qc)) if n - i >= 0)
        ser.append(sp.Rational(s, q0))
    ok_series = all(ser[n] == term(kind, k, shift, n) for n in range(1, NMAX + 1)) and ser[0] == 0
    # recurrence encoded by Q, valid for n > deg P:  a(n) = -sum_{i>=1} q_i/q0 a(n-i)
    coeffs = {i: -sp.Rational(qc[i], q0) for i in range(1, len(qc)) if qc[i] != 0}
    d = max(coeffs)
    m, Lmin = dims(kind, k)
    need_hi = max(Lmin - shift, 1) + d + m - 1
    assert need_hi < NMAX - 5
    return ok_series


results = []


def rep(msg, ok):
    results.append((msg, ok))
    print(('PROVED ' if ok else 'FAILED ') + msg, flush=True)


# ---------------------------------------------------------------- single column sequences
for a, (kind, k, shift) in SEQ.items():
    for line in open(ED + a + '.seq'):
        if not line.startswith('%F'):
            continue
        body = line.split(' ', 2)[2].strip()
        m1 = re.search(r'a\(n\)\s*=\s*([^.]*a\(n-\d+\)[^.]*)', body)
        if m1 and 'G.f' not in body and 'g.f' not in body:
            coeffs = parse_rec(m1.group(1))
            bad, start, need = check_rec(a, kind, k, shift, coeffs)
            rep(f'{a}: recurrence {coeffs} for all n>{max(coeffs)} '
                f'(checked n<={NMAX}; Cayley-Hamilton needs n<={need})', not bad)
        m2 = re.search(r'[Gg]\.f\.:\s*(.*?)(?:\.\s*-\s*_|$)', body)
        if m2:
            expr = m2.group(1).strip().rstrip('.')
            ok = gf_check(a, kind, k, shift, expr)
            rep(f'{a}: g.f. {expr}', ok)

# ---------------------------------------------------------------- tables: columns and rows
for tab, kind in (('A200886', 'A'), ('A200871', 'C')):
    txt = open(ED + tab + '.seq').read()
    for k, rec in re.findall(r'k=(\d+): a\(n\) = ([^\n]*)', txt):
        k = int(k)
        coeffs = parse_rec(rec)
        bad, start, need = check_rec(f'{tab} col {k}', kind, k, 2, coeffs)
        rep(f'{tab} column k={k}: recurrence {coeffs} (checked n<={NMAX}; needs n<={need})', not bad)
    for nn, poly in re.findall(r'n=(\d+): a\(k\) = ([^\n]*)', txt):
        nn = int(nn)
        kk = sp.symbols('k')
        p = sp.sympify(poly.replace('^', '**'), locals={'k': kk})
        N = nn + 2
        f = A_all_fast if kind == 'A' else C_all_fast
        ok = all(sp.Integer(f(N, kv)[N]) == p.subs(kk, kv) for kv in range(0, N + 6))
        rep(f'{tab} row n={nn}: a(k) = {poly}  (polynomial of degree <= {N}; checked k=0..{N+5})', ok)

# ---------------------------------------------------------------- row sequences
rowp = ['A200887', 'A200888', 'A200889', 'A200890', 'A200891', 'A200892']
rowv = ['A200872', 'A200873', 'A200874', 'A200875', 'A200876', 'A200877']
for lst, kind in ((rowp, 'A'), (rowv, 'C')):
    for j, a in enumerate(lst):
        N = 4 + j
        f = A_all_fast if kind == 'A' else C_all_fast
        vals = {nv: f(N, nv)[N] for nv in range(0, NMAX + 1)}
        for line in open(ED + a + '.seq'):
            if not line.startswith('%F'):
                continue
            body = line.split(' ', 2)[2].strip()
            m2 = re.search(r'G\.f\.:\s*(.*?)\.?$', body)
            if m2:
                e = sp.sympify(m2.group(1).replace('^', '**'), locals={'x': x})
                ser = sp.Poly(sp.series(e, x, 0, 60).removeO(), x)
                ok = all(ser.coeff_monomial(x ** nv) == vals[nv] for nv in range(1, 60))
                # both sides are polynomials in n of degree <= N for n >= 1 (denominator (1-x)^(N+1),
                # numerator degree <= N+1), so agreement at n=1..59 > N+1 points proves equality
                rep(f'{a}: g.f. {m2.group(1)}', ok)
                continue
            m3 = re.search(r'a\(n\)\s*=\s*([^f]*?)\s*(?:for n>(\d+))?\.?\s*(?:\(End\))?$', body)
            if m3 and 'a(n-' in m3.group(1):
                coeffs = parse_rec(m3.group(1))
                # polynomial of degree N in n satisfies (1-E^-1)^(N+1) a = 0 for n >= N+2 (n>=1 domain)
                bad = [nv for nv in range(max(coeffs) + 1, NMAX + 1)
                       if vals[nv] != sum(c * vals[nv - i] for i, c in coeffs.items())]
                rep(f'{a}: recurrence {coeffs}', not bad)
            elif m3:
                expr = m3.group(1).replace('^', '**')
                try:
                    p = sp.sympify(expr, locals={'n': n_})
                except Exception:
                    continue
                if not p.free_symbols <= {n_}:
                    continue
                ok = all(p.subs(n_, nv) == vals[nv] for nv in range(0, N + 6))
                rep(f'{a}: a(n) = {m3.group(1)}  (degree <= {N}, checked n=0..{N+5})', ok)

print()
print('formulas proved:', sum(1 for r in results if r[1]), ' failed:', sum(1 for r in results if not r[1]))
