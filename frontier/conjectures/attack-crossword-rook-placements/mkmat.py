import sys
def mat(w):
    n = len(w); black = {(i, w[i]-1) for i in range(n)}
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
    dn = {c: k for k, d in enumerate(down) for c in d}
    M = [[0]*len(down) for _ in across]
    for i, a in enumerate(across):
        for c in a: M[i][dn[c]] = 1
    return M
w = [int(x) for x in sys.argv[1].split(",")]
M = mat(w); print(len(M))
for row in M: print(" ".join(map(str, row)))
