import json, sys
from multiprocessing import Pool
sys.path.insert(0, sys.argv[1])
import c1_run as R
R.D = sys.argv[1]
def job(cfg):
    R.load()
    return R.grid_job(cfg)
if __name__ == "__main__":
    grid = [(mu, l2, "zero") for mu in (0.01, 0.03) for l2 in (0.0, 1e-5, 1e-4)]
    with Pool(4) as p:
        for r in p.imap_unordered(job, grid):
            print(json.dumps(r), flush=True)
