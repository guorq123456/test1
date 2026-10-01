import sys, glob
bad = []; tot = 0
for fn in sorted(glob.glob('polys_k*.txt')):
    for line in open(fn):
        k,n,cs = line.split(); c = list(map(int, cs.split(','))); tot += 1
        if any(v <= 0 for v in c): bad.append((k,n,'zero/neg coeff'))
        if any(c[j]*c[j] < c[j-1]*c[j+1] for j in range(1, len(c)-1)): bad.append((k,n,'not LC'))
print('checked', tot, 'bad', bad[:10], len(bad))
