"""
Fast exact counting (Python big integers) for the families involved.

  A(N,k): words of length N over {0..k}, no interior strict peak     (A200886: T(n,k)=A(n+2,k))
  C(N,k): no interior strict peak and no interior strict valley      (A200871: T(n,k)=C(n+2,k))
  B(M,k): length-M words (= M X 1 arrays) over {0..k} in which every
          nonzero entry is <= some (existing) neighbour              (A202882 etc.)
  D(M,k): number of distinct images of the clipped 3-window min filter
          z_i = min of w_j over j in {i-1,i,i+1} (existing)           (A217450, A218051)
  V(N,k): number of distinct images of the valid 2-window min filter
          z_i = min(w_i, w_{i+1}), w of length N+1                    (A217883/A217954 col 2)

A, B, C are computed by forward DP on the definition.  D and V are computed
from the *definition as a set of images* by a subset construction (determinising
the automaton that reads the output word and guesses the input), so they do
not use any characterisation of the image proved in proof.md.
"""


def A_all(Nmax, k):
    """list r with r[N] = A(N,k) for N=0..Nmax"""
    r = [1]
    if Nmax == 0:
        return r
    # state: f[v][s], v=current value, s=1 iff current > previous (strict rise)
    f0 = [1] * (k + 1)       # s=0
    f1 = [0] * (k + 1)       # s=1
    r.append(k + 1)
    for N in range(2, Nmax + 1):
        g0 = [0] * (k + 1)
        g1 = [0] * (k + 1)
        for v in range(k + 1):
            for w in range(k + 1):
                c = f0[v] + (f1[v] if w >= v else 0)   # strict rise into v forbids w < v
                if not c:
                    continue
                if w > v:
                    g1[w] += c
                else:
                    g0[w] += c
        f0, f1 = g0, g1
        r.append(sum(f0) + sum(f1))
    return r


def A_all_fast(Nmax, k):
    """same as A_all but O(k) per step with prefix sums (used for big tables)"""
    r = [1]
    if Nmax == 0:
        return r
    f0 = [1] * (k + 1)
    f1 = [0] * (k + 1)
    r.append(k + 1)
    for N in range(2, Nmax + 1):
        # g1[w] = sum_{v<w} (f0[v] + f1[v])      (w > v, and w>=v satisfied)
        # g0[w] = sum_{v>=w} f0[v] + f1[w]       (w <= v; f1[v] allowed only if w>=v i.e. v==w)
        g0 = [0] * (k + 1)
        g1 = [0] * (k + 1)
        acc = 0
        for w in range(k + 1):
            g1[w] = acc
            acc += f0[w] + f1[w]
        acc = 0
        for w in range(k, -1, -1):
            acc += f0[w]
            g0[w] = acc + f1[w]
        f0, f1 = g0, g1
        r.append(sum(f0) + sum(f1))
    return r


def C_all_fast(Nmax, k):
    """C(N,k) for N=0..Nmax; state (v, s) with s in {up, down, flat}"""
    r = [1]
    if Nmax == 0:
        return r
    fu = [0] * (k + 1)
    fd = [0] * (k + 1)
    ff = [1] * (k + 1)       # length-1 words: treat as 'flat' (no constraint)
    r.append(k + 1)
    for N in range(2, Nmax + 1):
        gu = [0] * (k + 1)
        gd = [0] * (k + 1)
        gf = [0] * (k + 1)
        # next w after (v,s): s=up requires w>=v ; s=down requires w<=v ; flat: any
        # new state: w>v -> up, w<v -> down, w==v -> flat
        # gu[w] = sum_{v<w} (fu[v]+fd[v]+ff[v])   but down at v requires w<=v: excluded since w>v
        #       = sum_{v<w} (fu[v] + ff[v])
        # gd[w] = sum_{v>w} (fd[v] + ff[v])
        # gf[w] = fu[w] + fd[w] + ff[w]
        acc = 0
        for w in range(k + 1):
            gu[w] = acc
            acc += fu[w] + ff[w]
        acc = 0
        for w in range(k, -1, -1):
            gd[w] = acc
            acc += fd[w] + ff[w]
        for w in range(k + 1):
            gf[w] = fu[w] + fd[w] + ff[w]
        fu, fd, ff = gu, gd, gf
        r.append(sum(fu) + sum(fd) + sum(ff))
    return r


