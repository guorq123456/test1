"""Battery: Lyndon/necklace features of the raw window and of the alt-flipped window; h = feature parity (and complements)."""
import numpy as np, itertools
from pnu import excess, alt_vec

def lyndon_factors(s):
    # Duval
    n = len(s); i = 0; out = []
    while i < n:
        j, k = i + 1, i
        while j < n and s[k] <= s[j]:
            k = i if s[k] < s[j] else k + 1
            j += 1
        while i <= k:
            out.append(s[i:i + j - k]); i += j - k
    return out

def feats(s):
    F = {}
    lf = lyndon_factors(s)
    F['nLyndon'] = len(lf)
    F['lastLyndonLen'] = len(lf[-1])
    F['firstLyndonLen'] = len(lf[0])
    F['lastLyndonStart'] = len(s) - len(lf[-1])
    F['minrotPos'] = min(range(len(s)), key=lambda i: s[i:] + s[:i])
    F['maxrotPos'] = max(range(len(s)), key=lambda i: s[i:] + s[:i])
    F['minsufPos'] = min(range(len(s)), key=lambda i: s[i:])
    F['maxsufPos'] = max(range(len(s)), key=lambda i: s[i:])
    F['minprefEnd'] = min(range(len(s)), key=lambda i: s[:i + 1][::-1])
    F['weight'] = s.count('1')
    F['runs'] = 1 + sum(1 for i in range(len(s) - 1) if s[i] != s[i + 1])
    F['longest1run'] = max(len(r) for r in s.split('0'))
    F['longest0run'] = max(len(r) for r in s.split('1'))
    return F

names = list(feats('0101').keys())
nus = [3, 5, 7, 9, 11]
hits = []
for src in ('raw', 'flip'):
    for name in names:
        for comp in (0, 1):
            row = []
            for nu in nus:
                h = np.zeros(1 << nu, dtype=np.int64)
                for W in range(1 << nu):
                    s = ''.join(map(str, alt_vec(W, nu))) if src == 'flip' else format(W, f'0{nu}b')
                    h[W] = (feats(s)[name] & 1) ^ comp
                row.append(excess(h, nu))
            if row[0] == 0 or row[1] == 0: hits.append((src, name, comp, row))
            if sum(row[:3]) == 0: print("!!! exact for nu<=7:", src, name, comp, row)
print("features exact at nu=3 or 5:")
for t in hits: print("  ", t)
# pairwise XOR of features (flip source), nu=3,5,7
print("pairwise XOR (flip), exact at nu=5:")
cache = {}
for nu in [3, 5, 7]:
    for W in range(1 << nu):
        s = ''.join(map(str, alt_vec(W, nu))); cache[(nu, W)] = feats(s)
for a, b in itertools.combinations(names, 2):
    row = []
    for nu in [3, 5, 7]:
        h = np.array([(cache[(nu, W)][a] ^ cache[(nu, W)][b]) & 1 for W in range(1 << nu)])
        row.append(excess(h, nu))
    if row[1] == 0: print("  ", a, "^", b, row)
