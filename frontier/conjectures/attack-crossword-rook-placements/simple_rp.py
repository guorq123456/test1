# Independent, deliberately naive implementation: build the grid, extract
# across/down words, and count complete rook placements by backtracking over
# across words (choose one white cell per across word; down words must each be
# hit exactly once).
import sys, itertools
def rp(w):
    n = len(w)
    black = {(i, w[i]-1) for i in range(n)}
    across, down = [], []
    for i in range(n):
        cur = []
        for j in range(n):
            if (i, j) in black:
                if cur: across.append(cur); cur = []
            else: cur.append((i, j))
        if cur: across.append(cur)
    for j in range(n):
        cur = []
        for i in range(n):
            if (i, j) in black:
                if cur: down.append(cur); cur = []
            else: cur.append((i, j))
        if cur: down.append(cur)
    if len(across) != len(down): return 0
    dn = {}
    for k, d in enumerate(down):
        for c in d: dn[c] = k
    used = [False]*len(down)
    def bt(a):
        if a == len(across): return 1
        t = 0
        for c in across[a]:
            k = dn[c]
            if not used[k]:
                used[k] = True; t += bt(a+1); used[k] = False
        return t
    return bt(0)
if __name__ == "__main__":
    for s in sys.argv[1:]:
        print(s, rp([int(c) for c in s]))
