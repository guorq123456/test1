"""
Direct (brute-force) implementations of the OEIS definitions involved,
written to follow the wording of the OEIS %N lines as literally as possible.

Conventions: an "a..b array" is a word/array with entries in {a,...,b}.
"""
import itertools


# ---------------------------------------------------------------------------
# A200886 family: "Number of 0..k arrays x(0..n+1) of n+2 elements without any
# interior element greater than both neighbors."   (interior = x(1..n))
# ---------------------------------------------------------------------------
def no_peak_ok(x):
    return not any(x[i] > x[i - 1] and x[i] > x[i + 1] for i in range(1, len(x) - 1))


def A200886_T(n, k):
    return sum(1 for x in itertools.product(range(k + 1), repeat=n + 2) if no_peak_ok(x))


# ---------------------------------------------------------------------------
# A200871 family: "... without any interior element greater than both
# neighbors or less than both neighbors."
# ---------------------------------------------------------------------------
def no_peak_valley_ok(x):
    for i in range(1, len(x) - 1):
        if x[i] > x[i - 1] and x[i] > x[i + 1]:
            return False
        if x[i] < x[i - 1] and x[i] < x[i + 1]:
            return False
    return True


def A200871_T(n, k):
    return sum(1 for x in itertools.product(range(k + 1), repeat=n + 2) if no_peak_valley_ok(x))


# ---------------------------------------------------------------------------
# Hardin 2-D family (A202889 for 0..2, A203101 0..3, A203191 0..4, A203057 0..5,
# A203066 0..6, A202916 0..7): "Number of n X m 0..K arrays with every nonzero
# element less than or equal to some horizontal or vertical neighbor."
# ---------------------------------------------------------------------------
def nonzero_le_neighbor_ok(a, n, m):
    for i in range(n):
        for j in range(m):
            v = a[i * m + j]
            if v == 0:
                continue
            ok = False
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + di, j + dj
                if 0 <= ii < n and 0 <= jj < m and v <= a[ii * m + jj]:
                    ok = True
                    break
            if not ok:
                return False
    return True


def nonzero_family_T(n, m, K):
    return sum(1 for a in itertools.product(range(K + 1), repeat=n * m)
               if nonzero_le_neighbor_ok(a, n, m))


# ---------------------------------------------------------------------------
# Hardin min-filter families: "Number of n X m arrays of the minimum value of
# corresponding elements and their <neighbourhood> neighbors in a random 0..K
# n X m array."  = number of distinct images of the min filter.
#   hv   : horizontal and vertical          (A217637 K=1, A217457 K=2, A218181 K=3)
#   hva  : horizontal, vertical, antidiag.  (A218084 K=1, A217645 K=2, A218651 K=3)
#   hvda : horizontal, vertical, diagonal, antidiagonal
#                                          (A217982 K=1, A217547 K=2, A218056 K=3)
# Hardin's convention for "antidiagonal" (NE/SW) vs "diagonal" (NW/SE) is
# irrelevant for the n X 1 and n X 2 checks we do, since for hva we only use
# n X 1 (where no diagonal neighbour exists).
# ---------------------------------------------------------------------------
NBHD = {
    'hv': [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)],
    'hva': [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, -1)],
    'hvda': [(di, dj) for di in (-1, 0, 1) for dj in (-1, 0, 1)],
}


def minfilter_images(n, m, K, nb):
    offs = NBHD[nb]
    nbrs = []
    for i in range(n):
        for j in range(m):
            nbrs.append([(i + di) * m + (j + dj) for di, dj in offs
                         if 0 <= i + di < n and 0 <= j + dj < m])
    imgs = set()
    for a in itertools.product(range(K + 1), repeat=n * m):
        imgs.add(tuple(min(a[t] for t in nb_) for nb_ in nbrs))
    return len(imgs)


# ---------------------------------------------------------------------------
# A217883 (K=2), A217954 (K=3): T(n,w) = number of n-element 0..K arrays with
# each element the minimum of w adjacent elements of a random 0..K array of
# n+w-1 elements (sliding-window "valid" min filter).
# ---------------------------------------------------------------------------
def valid_window_min_images(n, w, K):
    imgs = set()
    for a in itertools.product(range(K + 1), repeat=n + w - 1):
        imgs.add(tuple(min(a[i:i + w]) for i in range(n)))
    return len(imgs)
