"""Replay chosen games of NM1 self-play shards and compare them with the files (scaledata's own check: the whole
record after a JSON round trip, without the volatile fields date and cpu).

    python replay_check.py --dir DIR --g 0 333 666 999 [--deck ramp-t --opponent elf-t] [--workers 3]
"""
import argparse
import glob
import gzip
import json
import os
from multiprocessing import Pool

from svsim.learn.scaledata import SPEC, _play, _stable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--g", type=int, nargs="+", required=True)
    ap.add_argument("--deck", default="ramp-t")
    ap.add_argument("--opponent", default="elf-t")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    want, jobs = {}, []
    for path in sorted(glob.glob(os.path.join(args.dir, "rec-*.jsonl.gz"))):
        seed = int(os.path.basename(path)[4:-9])
        for line in gzip.open(path, "rt", encoding="utf-8"):
            r = json.loads(line)
            if r["g"] in args.g:
                want[(seed, r["g"])] = _stable(r)
        jobs += [(seed, g, args.deck, args.opponent, SPEC) for g in args.g]
    same = 0
    with Pool(args.workers) as pool:
        for job, (seed, rec) in zip(jobs, pool.imap(_play, jobs)):
            ok = _stable(json.loads(json.dumps(rec))) == want[(seed, job[1])]
            same += ok
            print(seed, job[1], "same" if ok else "DIFFERENT", flush=True)
    print(json.dumps({"games": len(jobs), "same": same}))


if __name__ == "__main__":
    main()
