"""Anchor rules in the 2-step order.  s cyclic (len m odd); t_i = s_{d*i mod m} (decimation d in {2,(m+1)/2});
walk Y on t with drift delta=2wt-m;  anchor a' = argmin/argmax of (m*Y_i - delta*i) [drift-adjusted] or Y_i [plain];
S = { d*(a'+shift+i) mod m : i=0..(m-1)/2 }  (arc of length (m+1)/2 in i-coords);  h(window)=[0 not in S].
Consistency: all 4 completions of a window must agree.  Report #conflicting windows and excess if consistent."""
import sys, numpy as np
from pnu import excess

def anchor(t, m, kind, adj):
    Y = [0]
    for b in t: Y.append(Y[-1] + (2 * b - 1))
    delta = Y[m]
    vals = [m * Y[i] - delta * i if adj else Y[i] for i in range(m)]
    if kind == 'min': return min(range(m), key=lambda i: (vals[i], i))
    if kind == 'max': return max(range(m), key=lambda i: (vals[i], -i))
    if kind == 'minmax':  # min if delta>0 else max
        return min(range(m), key=lambda i: (vals[i], i)) if delta > 0 else max(range(m), key=lambda i: (vals[i], -i))
    if kind == 'maxmin':
        return max(range(m), key=lambda i: (vals[i], -i)) if delta > 0 else min(range(m), key=lambda i: (vals[i], i))

def build_h(nu, d_choice, kind, adj, shift):
    m = nu + 2
    d = 2 if d_choice == 2 else (m + 1) // 2
    h = np.zeros(1 << nu, dtype=np.int64); conflicts = 0
    for W in range(1 << nu):
        bits = [(W >> (nu - 1 - i)) & 1 for i in range(nu)]
        ans = set()
        for x in (0, 1):
            for y in (0, 1):
                s = bits + [x, y]
                t = [s[(d * i) % m] for i in range(m)]
                a = anchor(t, m, kind, adj)
                S = {(d * (a + shift + i)) % m for i in range((m + 1) // 2)}
                ans.add(0 if 0 in S else 1)
        if len(ans) > 1: conflicts += 1
        h[W] = ans.pop()
    return h, conflicts

if __name__ == '__main__':
    nus = [3, 5, 7, 9]
    best = []
    for d_choice in (2, 'inv'):
        for kind in ('min', 'max', 'minmax', 'maxmin'):
            for adj in (True, False):
                for shift in range(0, 11):
                    row = []
                    for nu in nus:
                        if shift > nu + 1: row.append('-'); continue
                        h, conf = build_h(nu, d_choice, kind, adj, shift)
                        row.append(f"c{conf}" if conf else f"e{excess(h, nu)}")
                    tag = f"d={d_choice} {kind:6s} adj={adj!s:5s} shift={shift:2d}"
                    if any(r == 'e0' for r in row) or all(r.startswith('e') for r in row):
                        print(tag, row)
                    best.append((sum(int(r[1:]) if r[0] == 'e' else 10**6 for r in row), tag, row))
    best.sort()
    print("--- best 8 by total (conflicts penalised):")
    for b in best[:8]: print(b[1], b[2])
