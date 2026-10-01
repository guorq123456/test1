# fast exact DPs (own code), lists indexed by length
import numpy as np

def A_seq(Nmax, k):
    res = [1]
    f0 = [1]*(k+1); f1 = [0]*(k+1)   # length 1: no rise
    res.append(k+1)
    for N in range(2, Nmax+1):
        tot = [f0[v]+f1[v] for v in range(k+1)]
        # prefix sums
        pre = [0]*(k+2)
        for v in range(k+1): pre[v+1] = pre[v] + tot[v]
        suf0 = [0]*(k+2)
        for v in range(k, -1, -1): suf0[v] = suf0[v+1] + f0[v]
        g1 = [pre[w] for w in range(k+1)]           # sum_{v<w}
        g0 = [suf0[w] + f1[w] for w in range(k+1)]  # sum_{v>=w} f0 + f1[w]
        f0, f1 = g0, g1
        res.append(sum(f0)+sum(f1))
    return res[:Nmax+1]

def C_seq(Nmax, k):
    res = [1, k+1]
    U = [0]*(k+1); Dn = [0]*(k+1); F = [1]*(k+1)
    for N in range(2, Nmax+1):
        a = [U[v]+F[v] for v in range(k+1)]
        b = [Dn[v]+F[v] for v in range(k+1)]
        pre = [0]*(k+2)
        for v in range(k+1): pre[v+1] = pre[v]+a[v]
        suf = [0]*(k+2)
        for v in range(k, -1, -1): suf[v] = suf[v+1]+b[v]
        nU = [pre[w] for w in range(k+1)]
        nD = [suf[w+1] for w in range(k+1)]
        nF = [U[w]+Dn[w]+F[w] for w in range(k+1)]
        U, Dn, F = nU, nD, nF
        res.append(sum(U)+sum(Dn)+sum(F))
    return res[:Nmax+1]

def B_seq(Mmax, k):
    res = [1]
    f1 = [1 if v == 0 else 0 for v in range(k+1)]
    f0 = [0 if v == 0 else 1 for v in range(k+1)]
    res.append(sum(f1))
    for M in range(2, Mmax+1):
        tot = [f0[v]+f1[v] for v in range(k+1)]
        pre = [0]*(k+2)
        for v in range(k+1): pre[v+1] = pre[v]+tot[v]
        suf1 = [0]*(k+2)
        for v in range(k, -1, -1): suf1[v] = suf1[v+1]+f1[v]
        g1 = [suf1[w] + f0[w] for w in range(k+1)]
        g0 = [pre[w] for w in range(k+1)]
        f0, f1 = g0, g1
        res.append(sum(f1))
    return res[:Mmax+1]

def D_seq(Mmax, k):
    """compressed DP on the local characterisation z = eps3(delta3(z)).
    state after reading z_0..z_p (p>=1): (z_{p-1}, z_p, s1, s2), s1=sat(p-1), s2=sat(p)."""
    K = k+1
    res = [1, K]
    if Mmax <= 1: return res[:Mmax+1]
    # length 2: z0,z1.  sat(0): option j=0 window {0,1}: z1<=z0 ; (j=1 option needs z2, unknown yet)
    # sat(1): option j=0: window {0,1}: z0 <= z1.
    S = np.zeros((K, K, 2, 2), dtype=object)
    for a in range(K):
        for b in range(K):
            S[a, b, int(b <= a), int(a <= b)] += 1
    # final count for length 2: position0 sat: s1 or (j=1 option: window {0,1} (clipped, no z2): z0>=z1)
    #                           position1 sat: s2 or (j=1: window {0,1}: z0<=z1)
    def final(S):
        tot = 0
        for a in range(K):
            for b in range(K):
                for s1 in (0, 1):
                    for s2 in (0, 1):
                        c = S[a, b, s1, s2]
                        if not c: continue
                        ok1 = s1 or (b <= a)          # pos p-1 via j=p (window {p-1,p}, clipped)
                        ok2 = s2 or (a <= b)          # pos p via j=p (window {p-1,p})
                        if ok1 and ok2: tot += c
        return tot
    res.append(final(S))
    for M in range(3, Mmax+1):
        T = np.zeros((K, K, 2, 2), dtype=object)
        for a in range(K):          # z_{p-1}
            for b in range(K):      # z_p
                for s1 in (0, 1):
                    for s2 in (0, 1):
                        c = S[a, b, s1, s2]
                        if not c: continue
                        for w in range(K):   # z_{p+1}
                            # finalise p-1: option j=p: window {p-1,p,p+1}: b<=a and w<=a
                            if not (s1 or (b <= a and w <= a)): continue
                            # update p: option j=p: window {p-1,p,p+1}: a<=b and w<=b
                            n1 = int(s2 or (a <= b and w <= b))
                            # init p+1: option j=p: window {p-1,p,p+1}: a<=w and b<=w
                            n2 = int(a <= w and b <= w)
                            T[b, w, n1, n2] += c
        S = T
        res.append(final(S))
    return res[:Mmax+1]

def img2_seq(nmax, k):
    from collections import defaultdict
    cur = {frozenset(range(k+1)): 1}
    res = [None]
    for n in range(1, nmax+1):
        nxt = defaultdict(int)
        for S, c in cur.items():
            for u in range(k+1):
                T = frozenset(b for a in S for b in range(k+1) if min(a, b) == u)
                if T: nxt[T] += c
        cur = nxt
        res.append(sum(cur.values()))
    return res