def B_all_fast(Mmax, k):
    """B(M,k) for M=0..Mmax directly from the definition:
    every nonzero entry must be <= some existing neighbour.
    state (v, sat): v = last value, sat = last entry already satisfied
    (it is 0, or <= its left neighbour)."""
    r = [1]
    if Mmax == 0:
        return r
    fs = [1] + [0] * k       # length 1: value 0 is satisfied, nonzero not yet
    fn = [0] + [1] * k
    r.append(fs[0])          # a length-1 word is valid iff its entry is 0  -> 1
    for M in range(2, Mmax + 1):
        gs = [0] * (k + 1)
        gn = [0] * (k + 1)
        # from (v, sat) to w:  if not sat need w >= v.
        # new entry w is satisfied iff w == 0 or w <= v.
        # gs[w] = sum_{v >= w} (fs[v] + fn[v])  [w<=v: unsat v ok iff w>=v -> v==w]
        #        careful: for v > w, unsat v requires w >= v: false.
        #  => gs[w] = sum_{v>=w} fs[v] + fn[w]   (for w>0);  w==0: all v with sat, plus fn[0]=0
        # gn[w] (w>0, w>v) = sum_{v<w} (fs[v] + fn[v])   [unsat v needs w>=v: ok]
        acc = 0
        for w in range(k, -1, -1):
            acc += fs[w]
            gs[w] = acc + fn[w]
        # w == 0: satisfied regardless; previous v: sat any v, or unsat v needs 0>=v -> v==0 (fn[0]=0)
        gs[0] = sum(fs) + fn[0]
        acc = 0
        for w in range(k + 1):
            if w > 0:
                gn[w] = acc
            acc += fs[w] + fn[w]
        fs, fn = gs, gn
        r.append(sum(fs))    # last entry has no right neighbour: must be satisfied
    return r


def D_all(Mmax, k):
    """number of distinct clipped-3-window-min images, M=1..Mmax, by subset construction."""
    r = {0: 1, 1: k + 1}
    rng = range(k + 1)
    # after reading z_0 (= min(w0,w1)), state = set of (w0,w1) with min = z_0
    states = {}
    for z0 in rng:
        S = frozenset((a, b) for a in rng for b in rng if min(a, b) == z0)
        states[S] = states.get(S, 0) + 1
    for M in range(2, Mmax + 1):
        # finish: last output z_{M-1} = min(w_{M-2}, w_{M-1}); state holds (w_{M-2}, w_{M-1})
        tot = 0
        for S, c in states.items():
            tot += c * len({min(a, b) for (a, b) in S})
        r[M] = tot
        if M == Mmax:
            break
        new = {}
        for S, c in states.items():
            # read z_{i+1} = min(w_i, w_{i+1}, w_{i+2}); new state (w_{i+1}, w_{i+2})
            trans = {}
            for (a, b) in S:
                for d in rng:
                    trans.setdefault(min(a, b, d), set()).add((b, d))
            for z, T in trans.items():
                T = frozenset(T)
                new[T] = new.get(T, 0) + c
        states = new
    return [r[M] for M in range(0, Mmax + 1)]


def V_all(Nmax, k):
    """number of distinct valid-2-window-min images of length N (input length N+1)."""
    r = [1]
    rng = range(k + 1)
    states = {frozenset(rng): 1}     # possible values of w_i (current last input)
    for N in range(1, Nmax + 1):
        new = {}
        for S, c in states.items():
            trans = {}
            for a in S:
                for b in rng:
                    trans.setdefault(min(a, b), set()).add(b)
            for z, T in trans.items():
                T = frozenset(T)
                new[T] = new.get(T, 0) + c
        states = new
        r.append(sum(states.values()))
    return r


if __name__ == '__main__':
    for k in range(1, 4):
        print(k, A_all(10, k)[:10], A_all_fast(10, k)[:10])
        print(k, B_all_fast(11, k))
        print(k, C_all_fast(10, k))
        print(k, D_all(11, k))
        print(k, V_all(10, k))
