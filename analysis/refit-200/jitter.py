"""Line C diagnostic: how much an evaluator's win chance moves with the turn-start draw.

    cd <svsim checkout with the models> && PYTHONPATH=. python3 <this> --games ramp-t_ramp-t-s200.jsonl.gz \
        --every 11 A200=<dir>/ramp-t-ramp-t C1=... C2=... A100=... [--k 8] [--boot 1000]

Positions: in the held-out games (line number % every == 0), every moment where the opponent of the evaluated
side is about to end its turn (the record's EndTurn, both seats taking turns as the evaluated side). At each, K
determinizations from the evaluated side's view (its own deck order and the opponent's hand reshuffled,
svsim.core.view.determinize), the opponent's EndTurn applied (the evaluated side's turn starts and it draws),
and every evaluator's model of the chosen moment (--moment, default "ended": the one v2s's search reads at turn
ends and inside a turn; "act" is read only by the reply-playing search) gives the evaluated side a win chance; the standard deviation over the K is
that position's jitter. Reported: each evaluator's mean jitter over all positions, and each minus the first
(paired on the same positions and determinizations), games resampled for the interval. A diagnostic only.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import math
import random
import statistics
import sys
from multiprocessing import Pool

_M = None


MOMENT = "ended"


def load(prefix, moment):
    from pathlib import Path
    from svsim.learn.model import LinearValue
    return LinearValue.load(Path(f"{prefix}-{moment}.json"))


def game(job):
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.core.view import determinize
    from svsim.tools import records
    line, specs, k, moment = job
    global _M
    if _M is None:
        _M = {n: load(p, moment) for n, p in specs}
    rec = json.loads(line)
    st = records.start(rec)
    out = []
    for i, a in enumerate(rec["actions"]):
        act = from_dict(a)
        if isinstance(act, EndTurn) and not st.over:
            p = 1 - st.active                     # the side whose turn starts next
            vals = {n: [] for n in _M}
            for j in range(k):
                d = determinize(st, p, random.Random(rec["seed"] * 1000 + i * 10 + j))
                apply(d, EndTurn())
                if d.over or d.active != p:
                    break
                for n, m in _M.items():
                    z = m.logit(d, p)
                    vals[n].append(1 / (1 + math.exp(-max(min(z, 60.0), -60.0))))
            if all(len(v) == k for v in vals.values()):
                out.append({"g": rec.get("g"), "sd": {n: statistics.pstdev(v) for n, v in vals.items()}})
        apply(st, act)
    return out


def main():
    arg = lambda key, d=None: sys.argv[sys.argv.index(key) + 1] if key in sys.argv else d
    specs = [tuple(a.split("=", 1)) for a in sys.argv[1:] if "=" in a and not a.startswith("--")]
    every, k, nboot = int(arg("--every", "11")), int(arg("--k", "8")), int(arg("--boot", "1000"))
    moment = arg("--moment", MOMENT)
    lines = [l for i, l in enumerate(gzip.open(arg("--games"), "rt", encoding="utf-8")) if every and i % every == 0]
    with Pool(int(arg("--workers", "4"))) as pool:
        rows = [r for part in pool.imap(game, [(l, specs, k, moment) for l in lines], chunksize=2) for r in part]
    names = [n for n, _ in specs]
    print(f"条件：对手卡表已知（牌序、手牌未知）。留出 {len(lines)} 局，{len(rows)} 个「对手正要结束回合」的局面；"
          f"每个局面 {k} 个确定化（自己牌库顺序和对手手牌重洗），对手结束回合、被评估方开回合抽牌后用 {moment} 模型估胜率，取标准差。"
          f"只作诊断。区间 95%，按局重抽 {nboot} 次。\n")
    print("| 评估器 | 平均标准差 | 减 " + names[0] + "（95%） |")
    print("|---|---|---|")
    by = {}
    for r in rows:
        by.setdefault(r["g"], []).append(r)
    keys = list(by)
    rng = random.Random(17)
    for n in names:
        m = sum(r["sd"][n] for r in rows) / len(rows)
        if n == names[0]:
            print(f"| {n} | {m:.4f} | — |")
            continue
        d = m - sum(r["sd"][names[0]] for r in rows) / len(rows)
        bs = []
        for _ in range(nboot):
            s = [r for _ in keys for r in by[keys[rng.randrange(len(keys))]]]
            bs.append(sum(r["sd"][n] - r["sd"][names[0]] for r in s) / len(s))
        bs.sort()
        print(f"| {n} | {m:.4f} | {d:+.4f}（{bs[int(0.025 * nboot)]:+.4f}～{bs[int(0.975 * nboot) - 1]:+.4f}） |")


if __name__ == "__main__":
    main()
