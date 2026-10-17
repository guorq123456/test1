"""D7 (architecture thread 11:33Z): what the recorded search visits look like, for a possible learned move prior.
Read-only: parses the self-play records; replays a sample of decision points to check that "visits" lines up with
legal_actions(state). Condition: the opponent's deck list is known (order and hand not).

    python3 d7_survey.py --out d7.json          # run with PYTHONPATH = a checkout (for the replay check)
"""
import argparse, gzip, glob, json, math, os, random
from multiprocessing import Pool
import numpy as np

MINE = "/home/user/test1/analysis/scaling/data"
THEIRS = "/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/wt_eg3/analysis/scaling/data"
BATCHES = {
    "ramp v2skx 1e5 (rec)": ["rec"],
    "ramp v2skx holdout": ["heldout"],
    "ramp gen2": ["gen2/rec"],
    "ramp gen3": ["gen3/rec"],
    "ramp gen4": ["gen4/rec"],
    "ramp gen4x": ["gen4x/rec"],
    "elf-t v2skx (rec + holdout)": ["elf-t/rec", "elf-t/heldout"],
    "elf-t2": ["elf-t2/rec"],
    "elf-t3": ["elf-t3/rec"],
}


def files(dirs):
    out = {}
    for d in dirs:
        for root in (MINE, THEIRS):
            for f in glob.glob(os.path.join(root, d, "rec-*.jsonl.gz")):
                out.setdefault(os.path.basename(f), f)
    return [out[k] for k in sorted(out)]


def scan(path):
    rows = []                    # (g, i, n, total, top_share, entropy, norm_entropy, top_is_last, chosen_is_top)
    for line in gzip.open(path, "rt"):
        if not line.strip():
            continue
        r = json.loads(line)
        for i, (a, s) in enumerate(zip(r["actions"], r.get("search") or [])):
            if not s or "visits" not in s or a.get("type") == "Mulligan":
                continue
            v = s["visits"]
            n, tot = len(v), sum(v)
            if tot <= 0:
                rows.append((r["g"], i, n, tot, None, None, None, None))
                continue
            p = np.asarray(v, float) / tot
            nz = p[p > 0]
            h = float(-(nz * np.log(nz)).sum())
            top = int(np.argmax(v))
            rows.append((r["g"], i, n, tot, float(p.max()), h, h / math.log(n) if n > 1 else None, top == n - 1))
    return os.path.basename(path), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", type=int, default=25, help="decision points replayed per batch")
    args = ap.parse_args()
    rep = {"condition": "对手卡表已知（牌序、手牌未知）", "batches": {}}
    allpoints = {}
    with Pool(4) as pool:
        for name, dirs in BATCHES.items():
            fl = files(dirs)
            res = pool.map(scan, fl)
            pts = [(f, *row) for f, rows in res for row in rows]
            good = [x for x in pts if x[5] is not None]
            n = np.array([x[3] for x in good]); share = np.array([x[5] for x in good]); ent = np.array([x[6] for x in good])
            nent = np.array([x[7] for x in good if x[7] is not None]); last = np.array([x[8] for x in good])
            games = sum(sum(1 for l in gzip.open(f, "rt") if l.strip()) for f in fl)
            rep["batches"][name] = {
                "files": len(fl), "first": os.path.basename(fl[0]) if fl else None, "last": os.path.basename(fl[-1]) if fl else None,
                "games": games, "decisions_with_visits": len(pts), "zero_total": len(pts) - len(good),
                "per_game": round(len(pts) / max(games, 1), 2),
                "legal_median": float(np.median(n)), "legal_p90": float(np.percentile(n, 90)), "legal_mean": round(float(n.mean()), 2),
                "visits_total_median": float(np.median([x[4] for x in good])),
                "top_share_mean": round(float(share.mean()), 4), "top_share_median": round(float(np.median(share)), 4),
                "top_share_over_half": round(float((share > 0.5).mean()), 4),
                "entropy_mean_nats": round(float(ent.mean()), 4), "entropy_norm_mean": round(float(nent.mean()), 4),
                "top_is_endturn": round(float(last.mean()), 4),
            }
            allpoints[name] = good
            print(name, json.dumps(rep["batches"][name], ensure_ascii=False), flush=True)
    # replay check: `sample` points per batch, random.Random(0)
    from svsim.core.engine import legal_actions
    from svsim.core.actions import EndTurn, from_dict
    from svsim.tools import records as R
    rng = random.Random(0)
    check = {"points": 0, "len_match": 0, "endturn_last": 0, "chosen_is_top": 0, "chosen_has_visits": 0, "mismatches": []}
    paths = {os.path.basename(f): f for dirs in BATCHES.values() for f in files(dirs)}
    for name, good in allpoints.items():
        for f, g, i, *_ in rng.sample(good, min(args.sample, len(good))):
            rec = next(json.loads(l) for l in gzip.open(paths[f], "rt") if l.strip() and json.loads(l)["g"] == g)
            for j, (state, action) in enumerate(R.steps(rec)):
                if j == i:
                    legal = legal_actions(state)
                    v = rec["search"][i]["visits"]
                    check["points"] += 1
                    ok = len(legal) == len(v)
                    check["len_match"] += ok
                    check["endturn_last"] += isinstance(legal[-1], EndTurn)
                    if ok:
                        k = next((x for x, a in enumerate(legal) if repr(a) == repr(action)), None)
                        check["chosen_has_visits"] += k is not None and v[k] > 0
                        check["chosen_is_top"] += k is not None and v[k] == max(v)
                    else:
                        check["mismatches"].append({"batch": name, "file": f, "g": g, "i": i, "legal": len(legal), "visits": len(v)})
                    break
    rep["replay_check"] = check
    json.dump(rep, open(args.out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(check, ensure_ascii=False))


if __name__ == "__main__":
    main()
