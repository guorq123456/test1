"""The net's search path before and after a speed change gives the same logits, to the last bit (the architecture
thread 20:57Z). Condition: the opponent's deck list is known (order and hand not).

    python analysis/scaling/speedcheck.py --old REV --records RECDIR --net analysis/scaling/models/net-10000.npz

Loads learn.setnet as of git revision REV beside the current one and compares SetNet.logit on
- every turn end of the first --games holdout games (s = 70200000), and
- every position the search scores with the net during --decisions decisions of v2skx+setnet (the positions the
  current net path is asked about inside the search, kept as copies),
with ==. Prints the counts and the number of differences; exit 1 if any.
"""
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse      # noqa: E402
import gzip          # noqa: E402
import importlib.util  # noqa: E402
import json          # noqa: E402
import subprocess    # noqa: E402
import sys           # noqa: E402
import tempfile      # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.learn import setnet as new
    from svsim.learn.netdata import ENDED, rows
    from svsim.learn.scaledata import SPEC
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--records", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--decisions", type=int, default=30)
    args = ap.parse_args()
    src = subprocess.run(["git", "show", f"{args.old}:svsim/learn/setnet.py"], cwd=ROOT, capture_output=True,
                         check=True).stdout
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "setnet_old.py"
        path.write_bytes(src)
        spec = importlib.util.spec_from_file_location("setnet_old", path)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
    net_new, net_old = new.SetNet.load(args.net), old.SetNet.load(args.net)
    recs = []
    with gzip.open(Path(args.records) / "rec-70200000.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            recs.append(json.loads(line))
            if len(recs) >= args.games:
                break
    positions = [(s, p) for r in recs for ph, p, s, _ in rows(r) if ph == ENDED]
    turn_ends = len(positions)
    seen = []                                         # what the search asks the net (copies), current path
    plain = new.SetNet.logit

    def keep(self, state, player):
        seen.append((state.clone(), player))
        return plain(self, state, player)
    new.SetNet.logit = keep
    starts = []
    for r in recs[:10]:
        done = set()
        for s, _ in R.steps(r):
            if s.phase == Phase.MAIN and (s.active, s.turn) not in done and s.turn >= 3:
                done.add((s.active, s.turn))
                starts.append(s.clone())
    for i, s in enumerate(starts[:args.decisions]):
        make_agent(f"{SPEC}+setnet={args.net}", 1000 + i).act(s.clone(), legal_actions(s))
    new.SetNet.logit = plain
    positions += seen
    diff = sum(net_new.logit(s, p) != net_old.logit(s, p) for s, p in positions)
    out = {"old": args.old, "turn_ends": turn_ends, "search_positions": len(seen), "compared": len(positions),
           "different": int(diff)}
    print(json.dumps(out))
    sys.exit(1 if diff else 0)


if __name__ == "__main__":
    main()
