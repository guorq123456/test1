# Core library for path R2E7: explicit L0 and U_inf in the large-part regime.
# All objects here depend only on (r, residue multiset) -- never on the parts themselves.
import sys, math, subprocess
sys.path.insert(0, '/tmp/claude-0/qu/tools')

def wcoef(k, r, n):
    """w_0..w_n of W(q)=1/((1-q)^(k-1)(1-q^r)), k>=1."""
    w = [1 if i % r == 0 else 0 for i in range(n+1)]   # 1/(1-q^r)
    for _ in range(k-1):                                # multiply by 1/(1-q)
        s = 0
        for i in range(n+1):
            s += w[i]; w[i] = s
    return w

def tau_vec(r, res):
    """tau_t, t=0..r-1: coefficients of (1-q)*prod_i [s_i]_q reduced mod q^r-1."""
    c = [0]*r; c[0] = 1
    for s in res:
        s %= r
        n = [0]*r
        for t in range(r):
            if c[t]:
                for j in range(s): n[(t+j) % r] += c[t]
        c = n
    return [c[t] - c[(t-1) % r] for t in range(r)]

def R(r, k, tau, Delta, w=None):
    """Reduced condition R(Delta): for all m in (Delta/2, Delta/2 + r]: w_m - w_{Delta-m} >= tau_{m mod r}."""
    lo = Delta//2 + 1          # least integer > Delta/2
    hi = lo + r - 1
    if w is None: w = wcoef(k, r, max(hi, 0) + 1)
    def W(n): return w[n] if n >= 0 else 0
    for m in range(lo, hi+1):
        if W(m) - W(Delta - m) < tau[m % r]: return False
    return True

def Uinf(r, res):
    """U_inf as set of offsets e>=1 (b = F + e). res = residues (none divisible by r), k=len(res)>=2."""
    k = len(res); S = sum(res); tau = tau_vec(r, res)
    emax = 2 + (S - k + 1)//r + 2
    w = wcoef(k, r, max(S - k + 1, 0) + 2*r + 5)
    out = {1}
    for e in range(2, emax+1):
        Delta = S - k + 1 - r*(e+1)
        if R(r, k, tau, Delta, w): out.add(e)
    return out

def L0(r, res):
    # proved bound (proofs.md, Thm 3): L >= floor(Delta_2/2)+r+1 with Delta_2 = S-k+1-3r
    k = len(res); S = sum(res)
    return max(1, (S - k + 3 - r)//2)

def L0_old(r, res):
    k = len(res); S = sum(res)
    return max(1, -(-(S - k + 3 - r)//2))

# ---------------- ground truth helpers (fit box only) -----------------
UNI = '/tmp/claude-0/qu/tools/uni'
def in_box(r, a):
    k = len(a)
    if r > 30 or max(a) > 100: return False
    if k <= 40: return True
    return k <= 60 and len(set(a)) == 1

def gt_profile(r, a, bs):
    assert in_box(r, a), (r, a)
    tot = 1
    for x in a: tot *= x
    if tot * max(bs) < 2**120:
        inp = ''.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}\n" for b in bs)
        out = subprocess.run([UNI], input=inp, capture_output=True, text=True).stdout.split()
        return [o == '1' for o in out]
    from gt_big import profile
    return profile(r, a, bs)
