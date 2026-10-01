# check log-concavity (c_j^2 >= c_{j-1} c_{j+1}) of all computed I(GP(n,k),x)
import sys
from crt import parse_line
tot = 0; fails = []
for k in range(1, 11):
    try: f = open('tm_k%d.txt' % k)
    except FileNotFoundError: continue
    nmax = 0
    for line in f:
        kk, m, c = parse_line(line); tot += 1; nmax = max(nmax, m)
        for j in range(1, len(c)-1):
            if c[j]*c[j] < c[j-1]*c[j+1]: fails.append((m, k, j)); break
    print('k=%d n<=%d' % (k, nmax), flush=True)
print('polys checked', tot, 'log-concavity failures', fails[:20], len(fails))
