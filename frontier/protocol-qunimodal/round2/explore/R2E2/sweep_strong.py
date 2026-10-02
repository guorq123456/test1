# Sweep the STRONG residue certificate (TP, E+, O+) over rho' with parts in [2,r-1]; writes sweep_strong.txt.
# A pass for rho' proves S2 for every a whose residues != 1 (mod r) form rho' (any number of residue-1 parts, any sizes).
# Usage: python3 sweep_strong.py rmin rmax budget   (k' <= kmax(r) chosen by count budget, k' <= 40)
import sys, itertools
from math import comb
from multiprocessing import Pool
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from strong_check import strong
def job(args):
    r, rho = args
    e, o, t = strong(r, list(rho))
    return (r, rho, e and o and t)
if __name__ == '__main__':
    rmin, rmax, budget = map(int, sys.argv[1:4])
    out = open('/tmp/claude-0/qu/explore2/R2E2/sweep_strong.txt', 'a')
    with Pool(4) as pool:
        for r in range(max(rmin, 3), rmax + 1):
            kmax = 1
            while kmax < 40 and sum(comb(r - 3 + k, k) for k in range(1, kmax + 2)) <= budget: kmax += 1
            tasks = [(r, rho) for k in range(1, kmax + 1) for rho in itertools.combinations_with_replacement(range(2, r), k)]
            eq = [(r, (t,) * k) for t in range(2, r) for k in range(kmax + 1, 61)]
            fails = [x[:2] for x in pool.imap_unordered(job, tasks + eq, chunksize=16) if not x[2]]
            line = f"r={r} rho' all k'<={kmax} plus equal (t^k'), k'<=60: count {len(tasks)+len(eq)}, strong-certificate failures {len(fails)} {fails[:5]}"
            print(line, flush=True); out.write(line + "\n"); out.flush()
