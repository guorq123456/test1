"""The hidden-layer logit rewritten in numpy (learn.model.LinearValue._logit_hidden): the old and new code on the same
ENDED positions of step-1 self-play. Largest logit difference for cand-nl (the old code is a saved copy of
learn/model.py, OLD_MODEL_PY), bit-for-bit check for models without a hidden layer (the installed one, cand-kc), and
microseconds per logit (interleaved rounds, median). Condition: the opponent's deck list is known (order and hand
not).
usage: nl_logit_check.py STEP1_DIR OLD_MODEL_PY [GAMES] [ROUNDS]"""
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
P = ROOT / "svsim/learn/phased_models"


def main():
    d, old_py = sys.argv[1], sys.argv[2]
    games = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    rounds = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    from svsim.learn.model import LinearValue as New
    from svsim.learn.netdata import ENDED, rows
    spec = importlib.util.spec_from_file_location("model_old", old_py)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    Old = old.LinearValue
    recs = list(SD._lines(f"{d}/selfplay.jsonl"))[:games]
    ends = [(st, me) for rec in recs for ph, me, st, res in rows(rec) if ph == ENDED]
    files = {"installed": ROOT / "svsim/learn/phased_models/ramp-ramp-ended.json",
             "cand-kc": P / "cand-kc-ramp-ramp/ramp-ramp-ended.json",
             "cand-nl": P / "cand-nl-ramp-ramp/ramp-ramp-ended.json"}
    out = {"turn ends": len(ends)}
    models = {}
    for name, f in files.items():
        o, n = Old.load(f), New.load(f)
        a = [o.logit(st, me) for st, me in ends]
        b = [n.logit(st, me) for st, me in ends]
        out[name] = {"bit-identical": a == b, "max |old - new|": max(abs(x - y) for x, y in zip(a, b))}
        models[name] = (o, n)
    times = {f"{name} {w}": [] for name in files for w in ("old", "new")}
    for _ in range(rounds):
        for name, (o, n) in models.items():
            for w, m in (("old", o), ("new", n)):
                t = time.perf_counter()
                for st, me in ends:
                    m.logit(st, me)
                times[f"{name} {w}"].append(1e6 * (time.perf_counter() - t) / len(ends))
    out["us per logit (median)"] = {k: round(statistics.median(v), 1) for k, v in times.items()}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
