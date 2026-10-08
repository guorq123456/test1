"""Line A / C: log loss and accuracy of evaluators on the held-out games (line number % K == 0), against the
game's result only, with game-resampled intervals for the differences.

    cd <svsim checkout with learn.netdata.rows and the models> && PYTHONPATH=. python3 <this> \
        --games ramp-t_ramp-t-s200.jsonl.gz --every 11 \
        B=svsim/learn/phased_models/ramp-ramp  A200=<dir>/ramp-t-ramp-t ... [--boot 2000] [--out rows.jsonl] \
        [--side elf-t-nemesis-t]

Each NAME=PREFIX names an evaluator by its two files PREFIX-ended.json and PREFIX-act.json (learn.model
.LinearValue; a model with "extras" reads its named feature sets itself). Every held-out game is replayed with
learn.netdata.rows (the same positions the fit uses: both seats, the turn's end and the moments in a turn); each
position is scored by every evaluator, p = 1 / (1 + exp(-logit)), against the result (draws left out, as in the
fit). Reported per evaluator and moment: positions, log loss, accuracy; then each evaluator minus the first, the
difference of log loss with its 95% interval (games resampled).
--side <mine>-<theirs> (a pairing that is not a mirror, or to be explicit): only the positions of the seat that
played <mine> against <theirs>, by the record's "names", as learn.phased --matchup keeps for the fit; without it
both seats count (the ramp-t mirror).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import math
import random
import sys
from multiprocessing import Pool

_MODELS = None


def load(prefix):
    from pathlib import Path
    from svsim.learn.model import LinearValue
    out = {}
    for moment in ("ended", "act"):
        out[moment] = LinearValue.load(Path(f"{prefix}-{moment}.json"))
    return out


def game_rows(job):
    from svsim.learn.netdata import ACT, rows
    line, specs, side = job
    global _MODELS
    if _MODELS is None:
        _MODELS = {name: load(prefix) for name, prefix in specs}
    rec = json.loads(line)
    out = []
    names = rec.get("names")
    for phase, me, state, result, q in rows(rec, with_search=True):
        if result not in (0, 1, 0.0, 1.0):
            continue
        if side is not None and names and (names[me], names[1 - me]) != side:
            continue
        moment = "act" if phase == ACT else "ended"
        ps = {}
        for name, m in _MODELS.items():
            z = m[moment].logit(state, me)
            ps[name] = 1 / (1 + math.exp(-max(min(z, 60.0), -60.0)))
        out.append({"g": rec.get("g"), "moment": moment, "y": float(result), "p": ps})
    return out


def logloss(rows, name):
    eps = 1e-9
    return -sum(r["y"] * math.log(max(r["p"][name], eps)) + (1 - r["y"]) * math.log(max(1 - r["p"][name], eps))
                for r in rows) / len(rows)


def acc(rows, name):
    return sum((r["p"][name] > 0.5) == (r["y"] > 0.5) for r in rows) / len(rows)


def main():
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    specs = [tuple(a.split("=", 1)) for a in sys.argv[1:] if "=" in a and not a.startswith("--")]
    every = int(arg("--every", "11"))
    nboot = int(arg("--boot", "2000"))
    side = None
    if arg("--side"):
        from svsim.learn.model import split_keys
        side = tuple(split_keys(arg("--side")))
        assert all(isinstance(k, str) for k in side), "--side takes two named decks"
    lines = [l for i, l in enumerate(gzip.open(arg("--games"), "rt", encoding="utf-8")) if every and i % every == 0]
    with Pool(int(arg("--workers", "4"))) as pool:
        rows = [r for part in pool.imap(game_rows, [(l, specs, side) for l in lines], chunksize=4) for r in part]
    if arg("--out"):
        with open(arg("--out"), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    names = [n for n, _ in specs]
    who = f"只取 {side[0]} 对 {side[1]} 那一侧；" if side else ""
    print(f"条件：对手卡表已知（牌序、手牌未知）。留出 {len(lines)} 局（行号 % {every} == 0），{who}按终局胜负算，平局不计；区间 95%，按局重抽 {nboot} 次。\n")
    print("| 评估器 | 时刻 | 局面数 | 对数损失 | 判对率 |")
    print("|---|---|---|---|---|")
    for moment in ("ended", "act"):
        sub = [r for r in rows if r["moment"] == moment]
        for n in names:
            print(f"| {n} | {moment} | {len(sub)} | {logloss(sub, n):.4f} | {acc(sub, n):.1%} |")
    if len(names) > 1:
        print(f"\n**对数损失差（减 {names[0]}；负的是更好）**\n")
        print("| 评估器 | ended | act |")
        print("|---|---|---|")
        rng = random.Random(17)
        for n in names[1:]:
            cells = []
            for moment in ("ended", "act"):
                sub = [r for r in rows if r["moment"] == moment]
                by = {}
                for r in sub:
                    by.setdefault(r["g"], []).append(r)
                keys = list(by)
                d = logloss(sub, n) - logloss(sub, names[0])
                bs = []
                for _ in range(nboot):
                    s = [r for _ in keys for r in by[keys[rng.randrange(len(keys))]]]
                    bs.append(logloss(s, n) - logloss(s, names[0]))
                bs.sort()
                cells.append(f"{d:+.4f}（{bs[int(0.025 * nboot)]:+.4f}～{bs[int(0.975 * nboot) - 1]:+.4f}）")
            print(f"| {n} | {cells[0]} | {cells[1]} |")


if __name__ == "__main__":
    main()
