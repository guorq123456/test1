"""Independent implementations of |RP(Grid(w))| for permutation grids.
w is given as a list of values w(1..n) (1-based values).
Grid: black squares (i, w(i)), rows/cols 1..n.
"""
import itertools, sys
from functools import lru_cache

def words(w):
    """Return (across, down) lists; each word is a list of (r,c) white squares (1-based)."""
    n = len(w)
    black = set((i+1, w[i]) for i in range(n))
    across = []
    for r in range(1, n+1):
        cur = []
        for c in range(1, n+1):
            if (r, c) in black:
                if cur: across.append(cur); cur = []
            else:
                cur.append((r, c))
        if cur: across.append(cur)
    down = []
    for c in range(1, n+1):
        cur = []
        for r in range(1, n+1):
            if (r, c) in black:
                if cur: down.append(cur); cur = []
            else:
                cur.append((r, c))
        if cur: down.append(cur)
    return across, down

def biadj(w):
    across, down = words(w)
    sq2d = {}
    for j, d in enumerate(down):
        for s in d: sq2d[s] = j
    B = [[0]*len(down) for _ in across]
    for i, a in enumerate(across):
        for s in a:
            B[i][sq2d[s]] = 1
    return B

def brute(w):
    """Naive backtracking directly on squares: assign each across word a square, check down words."""
    across, down = words(w)
    if len(across) != len(down): return 0
    sq2d = {}
    for j, d in enumerate(down):
        for s in d: sq2d[s] = j
    used = [False]*len(down)
    cnt = 0
    def rec(i):
        nonlocal cnt
        if i == len(across):
            cnt += 1; return
        for s in across[i]:
            j = sq2d[s]
            if not used[j]:
                used[j] = True; rec(i+1); used[j] = False
    rec(0)
    return cnt

def perm_generic(B):
    """Generic permanent of a 0/1 square matrix by DP over used-column bitmasks,
    processing rows in given order, pruning states in which some unused column
    has no remaining row able to cover it. Exact Python ints."""
    R = len(B); C = len(B[0]) if R else 0
    if R != C: return 0
    rowmask = [sum(1 << j for j in range(C) if B[i][j]) for i in range(R)]
    # suffix union of rows i..R-1
    suf = [0]*(R+1)
    for i in range(R-1, -1, -1): suf[i] = suf[i+1] | rowmask[i]
    full = (1 << C) - 1
    states = {0: 1}
    for i in range(R):
        new = {}
        rm = rowmask[i]
        for S, v in states.items():
            free = rm & ~S
            while free:
                b = free & -free; free ^= b
                T = S | b
                # prune: every column not in T must be coverable by rows i+1..
                if (full & ~T) & ~suf[i+1]:
                    continue
                new[T] = new.get(T, 0) + v
        states = new
    return states.get(full, 0)

def ryser_exact(B):
    """Ryser formula, exact, for small matrices only."""
    n = len(B)
    tot = 0
    for S in range(1, 1 << n):
        prod = 1
        for i in range(n):
            s = 0
            for j in range(n):
                if S >> j & 1 and B[i][j]: s += 1
            prod *= s
            if prod == 0: break
        k = bin(S).count('1')
        tot += (-1)**(n-k) * prod
    return tot

def grid_dp(w):
    """Row-by-row DP over column-coverage bitmask, exact Python ints, dict-based."""
    n = len(w)
    if n == 1: return 1
    c0 = w[0]-1
    states = {1 << c0: 1}
    full = (1 << n) - 1
    for i in range(n):
        c = w[i]-1
        new = {}
        for S, v in states.items():
            if not (S >> c & 1): continue
            T = S & ~(1 << c) if i < n-1 else S
            new[T] = new.get(T, 0) + v
        states = new
        for lo, hi in ((0, c), (c+1, n)):
            if lo >= hi: continue
            new = {}
            for S, v in states.items():
                for j in range(lo, hi):
                    if not (S >> j & 1):
                        T = S | (1 << j)
                        new[T] = new.get(T, 0) + v
            states = new
    return states.get(full, 0)

def layered(shape):
    w = []; base = 0
    for m in shape:
        w += list(range(base+m, base, -1)); base += m
    return w

def parse(s):
    s = s.strip()
    if ' ' in s or ',' in s:
        return [int(x) for x in s.replace(',', ' ').split()]
    return [int(ch) for ch in s]

if __name__ == '__main__':
    for a in sys.argv[1:]:
        w = parse(a)
        print(a, grid_dp(w), perm_generic(biadj(w)))
