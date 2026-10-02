"""Build the in-box fit set: instances (r, a) with ground-truth U (exact, cross-checked method).
All instances: r in [4,30], k in [3,40] (<=60 if all a_i equal), a_i<=100, r does not divide any a_i,
at least three a_i with middle residue (a_i mod r in [2, r-2]).
usage: build_fitset.py seed n out.jsonl"""
import sys, random, json
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from excess import Inst, in_box
seed, n, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
random.seed(seed)
f = open(out, 'w')
cnt = 0
while cnt < n:
    typ = random.choice('ABCD')
    r = random.randint(4, 30)
    mids = list(range(2, r - 1))
    if typ == 'A':      # residue-pattern family, a_i = largest value <= 100 with that residue
        pat = [random.choice(list(range(1, r))) for _ in range(random.randint(1, 4))]
        if not any(2 <= s <= r - 2 for s in pat): pat.append(random.choice(mids))
        kmax = 60 if len(set(pat)) == 1 else 40
        k = random.randint(3, kmax)
        s = (pat * k)[:k]
        a = sorted(max(x for x in range(1, 101) if x % r == si) for si in s)
    elif typ == 'B':    # random a_i >= r
        k = random.randint(3, 40)
        a = sorted(random.choice([x for x in range(r, 101) if x % r]) for _ in range(k))
    elif typ == 'C':    # random a_i >= 2 (small values allowed)
        k = random.randint(3, 40)
        a = sorted(random.choice([x for x in range(2, 101) if x % r]) for _ in range(k))
    else:               # all equal
        k = random.randint(3, 60)
        v = random.choice([x for x in range(2, 101) if 2 <= x % r <= r - 2])
        a = [v] * k
    if sum(1 for x in a if 2 <= x % r <= r - 2) < 3 or not in_box(r, a):
        continue
    I = Inst(r, a)
    T6 = I.T6()
    U = [b for b in range(1, T6 + 3) if I.unimodal(b)]
    f.write(json.dumps(dict(typ=typ, r=r, a=a, F=I.F, T6=T6, U=U)) + "\n"); f.flush()
    cnt += 1
