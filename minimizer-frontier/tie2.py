import sys, numpy as np
from pnu import excess, alt_vec
from walkrules import walk
def mk(rule, nu):
    h = np.zeros(1 << nu, dtype=np.int64)
    for W in range(1 << nu):
        v = alt_vec(W, nu); y = walk(v); M, mn = max(y), min(y)
        Mx = [i for i, t in enumerate(y) if t == M]; Mn = [i for i, t in enumerate(y) if t == mn]
        ctr = nu / 2
        if rule == 'mid':
            a, b = (Mx[0] + Mx[-1]) / 2, (Mn[0] + Mn[-1]) / 2
            r = a < b if a != b else (sum(v) > nu / 2)
        elif rule == 'mid|wt':
            a, b = (Mx[0] + Mx[-1]) / 2, (Mn[0] + Mn[-1]) / 2
            r = a < b if a != b else (sum(v) < nu / 2)
        elif rule == 'center':
            a = min(Mx, key=lambda i: (abs(i - ctr), i)); b = min(Mn, key=lambda i: (abs(i - ctr), i)); r = a < b
        elif rule == 'center2':
            a = min(Mx, key=lambda i: (abs(i - ctr), -i)); b = min(Mn, key=lambda i: (abs(i - ctr), -i)); r = a < b
        elif rule == 'pairs':
            lt = sum(1 for i in Mx for j in Mn if i < j); gt = sum(1 for i in Mx for j in Mn if i > j)
            r = lt > gt if lt != gt else (sum(v) > nu / 2)
        elif rule == 'pairs|wt':
            lt = sum(1 for i in Mx for j in Mn if i < j); gt = sum(1 for i in Mx for j in Mn if i > j)
            r = lt > gt if lt != gt else (sum(v) < nu / 2)
        elif rule == 'both':
            p1 = Mx[0] < Mn[-1]; p2 = Mx[-1] < Mn[0]
            r = p1 if p1 == p2 else (sum(v) > nu / 2)
        elif rule == 'both|wt':
            p1 = Mx[0] < Mn[-1]; p2 = Mx[-1] < Mn[0]
            r = p1 if p1 == p2 else (sum(v) < nu / 2)
        elif rule == 'both|mid':
            p1 = Mx[0] < Mn[-1]; p2 = Mx[-1] < Mn[0]
            r = p1 if p1 == p2 else (v[nu // 2] == 1)
        elif rule == 'both|mid0':
            p1 = Mx[0] < Mn[-1]; p2 = Mx[-1] < Mn[0]
            r = p1 if p1 == p2 else (v[nu // 2] == 0)
        elif rule == 'span':   # compare extents: max-set span vs min-set span ... (mirror-symmetric)
            a, b = (Mx[0] + Mx[-1]) / 2, (Mn[0] + Mn[-1]) / 2
            r = a < b if a != b else ((Mx[-1] - Mx[0]) > (Mn[-1] - Mn[0]))
        elif rule == 'span2':
            a, b = (Mx[0] + Mx[-1]) / 2, (Mn[0] + Mn[-1]) / 2
            r = a < b if a != b else ((Mx[-1] - Mx[0]) < (Mn[-1] - Mn[0]))
        h[W] = 1 if r else 0
    return h
nus = [3, 5, 7, 9, 11, 13]
for rule in ['mid', 'mid|wt', 'center', 'center2', 'pairs', 'pairs|wt', 'both', 'both|wt', 'both|mid', 'both|mid0', 'span', 'span2']:
    print(f"{rule:10s} excess {nus}: {[excess(mk(rule, nu), nu) for nu in nus]}")
