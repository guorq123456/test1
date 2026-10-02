# Sweep the residue-level certificate (E_rho) & (O_rho) over many residue multisets.
#  mode 'all'  : all multisets of residues in [1,r-1] with k <= kmax(r) (count budget per r)
#  mode 'equal': all equal-residue multisets (t^k), k <= 60, r <= 30
# Writes one summary line per (r, mode) to sweep_results.txt.  Usage: python3 sweep_certificate.py mode rmin rmax budget
import sys, itertools
from math import comb
from multiprocessing import Pool
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from residue_check import check_rho

def job(args):
    r, rho = args
    okE, okO, ms = check_rho(r, list(rho))
    return (r, rho, okE, okO)

if __name__ == '__main__':
    mode, rmin, rmax = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 20000
    out = open('/tmp/claude-0/qu/explore2/R2E2/sweep_results.txt', 'a')
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
            fails = [x for x in pool.imap_unordered(job, tasks, chunksize=16) if not (x[2] and x[3])]
            line = f"r={r} {label}: residue multisets {len(tasks)}, certificate failures {len(fails)} {fails[:5]}"
            print(line, flush=True); out.write(line + "\n"); out.flush()
