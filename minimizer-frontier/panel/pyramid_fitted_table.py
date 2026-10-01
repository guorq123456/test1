"""Self-contained recursive rule for P(nu), sigma=w=2 (state-passing pyramid), with verification.
Rule: every odd nu gets a state function g_nu : {0,1}^nu -> {0,1}^2; the scheme is h_nu = first state bit.
  base: g_1(0) = (0, 0), g_1(1) = (0, 1)
  step: g_nu(W) = PHI[ g_{nu-2}(W[0:nu-2]), g_{nu-2}(W[1:nu-1]), g_{nu-2}(W[2:nu]), raw bits [0, -1] ]
  (sub-window deletion tuples [(-2, -1), (0, -1), (0, 1)]; key bits in that order, first = most significant; raw position
   p<0 means nu+p; 'm' means the middle).  PHI is the fixed 256-entry table below (the same at every level).
Prints excess(h_nu, nu) for nu = 3..13 (0 = optimal, i.e. the Kille et al. bound is attained for k = nu-1 and k = nu)."""
import sys, numpy as np
sys.path.insert(0, '/home/user/test1/minimizer-frontier')
from pnu import excess
B = 2
FEATS = {'sub': [(-2, -1), (0, -1), (0, 1)], 'raw': [0, -1]}
G1 = {0: (0, 0), 1: (0, 1)}
PHI = "10111101110011111110000111000101111111111111111111101101110010000000000000010000100110111101111101010001010100011001100110011001111101111101110111110001110110011111110111111101111101011101110100000101000101011001010111011101011010100101010110010001100101011010101111101010101010101011101010101010101011111010101011101110010100010101000110111111111111110101000101010101111111111111111100000000110101010010101010101101101110111010101111101110111011100001000100010000111111111111111110001001000000011111111110111111"   # entry k occupies characters k*B .. k*B+B-1

def pos(p, nu):
    if isinstance(p, str):
        return (nu - 1) // 2 + (int(p[1:]) if len(p) > 1 else 0)
    return p if p >= 0 else nu + p

def bits(nu):
    W = np.arange(1 << nu); return np.array([(W >> (nu - 1 - i)) & 1 for i in range(nu)]).T

def build(numax):
    gs = {1: np.array([G1[0], G1[1]], dtype=np.int64)}
    tab = np.array([[int(PHI[k * B + b]) for b in range(B)] for k in range(len(PHI) // B)], dtype=np.int64)
    for nu in range(3, numax + 1, 2):
        Bm = bits(nu); key = np.zeros(1 << nu, dtype=np.int64)
        for tup in FEATS['sub']:
            lvl = nu - len(tup); dele = {pos(p, nu) for p in tup}
            keep = [q for q in range(nu) if q not in dele]
            code = np.zeros(1 << nu, dtype=np.int64)
            for q in keep: code = (code << 1) | Bm[:, q]
            for b in range(B): key = (key << 1) | (gs[lvl][code, b] if lvl >= 1 else 0)
        for p in FEATS['raw']: key = (key << 1) | Bm[:, pos(p, nu)]
        gs[nu] = tab[key]
    return gs

if __name__ == '__main__':
    numax = int(sys.argv[1]) if len(sys.argv) > 1 else 13
    gs = build(numax)
    for nu in range(3, numax + 1, 2):
        print(f'nu={nu}: excess = {excess(gs[nu][:, 0].astype(np.int64), nu)}', flush=True)
