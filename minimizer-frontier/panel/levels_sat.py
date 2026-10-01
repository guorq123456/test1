"""P(nu) as a minimizer: h(W) = [lam(suffix kmer) < lam(prefix kmer)], lam a PROPER colouring of undirected B(2,nu-1)
with c ordered colours (constant windows free). SAT: smallest c for which a P(nu) solution of this form exists.
Also used for odd k unrestricted ('--odd'): scheme on n=k+1 bits windows."""
import sys, time, numpy as np
from pysat.solvers import Cadical153
sys.path.insert(0, '/home/user/test1/minimizer-frontier')
from w2 import build

def model(nu, c, odd=False, extra=None):
    if odd:   # unrestricted odd k = nu: window n = nu+1 bits, k-mers nu bits
        pool, cl = build(nu, restricted=False); nb = nu + 1
        hv = lambda W: pool.id(('c', W))
    else:
        pool, cl = build(nu, restricted=True); nb = nu
        hv = lambda W: pool.id(('c', W))   # restricted: id ('c', v>>1) where v is (nu+1)-bit; W is nu-bit
    k = nb - 1; K = 1 << k
    g = lambda i, x: pool.id(('g', i, x))   # lam(x) >= i, i = 1..c-1
    for x in range(K):
        for i in range(1, c - 1): cl.append([-g(i + 1, x), g(i, x)])
    for W in range(1 << nb):
        x, y = W >> 1, W & (K - 1)
        if x == y: continue
        # proper: not all g equal
        # h <-> lam(y) < lam(x); with properness h <-> not(lam(x) < lam(y))
        ds = []
        for i in range(1, c):
            d = pool.id(('d', W, i))  # d <-> g(i,x) & ~g(i,y)
            cl += [[-d, g(i, x)], [-d, -g(i, y)], [d, -g(i, x), g(i, y)]]
            ds.append(d)
        e = []
        for i in range(1, c):
            d = pool.id(('d2', W, i))  # g(i,y) & ~g(i,x)
            cl += [[-d, g(i, y)], [-d, -g(i, x)], [d, -g(i, y), g(i, x)]]
            e.append(d)
        cl.append(ds + e)              # proper colouring
        h = hv(W)
        cl.append([-h] + ds); cl += [[h, -d] for d in ds]
    if extra: cl += extra(pool, g, K)
    return pool, cl, g, K

def levels_of(nu, c, odd=False):
    pool, cl, g, K = model(nu, c, odd)
    s = Cadical153(bootstrap_with=cl)
    if not s.solve(): return None
    pos = set(l for l in s.get_model() if l > 0)
    return [sum(1 for i in range(1, c) if g(i, x) in pos) for x in range(K)]

if __name__ == '__main__':
    odd = '--odd' in sys.argv
    for nu in [int(a) for a in sys.argv[1].split(',')]:
        for c in range(2, 8):
            t = time.time(); lam = levels_of(nu, c, odd)
            print(f"{'odd k' if odd else 'P'}({nu}) c={c}: {'SAT' if lam else 'UNSAT'} ({time.time()-t:.1f}s)", flush=True)
            if lam:
                k = (nu if odd else nu - 1)
                for l in range(c): print(f"   level {l}:", [format(x, f'0{k}b') for x in range(1 << k) if lam[x] == l])
                break
