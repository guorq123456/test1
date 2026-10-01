# Independent implementation (written from the OEIS %N wording, not from the colleague's code)
from itertools import product
from functools import lru_cache

# ---------- brute force straight from the definitions ----------
def peak_free(x):
    return not any(x[i] > x[i-1] and x[i] > x[i+1] for i in range(1, len(x)-1))
def valley_free(x):
    return not any(x[i] < x[i-1] and x[i] < x[i+1] for i in range(1, len(x)-1))
def b_ok(y):
    # n X 1 array: only vertical neighbours i-1, i+1 that exist
    n = len(y)
    for i in range(n):
        if y[i] != 0:
            nb = [y[j] for j in (i-1, i+1) if 0 <= j < n]
            if not any(y[i] <= v for v in nb):
                return False
    return True
def eps3(w):
    n = len(w)
    return tuple(min(w[j] for j in (i-1, i, i+1) if 0 <= j < n) for i in range(n))
def eps2valid(w):
    return tuple(min(w[i], w[i+1]) for i in range(len(w)-1))

def A_bf(N, k): return sum(1 for x in product(range(k+1), repeat=N) if peak_free(x))
def V_bf(N, k): return sum(1 for x in product(range(k+1), repeat=N) if valley_free(x))
def C_bf(N, k): return sum(1 for x in product(range(k+1), repeat=N) if peak_free(x) and valley_free(x))
def B_bf(M, k): return sum(1 for y in product(range(k+1), repeat=M) if b_ok(y))
def D_bf(M, k): return len({eps3(w) for w in product(range(k+1), repeat=M)})
def Img2_bf(n, k): return len({eps2valid(w) for w in product(range(k+1), repeat=n+1)})

# ---------- 2D brute force for the min-filter tables ----------
NB = {
 'hv':   [(0,0),(-1,0),(1,0),(0,-1),(0,1)],
 'hva':  [(0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,1),(1,-1)],
 'hvda': [(di,dj) for di in (-1,0,1) for dj in (-1,0,1)],
}
def minfilter2d_count(n, m, K, nb):
    offs = NB[nb]
    out = set()
    for flat in product(range(K+1), repeat=n*m):
        a = [flat[i*m:(i+1)*m] for i in range(n)]
        res = tuple(min(a[i+di][j+dj] for di, dj in offs if 0 <= i+di < n and 0 <= j+dj < m)
                    for i in range(n) for j in range(m))
        out.add(res)
    return len(out)
def hardin2d_count(n, m, K):
    cnt = 0
    for flat in product(range(K+1), repeat=n*m):
        a = [flat[i*m:(i+1)*m] for i in range(n)]
        ok = True
        for i in range(n):
            for j in range(m):
                v = a[i][j]
                if v == 0: continue
                if not any(v <= a[i+di][j+dj] for di, dj in ((-1,0),(1,0),(0,-1),(0,1)) if 0 <= i+di < n and 0 <= j+dj < m):
                    ok = False; break
            if not ok: break
        if ok: cnt += 1
    return cnt

# ---------- generic sliding-window DP ----------
# Count words z of length L over [0,k] such that pred(window, i_rel) holds at every position,
# where window = (z_{i-r},...,z_{i+r}) with None for nonexistent positions.
def window_count(L, k, r, pred):
    if L == 0:
        return 1
    W = 2*r  # state holds last 2r letters (None = before start)
    # state: tuple of last 2r letters (positions p-2r+1..p) after reading z_0..z_p
    from collections import defaultdict
    cur = defaultdict(int)
    cur[(None,)*W] = 1
    letters = list(range(k+1))
    for p in range(L):
        nxt = defaultdict(int)
        for st, c in cur.items():
            for a in letters:
                win = st + (a,)  # positions p-2r..p ; centre p-r
                if win[r] is not None and not pred(win):
                    continue
                nxt[win[1:]] += c
        cur = nxt
    # finalise: append r 'None's and check the remaining centres
    tot = 0
    for st, c in cur.items():
        s = st
        ok = True
        for _ in range(r):
            win = s + (None,)
            if win[r] is not None and not pred(win):
                ok = False; break
            s = win[1:]
        if ok: tot += c
    return tot

def pred_A(w):   # w=(a,b,c), b exists
    a, b, c = w
    if a is None or c is None: return True
    return not (b > a and b > c)
def pred_V(w):
    a, b, c = w
    if a is None or c is None: return True
    return not (b < a and b < c)
def pred_C(w): return pred_A(w) and pred_V(w)
def pred_B(w):
    a, b, c = w
    if b == 0: return True
    return (a is not None and b <= a) or (c is not None and b <= c)
def pred_D(w):  # w = z_{i-2..i+2}; z in D iff eps3(delta3(z)) == z (adjunction)
    zi = w[2]
    best = None
    for j in (1, 2, 3):  # j-th entry of window is position i-1, i, i+1
        if w[j] is None: continue
        t = max(w[l] for l in (j-1, j, j+1) if w[l] is not None)
        best = t if best is None else min(best, t)
    return best == zi

def A_dp(N, k): return window_count(N, k, 1, pred_A)
def B_dp(M, k): return window_count(M, k, 1, pred_B)
def C_dp(N, k): return window_count(N, k, 1, pred_C)
def D_dp(M, k): return window_count(M, k, 2, pred_D)

# ---------- sequences of counts (single pass) ----------
def window_seq(Lmax, k, r, pred):
    """return list s with s[L] = count for L=0..Lmax"""
    from collections import defaultdict
    W = 2*r
    res = [1]
    cur = {(None,)*W: 1}
    for p in range(Lmax):
        nxt = defaultdict(int)
        for st, c in cur.items():
            for a in range(k+1):
                win = st + (a,)
                if win[r] is not None and not pred(win):
                    continue
                nxt[win[1:]] += c
        cur = nxt
        tot = 0
        for st, c in cur.items():
            s = st; ok = True
            for _ in range(r):
                win = s + (None,)
                if win[r] is not None and not pred(win):
                    ok = False; break
                s = win[1:]
            if ok: tot += c
        res.append(tot)
    return res

# ---------- subset construction for the image of eps- (valid 2-window min) ----------
def img2_seq(nmax, k):
    """number of distinct eps-(w), w in [0,k]^(n+1), n=1..nmax; via determinising the NFA (state = w_{j+1})."""
    from collections import defaultdict
    # after reading u_0..u_j, NFA state = set of possible w_{j+1}
    cur = defaultdict(int)
    start = frozenset(range(k+1))  # possible w_0
    cur[start] = 1
    res = [None]
    for n in range(1, nmax+1):
        nxt = defaultdict(int)
        for S, c in cur.items():
            for u in range(k+1):
                T = frozenset(b for a in S for b in range(k+1) if min(a, b) == u)
                if T:
                    nxt[T] += c
        cur = nxt
        res.append(sum(cur.values()))
    return res
