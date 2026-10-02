# Search for witness pairs with IDENTICAL Gamma-level data:
# same r, same k, same residue multiset, same F (hence same D), same prod a_i (hence identical Gamma vector,
# Gamma = Gamma_res + ((prod a - prod s)/r) * all-ones), yet different U. Four middle residues.
import sys, random, itertools, json
from collections import defaultdict
from core import U
from math import prod

def partitions_bounded(total, m, cap):
    # multisets of m nonneg ints <= cap summing to total, nonincreasing
    def rec(t, m, mx):
        if m == 0:
            if t == 0: yield ()
            return
        for x in range(min(t, mx), -1, -1):
            if x * m < t: break
            for rest in rec(t - x, m - 1, x):
                yield (x,) + rest
    yield from rec(total, m, cap)

def configs(r, resmult, F):
    # resmult: dict residue->multiplicity
    items = sorted(resmult.items())
    caps = {s: (400 - s) // r for s, _ in items}
    def rec(i, t):
        if i == len(items):
            if t == 0: yield []
            return
        s, m = items[i]
        for tt in range(0, t + 1):
            for p in partitions_bounded(tt, m, caps[s]):
                for rest in rec(i + 1, t - tt):
                    yield [r * x + s for x in p] + rest
    yield from rec(0, F)

seed = int(sys.argv[1]); trials = int(sys.argv[2])
random.seed(seed)
fo = open(f'gw_{seed}.jsonl', 'w')
found = 0
for tr in range(trials):
    r = random.randint(6, 30)
    mids = [random.randint(2, r - 2) for _ in range(4)]
    n1 = random.randint(0, 3); nm = random.randint(0, 3)
    res = mids + [1] * n1 + [r - 1] * nm
    rm = defaultdict(int)
    for s in res: rm[s] += 1
    F = random.randint(2, 7)
    buckets = defaultdict(list)
    cnt = 0
    for a in configs(r, rm, F):
        buckets[prod(a)].append(sorted(a)); cnt += 1
        if cnt > 20000: break
    for p, lst in buckets.items():
        if len(lst) < 2: continue
        Us = {}
        for a in lst:
            u = tuple(U(r, a)[0])
            Us.setdefault(u, a)
        if len(Us) > 1:
            found += 1
            rec = dict(r=r, F=F, prod=p, variants=[[list(u), a] for u, a in Us.items()])
            fo.write(json.dumps(rec) + '\n'); fo.flush()
            print(r, F, [(a, list(u)[-3:], len(u)) for u, a in Us.items()])
print('seed', seed, 'found', found)
