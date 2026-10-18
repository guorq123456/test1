"""D11 part 2 (registered in 0c353df; report only): D9's "end the turn now" bias y - p_now split by whether the mover
is the game's first player, and the mid-turn net's bias y - p_new on the same decisions (the builder's dumps).
Condition: the opponent's deck list is known (order and hand not).

    python3 d9split.py BUILDER_CHECKOUT --out d9split.json
"""
import argparse, gzip, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/home/user/test1"
SETS = [("ramp", "ramp-71600018", "analysis/scaling/data/gen4/rec/rec-71600018.jsonl.gz", "dump-mid-ramp-t/selfplay-mid.npz"),
        ("ramp", "ramp-75400038", "analysis/scaling/data/ramp-t4/rec/rec-75400038.jsonl.gz", "dump-mid-ramp-t/selfplay5-mid.npz"),
        ("elft", "elft-74100038", "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz", "dump-mid-elf-t/selfplay3-mid.npz"),
        ("elft", "elft-75500038", "analysis/scaling/data/elf-t4/rec/rec-75500038.jsonl.gz", "dump-mid-elf-t/selfplay4-mid.npz")]


def boot(rows, fn, reps=2000):
    games = sorted({r[0] for r in rows})
    by = {}
    for r in rows:
        by.setdefault(r[0], []).append(r)
    gl = [by[g] for g in games]
    rng = np.random.default_rng(0)
    vals = [fn([x for k in rng.integers(0, len(gl), len(gl)) for x in gl[k]]) for _ in range(reps)]
    return [float(fn(rows))] + [float(v) for v in np.percentile(vals, [2.5, 97.5])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("builder")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out, pooled = {}, {"ramp": [], "elft": [], "all": []}
    for deck, name, rec, dump in SETS:
        first = {}
        for line in gzip.open(os.path.join(ROOT, rec), "rt"):
            r = json.loads(line); first[r["g"]] = r["first"]
        d9 = json.load(gzip.open(os.path.join(HERE, "..", "d9", name + ".json.gz"), "rt"))["mid"]
        z = np.load(os.path.join(args.builder, "analysis/scaling/data/mid", dump))
        pnew = {(int(g), int(i)): (float(p), float(y)) for g, i, p, y in zip(z["g"], z["i"], z["p_new"], z["y"])}
        rows, ymis = [], 0
        for m in d9:
            pn, yn = pnew[(m["g"], m["i"])]
            ymis += yn != m["y"]
            # (game, first?, y - p_now, y - p_new)
            rows.append((f"{name}/{m['g']}", m["me"] == first[m["g"]], m["y"] - m["p_now"], m["y"] - pn))
        assert ymis == 0
        res = {"decisions": len(rows)}
        for lab, sel in (("first", [r for r in rows if r[1]]), ("second", [r for r in rows if not r[1]])):
            res[lab] = {"n": len(sel), "old": boot(sel, lambda xs: np.mean([x[2] for x in xs])),
                        "new": boot(sel, lambda xs: np.mean([x[3] for x in xs]))}
        f = lambda k: (lambda xs: np.mean([x[k] for x in xs if not x[1]]) - np.mean([x[k] for x in xs if x[1]]))
        res["second_minus_first"] = {"old": boot(rows, f(2)), "new": boot(rows, f(3))}
        out[name] = res
        pooled[deck] += rows; pooled["all"] += rows
        print(name, json.dumps(res))
    for k, rows in pooled.items():
        f = lambda j: (lambda xs: np.mean([x[j] for x in xs if not x[1]]) - np.mean([x[j] for x in xs if x[1]]))
        out["pooled-" + k] = {"decisions": len(rows),
                              "first_old": boot([r for r in rows if r[1]], lambda xs: np.mean([x[2] for x in xs])),
                              "second_old": boot([r for r in rows if not r[1]], lambda xs: np.mean([x[2] for x in xs])),
                              "first_new": boot([r for r in rows if r[1]], lambda xs: np.mean([x[3] for x in xs])),
                              "second_new": boot([r for r in rows if not r[1]], lambda xs: np.mean([x[3] for x in xs])),
                              "second_minus_first_old": boot(rows, f(2)), "second_minus_first_new": boot(rows, f(3))}
        print("pooled", k, json.dumps(out["pooled-" + k]))
    json.dump(out, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
