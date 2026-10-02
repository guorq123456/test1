# TP_rho (and mu*_inf >= -r) sweep over the SAME residue ranges as sweep_results.txt (which recorded E_rho, O_rho via
# residue_check.check_rho). Together they give the full certificate of Theorem R. Writes sweep_tp.txt.
# Usage: python3 sweep_tp.py mode rmin rmax budget
import sys, itertools
from math import comb
from multiprocessing import Pool
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from residue_check2 import tp_rho, mu_lower_ok
def job(args):
    r, rho = args
    return (r, rho, tp_rho(r, list(rho)) and mu_lower_ok(r, list(rho)))
if __name__ == '__main__':
    mode, rmin, rmax = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 20000
    out = open('/tmp/claude-0/qu/explore2/R2E2/sweep_tp.txt', 'a')
    with Pool(4) as pool:
        for r in range(rmin, rmax + 1):
            if mode == 'all':
                kmax = 1
                while kmax < 40 and sum(comb(r - 2 + k, k) for k in range(1, kmax + 2)) <= budget: kmax += 1
                tasks = [(r, rho) for k in range(1, kmax + 1) for rho in itertools.combinations_with_replacement(range(1, r), k)]
                label = f"all k<={kmax}"
            else:
                tasks = [(r, (t,) * k) for t in range(1, r) for k in range(1, 61)]
                label = "equal t^k, k<=60"
            fails = [x[:2] for x in pool.imap_unordered(job, tasks, chunksize=64) if not x[2]]
            line = f"r={r} {label}: residue multisets {len(tasks)}, TP/mu failures {len(fails)} {fails[:5]}"
            print(line, flush=True); out.write(line + "\n"); out.flush()
