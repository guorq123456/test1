"""Smoke test after installing "strong + lethal-clock evaluator + discard pruning" (analysis/install/strong_kc_xprune.py
apply): level strong plays itself for 2 pairs of the original Ramp mirror and 1 pair of 机锋 (nemesis-t) against 旗皇
(pirate-t), with tools.gate's own game function. Checks:
- every game finishes;
- in the Ramp games the pruning cuts at least one discard choice;
- level strong's Ramp-mirror turn-end model is pkg-kc-ramp-ramp's (cand-kc's), and level max's is still the
  installed one (svsim/learn/phased_models/ramp-ramp-ended.json).
Condition: the opponent's deck list is known (order and hand not).

    python -m svsim.tools.host analysis.install.strong_kc_xprune_smoke --workers 3

Prints which turn-end model each level reads, one line per game (pairing, seat, result, actions, discard choices cut),
then "OK" or "FAILED"; exit 1 on a failure.
"""
import argparse
import json
import sys
from pathlib import Path

PAIRS = [("ramp", "ramp", 69900001), ("ramp", "ramp", 69900002), ("nemesis-t", "pirate-t", 69900003)]
MODELS = Path(__file__).resolve().parents[2] / "svsim/learn/phased_models"


def evaluator(spec):
    """Which Ramp-mirror turn-end model the agent `spec` reads: "pkg-kc-ramp-ramp", "installed" or "other"."""
    from svsim.learn.model import LinearValue
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    model = _search(make_agent(spec, 0)).weights.models[("ramp", "ramp", "ended")]
    coef = list(model.coef)
    if coef == list(LinearValue.load(MODELS / "pkg-kc-ramp-ramp/ramp-ramp-ended.json").coef):
        return "pkg-kc-ramp-ramp"
    if coef == list(LinearValue.load(MODELS / "ramp-ramp-ended.json").coef):
        return "installed"
    return "other"


def _pair(job):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import strong_xprune_smoke as base
    return base._pair(job)


def main():
    from multiprocessing import Pool
    from svsim.ui.session import LEVELS
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    ev = {"strong": evaluator("level-strong"), "max": evaluator("level-max")}
    print(json.dumps({"strong_spec": LEVELS["strong"], "max_spec": LEVELS["max"], "ramp_ramp_ended_read_by": ev},
                     ensure_ascii=False))
    with Pool(min(args.workers, len(PAIRS))) as pool:
        rows = [r for rs in pool.map(_pair, PAIRS) for r in rs]
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    ok = (all(r["winner"] is not None for r in rows) and "xprune" in LEVELS["strong"]
          and "pkg-kc-ramp-ramp" in LEVELS["strong"]
          and sum(r["cut"] for r in rows if r["pairing"] == "ramp / ramp") > 0
          and ev == {"strong": "pkg-kc-ramp-ramp", "max": "installed"})
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
