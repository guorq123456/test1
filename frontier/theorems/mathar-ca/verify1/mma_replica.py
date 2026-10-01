# Literal replica of Price's Mathematica program (my own code).
import numpy as np, sys
def run(code, stages=128):
    rule = [int(b) for b in format(code, '010b')]   # IntegerDigits[code,2,10], MSB first
    g = 2*stages+1
    a = np.zeros((g,g), dtype=np.int64)
    # PadLeft[{{1}},{g,g},0,Floor[{g,g}/2]]: margin floor(g/2) on the right/bottom
    m = g//2
    a[g-1-m, g-1-m] = 1          # 0-based position (g-1-m) = 1-based g-m
    ca=[a]
    cur=a
    for n in range(1, stages+2):
        # ListConvolve[{{0,2,0},{2,1,2},{0,2,0}}, cur, 2]: cyclic, centre aligned
        # convolution: out[i,j] = sum_{r,s} ker[r,s]*cur[i-(r-1), j-(s-1)] (kernel symmetric)
        ker = [[0,2,0],[2,1,2],[0,2,0]]
        out = np.zeros_like(cur)
        for r in range(3):
            for s in range(3):
                if ker[r][s]:
                    out += ker[r][s]*np.roll(np.roll(cur, r-1, axis=0), s-1, axis=1)
        # Map[rule[[10-#]]&, ...] (1-based) -> rule[9-v] 0-based
        lut = np.array([rule[9-v] for v in range(10)], dtype=np.int64)
        cur = lut[out]
        ca.append(cur)
    k = (g+1)//2
    # trimmed: entry n (1-based) = rows/cols k+1-n .. k-1+n (1-based)
    trimmed = []
    for n in range(1, k+1):
        lo, hi = k+1-n, k-1+n
        trimmed.append(ca[n-1][lo-1:hi, lo-1:hi])
    right = []; left = []
    for i in range(1, stages):
        row = trimmed[i-1][i-1]   # Part[ca[[i]][[i]], ...]
        r = row[i-1:2*i-1]         # Range[i, 2i-1]
        l = row[0:i]               # Range[1, i]
        right.append(int(''.join(map(str, r))))
        left.append(int(''.join(map(str, l))))
    return right, left
if __name__ == '__main__':
    def rd(f):
        return {int(x.split()[0]): int(x.split()[1]) for x in open(f) if len(x.split())==2}
    for code, rb, lb in [(451,'282297','282295'), (193,'279721','279720')]:
        R, L = run(code)
        Rb = rd(f'oeis_b{rb}.txt'); Lb = rd(f'oeis_b{lb}.txt')
        print(code, all(R[n]==Rb[n] for n in range(127)), all(L[n]==Lb[n] for n in range(127)))
        with open(f'mma_{code}.txt','w') as f:
            for n in range(127): f.write(f'{n} {R[n]} {L[n]}\n')
