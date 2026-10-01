"""
Exhaustive verification, for small parameters, of every set equality and of the
explicit bijections used in proof.md (independently of the counting DPs).

Notation (0-indexed words, alphabet {0..k}):
  A_N  : no interior strict peak            (x_i > x_{i-1} and x_i > x_{i+1}, 1<=i<=N-2, forbidden)
  V_N  : no interior strict valley
  C_N  = A_N & V_N
  B_M  : every nonzero entry <= some existing neighbour
  D_M  : set of images of the clipped 3-window min filter on {0..k}^M
  dfull(x)_i  = max(x_{i-1}, x_i)   (i=0..N, missing terms omitted)        {0..k}^N -> {0..k}^{N+1}
  efull(x)_i  = min(x_{i-1}, x_i)   (i=0..N, missing terms omitted)        {0..k}^N -> {0..k}^{N+1}
  dval(y)_j   = max(y_j, y_{j+1})   (j=0..M-2)                             {0..k}^M -> {0..k}^{M-1}
  eval_(y)_j  = min(y_j, y_{j+1})
  Phi = dfull o complement : A_N -> B_{N+1}     Psi = complement o eval_ : B_{N+1} -> A_N
  Theta = efull : C_N -> D_{N+1}                Xi = dval : D_{N+1} -> C_N
"""
import itertools
import sys


def no_peak(x):
    return all(not (x[i] > x[i - 1] and x[i] > x[i + 1]) for i in range(1, len(x) - 1))


def no_valley(x):
    return all(not (x[i] < x[i - 1] and x[i] < x[i + 1]) for i in range(1, len(x) - 1))


def nonzero_ok(y):
    M = len(y)
    for i in range(M):
        if y[i] == 0:
            continue
        if not ((i > 0 and y[i] <= y[i - 1]) or (i < M - 1 and y[i] <= y[i + 1])):
            return False
    return True


def dfull(x):
    N = len(x)
    return tuple(max(x[j] for j in (i - 1, i) if 0 <= j < N) if N else 0 for i in range(N + 1))


def efull(x, k):
    N = len(x)
    return tuple(min([x[j] for j in (i - 1, i) if 0 <= j < N] or [k]) for i in range(N + 1))


def dval(y):
    return tuple(max(y[j], y[j + 1]) for j in range(len(y) - 1))


def eval_(y):
    return tuple(min(y[j], y[j + 1]) for j in range(len(y) - 1))


def comp(x, k):
    return tuple(k - t for t in x)


def eps3(w):
    M = len(w)
    return tuple(min(w[j] for j in (i - 1, i, i + 1) if 0 <= j < M) for i in range(M))


LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 3 * 10 ** 5
total = 0
for k in range(0, 8):
    for N in range(1, 30):
        if (k + 1) ** (N + 1) > LIMIT:
            break
        words_N = list(itertools.product(range(k + 1), repeat=N))
        words_N1 = list(itertools.product(range(k + 1), repeat=N + 1))
        A = {x for x in words_N if no_peak(x)}
        V = {x for x in words_N if no_valley(x)}
        C = A & V
        B = {y for y in words_N1 if nonzero_ok(y)}
        D = {eps3(w) for w in words_N1}
        imEval = {eval_(w) for w in words_N1}          # Lemma 2: = V_N
        imDval = {dval(w) for w in words_N1}           # Lemma 2': = A_N
        imDfull = {dfull(x) for x in words_N}          # Lemma 3: = B_{N+1}
        assert imEval == V, (k, N)
        assert imDval == A, (k, N)
        assert imDfull == B, (k, N)
        assert {comp(x, k) for x in A} == V
        # Theorem 1 bijection
        Phi = {x: dfull(comp(x, k)) for x in A}
        assert set(Phi.values()) == B and len(set(Phi.values())) == len(A)
        for x, y in Phi.items():
            assert comp(eval_(y), k) == x
        for y in B:
            assert dfull(comp(comp(eval_(y), k), k)) == y
        # Theorem 2 bijection
        Th = {x: efull(x, k) for x in C}
        assert set(Th.values()) == D and len(set(Th.values())) == len(C)
        for x, z in Th.items():
            assert dval(z) == x
        for z in D:
            assert dval(z) in C and efull(dval(z), k) == z
        # Lemma 5 (opening gamma = dval o efull preserves V_N and maps into A_N)
        for u in V:
            g = dval(efull(u, k))
            assert g in C
            assert efull(g, k) == efull(u, k)
        # factorisation eps3 = efull o eval_ (Lemma 4)
        for w in words_N1:
            assert eps3(w) == efull(eval_(w), k)
        total += 1
        print(f'k={k} N={N}: |A_N|={len(A)} = |B_N+1|={len(B)}, |C_N|={len(C)} = |D_N+1|={len(D)}  all assertions OK', flush=True)
print('cases verified:', total)
