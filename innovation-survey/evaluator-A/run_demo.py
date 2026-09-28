"""End-to-end demo: baselines -> evolutionary search -> ONE sealed evaluation.

用法 / Usage:
    python run_demo.py --csv /path/to/covtype.csv --dev-rows 60000 --evals 16
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forest_eval import ForestEvaluator, load_covertype
from forest_eval.candidates import build
from forest_eval.search import evolve

BASELINES = {
    "logreg_raw": {"model": "logreg", "features": (), "params": {"C": 1.0, "class_weight": None}, "seed": 0},
    "rf_raw": {"model": "rf", "features": (), "params": {"n_estimators": 200, "max_depth": None, "min_samples_leaf": 1, "class_weight": None}, "seed": 0},
    "hgb_raw": {"model": "hgb", "features": (), "params": {"max_iter": 200, "learning_rate": 0.1, "max_leaf_nodes": 31, "l2": 0.0, "class_weight": None}, "seed": 0},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default="results")
    ap.add_argument("--dev-rows", type=int, default=60_000)
    ap.add_argument("--evals", type=int, default=16)
    ap.add_argument("--time-budget", type=float, default=None)
    ap.add_argument("--skip-sealed", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    splits = load_covertype(args.csv, max_dev_rows=args.dev_rows)
    print(splits.describe(), flush=True)
    ev = ForestEvaluator(splits, log_path=out / "audit_log.jsonl", sealed_budget=3)

    print("\n== baselines ==", flush=True)
    for name, cfg in BASELINES.items():
        r = ev.evaluate(build, cfg, note=f"baseline:{name}")
        print(f"{name:12s} iid_f1={r.iid_macro_f1:.3f} acc={r.iid_accuracy:.3f} "
              f"transfer_f1={r.transfer_macro_f1:.3f} per_area={ {k: round(v,3) for k,v in r.transfer_per_area.items()} } "
              f"({r.fit_seconds:.0f}s)", flush=True)

    print("\n== evolutionary search (searcher sees only transfer F1) ==", flush=True)
    elite = evolve(ev, n_evals=args.evals, time_budget_s=args.time_budget, seed=1)
    best_cfg, best_dev = elite[0]
    print("\nbest dev candidate:", json.dumps(best_cfg, default=list), flush=True)

    lb = ev.leaderboard(top=10)
    lb.to_csv(out / "leaderboard.csv", index=False)
    print("\n== leaderboard (dev, by transfer F1) ==")
    print(lb.to_string(index=False))

    if not args.skip_sealed:
        print("\n== sealed evaluation (1 of 3 budget) ==", flush=True)
        rs = ev.evaluate_sealed(build, best_cfg, note="best-by-transfer")
        rb = ev.evaluate_sealed(build, BASELINES["hgb_raw"], note="baseline hgb_raw for reference")
        for tag, r in (("best", rs), ("hgb_raw", rb)):
            print(f"{tag:8s} sealed macro-F1={r.sealed_macro_f1:.3f} acc={r.sealed_accuracy:.3f} "
                  f"per_area={ {k: round(v,3) for k,v in r.transfer_per_area.items()} }")
        summary = {
            "best_config": best_cfg,
            "best_dev": best_dev.to_json(),
            "best_sealed": rs.to_json(),
            "baseline_sealed": rb.to_json(),
        }
        (out / "summary.json").write_text(json.dumps(summary, indent=2, default=list))


if __name__ == "__main__":
    main()
