"""Does setting a net's subnormal weights to 0 (+netftz) change any of its numbers, and how much time does it save?
(The architecture thread 2026-10-16 04:30Z, R2.) Condition: the opponent's deck list is known (order and hand not).

    python analysis/scaling/ftzcheck.py --net analysis/scaling/models/net-gen2-20000.npz --tokens TOKDIR --records RECDIR

- how many subnormal weights the net has;
- the batch pass (SetNet.predict's logits) on every holdout turn end (the 5 tok-702000xx files), as loaded and with
  the subnormals set to 0, compared with ==;
- the search's single-position path (SetNet.logit) on every holdout turn end, replayed from the records (rows,
  phase ENDED), the same comparison;
- the time of that single-position path over all of them, both ways (one process).
Prints one JSON line; exit 1 if any logit differs.
"""
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import gzip      # noqa: E402
import json      # noqa: E402
import sys       # noqa: E402
import time      # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    from svsim.learn.netdata import ENDED, rows
    from svsim.learn.setnet import Data, SetNet, _TINY
    import train as T
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True)
    ap.add_argument("--tokens", required=True)
    ap.add_argument("--records", required=True)
    args = ap.parse_args()
    plain, flushed = SetNet.load(args.net), SetNet.load(args.net)
    sub = sum(int(((getattr(plain, k) != 0) & (np.abs(getattr(plain, k)) < _TINY)).sum()) for k in SetNet.PARAMS)
    n0 = flushed.flush_subnormals()
    tok = Path(args.tokens)
    h = T._align(plain, Data([tok / f"tok-{s}.npz" for s in T.HOLDOUT], tok / "cards.npz"))
    zb = [net.forward(*h.batch(np.arange(i, min(i + 1024, h.n)))) for net in (plain, flushed)
          for i in range(0, h.n, 1024)]
    half = len(zb) // 2
    batch_a, batch_b = np.concatenate(zb[:half]), np.concatenate(zb[half:])
    states = []
    for s in T.HOLDOUT:
        with gzip.open(Path(args.records) / f"rec-{s}.jsonl.gz", "rt", encoding="utf-8") as fh:
            for line in fh:
                states += [(st, p) for ph, p, st, _ in rows(json.loads(line)) if ph == ENDED]
    times, single = {}, {}
    for name, net in (("as_loaded", plain), ("subnormals_0", flushed)):
        net.logit(*states[0])
        t0 = time.perf_counter()
        single[name] = np.array([net.logit(st, p) for st, p in states])
        times[name] = round((time.perf_counter() - t0) / len(states) * 1e3, 4)
    out = {"net": args.net, "subnormal_weights": sub, "set_to_0": n0, "holdout_turn_ends": int(h.n),
           "batch_differ": int((batch_a != batch_b).sum()),
           "single_path_positions": len(states), "single_differ": int((single["as_loaded"] != single["subnormals_0"]).sum()),
           "single_vs_batch_max": float(np.max(np.abs(single["as_loaded"] - batch_a))) if len(states) == h.n else None,
           "ms_per_logit": times}
    print(json.dumps(out))
    sys.exit(1 if out["batch_differ"] or out["single_differ"] else 0)


if __name__ == "__main__":
    main()
