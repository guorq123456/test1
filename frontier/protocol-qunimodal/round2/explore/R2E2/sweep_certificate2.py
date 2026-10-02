# Sweep the FULL residue certificate (TP, E, O, mu*_inf>=-r) over residue multisets; writes sweep_results2.txt.
#  mode 'all' : all multisets of residues in [1,r-1] with k <= kmax(r), kmax chosen by a count budget (k<=40)
#  mode 'equal': (t^k), t in [1,r-1], k <= 60
# Usage: python3 sweep_certificate2.py mode rmin rmax budget
import sys, itertools
from math import comb
from multiprocessing import Pool
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from residue_check2 import full_check
def job(args):
    r, rho = args
    return (r, rho, full_check(r, list(rho)))
if __name__ == '__main__':
    mode, rmin, rmax = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 20000
    out = open('/tmp/claude-0/qu/explore2/R2E2/sweep_results2.txt', 'a')
    with Pool(4) as pool:
        for r in range(rmin, rmax + 1):
            tasks = []
            if mode == 'all':
                kmax = 1
                while kmax < 40 and sum(comb(r - 2 + k, k) for k in range(1, kmax + 2)) <= budget: kmax += 1
                for k in range(1, kmax + 1):
                    tasks += [(r, rho) for rho in itertools.combinations_with_replacement(range(1, r), k)]
                label = f"all k<={kmax}"
            else:
                for t in range(1, r):
                    tasks += [(r, (t,) * k) for k in range(1, 61)]
                label = "equal t^k, k<=60"
            fails = [x[:2] for x in pool.imap_unordered(job, tasks, chunksize=16) if not x[2]]
            line = f"r={r} {label}: residue multisets {len(tasks)}, full-certificate failures {len(fails)} {fails[:5]}"
            print(line, flush=True); out.write(line + "\n"); out.flush()
