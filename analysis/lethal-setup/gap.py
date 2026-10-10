"""Two small measurements (README-gap.md): (1) how much of the operations gap level-strong and mcts:1043 close on
the 6 big-gap starts; (2) level-strong vs mcts:1043 root disagreement by root legal-move count on self-play decisions.
Condition: the opponent's deck list is known (order and hand not).

    python gap.py t2sample <stage-0 dir> --out gap/t2_sample.json
    python -m svsim.tools.host gap t2run <stage-0 dir> --sample gap/t2_sample.json --out gap/t2_rows.jsonl --workers 3
    python gap.py t2read gap/t2_rows.jsonl --sample gap/t2_sample.json --out gap/t2.txt
    python -m svsim.tools.host gap t1run <stage-0 dir> --out gap/t1_rows.jsonl --workers 3
    python gap.py t1read gap/t1_rows.jsonl --out gap/t1.txt
"""
import argparse
import json
import math
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "turn-level"))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))
import setup_prob as SP          # noqa: E402
import turn_level as TL          # noqa: E402

STRONG, DEEP, SPEC = "level-strong", "mcts:1043+plan+learned+phased", "mcts:100+plan+learned+phased"
STARTS = (320, 518, 445, 313, 455, 329)
T1_TURN, T1_PLAY, T1_K, T1_SEEDS = 67300000, 67350000, 48, 8
T2_SAMPLE, T2_AGENT, T2_N = 67320000, 67330000, 2000


# ---- 2: disagreement by root legal-move count ----

def _decisions(step0):
    """(game, action index, legal moves) of every main-phase decision with at least 2 legal moves."""
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.tools import records
    out = []
    for rec in SP._lines(os.path.join(step0, "selfplay.jsonl")):
        st = records.start(rec)
        for i, a in enumerate(rec["actions"]):
            if st.over:
                break
            if st.phase == Phase.MAIN:
                n = len(legal_actions(st))
                if n >= 2:
                    out.append((rec["g"], i, n))
            apply(st, from_dict(a))
    return out


def t2sample(args):
    pts = _decisions(args.step0)
    pick = random.Random(T2_SAMPLE).sample(pts, T2_N)
    ns = sorted(p[2] for p in pick)
    q = [ns[int(f * len(ns)) - 1] if f * len(ns) == int(f * len(ns)) else ns[int(f * len(ns))] for f in (0.25, 0.5, 0.75)]
    bins = Counter(_bin(p[2], q) for p in pick)
    out = {"decisions": len(pts), "q": q, "bins": {str(b): bins[b] for b in range(4)},
           "pick": [{"d": d, "g": g, "at": at, "legal": n, "seed": T2_AGENT + d} for d, (g, at, n) in enumerate(pick)]}
    json.dump(out, open(args.out, "w"), indent=0)
    print(f"决策点 {len(pts)} 个，抽 {T2_N} 个；走法数分位数 q1/q2/q3 = {q}；各档个数 {[bins[b] for b in range(4)]}；"
          f"走法数最小 {ns[0]}、最大 {ns[-1]}、中位 {ns[len(ns) // 2]}")


def _bin(n, q):
    return 0 if n <= q[0] else 1 if n <= q[1] else 2 if n <= q[2] else 3


def _t2_job(p):
    from svsim.core.actions import to_dict
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    import student_data as SD
    rec = TL.REC[("selfplay", p["g"])]
    st = SD._state_at(rec, p["at"])
    legal = legal_actions(st)
    assert len(legal) == p["legal"]
    pick = {}
    for name, spec in (("strong", STRONG), ("deep", DEEP)):
        pick[name] = to_dict(make_agent(spec, p["seed"]).act(st.clone(), legal_actions(st)))
    return {**p, "strong": pick["strong"], "deep": pick["deep"], "same": pick["strong"] == pick["deep"],
            "record": rec["actions"][p["at"]] == pick["strong"]}


def t2run(args):
    from multiprocessing import Pool
    recs = TL._records(os.path.join(args.step0, "selfplay.jsonl"))
    pick = json.load(open(args.sample))["pick"]
    with Pool(args.workers, initializer=SP._init, initargs=(recs,)) as pool, open(args.out, "w") as fh:
        for n, row in enumerate(pool.imap_unordered(_t2_job, pick), 1):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            if n % 200 == 0:
                print(f"{n}/{len(pick)}", flush=True)
    print(f"写进了 {args.out}")


def _wilson(k, n):
    if n == 0:
        return float("nan"), float("nan")
    z, p = 1.96, k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def t2read(args):
    rows = SP._lines(args.rows)
    sample = json.load(open(args.sample))
    q = sample["q"]
    assert len(rows) == T2_N and len({r["d"] for r in rows}) == T2_N
    by = {b: [r for r in rows if _bin(r["legal"], q) == b] for b in range(4)}
    out = ["条件：对手卡表已知（牌序、手牌未知）。搜索档位的分歧和根节点走法数（README-gap.md 第 2 件）\n",
           f"- 决策点 {sample['decisions']} 个里抽 {len(rows)} 个；分界 q1/q2/q3 = {q}",
           f"- 总的不同比例：{sum(not r['same'] for r in rows) / len(rows):.1%}（{sum(not r['same'] for r in rows)} 个）\n",
           "| 档 | 走法数 | 决策点 | 不同 | 比例（Wilson 95%） |", "|---|---|---|---|---|"]
    rng_txt = [f"≤ {q[0]}", f"{q[0] + 1}～{q[1]}", f"{q[1] + 1}～{q[2]}", f"> {q[2]}"]
    rate = {}
    for b in range(4):
        n, k = len(by[b]), sum(not r["same"] for r in by[b])
        lo, hi = _wilson(k, n)
        rate[b] = k / n if n else float("nan")
        out.append(f"| {b + 1} | {rng_txt[b]} | {n} | {k} | {rate[b]:.1%}（{lo:.1%}～{hi:.1%}） |")
    rnd = random.Random(0)
    bs = []
    for _ in range(2000):
        s = [rows[rnd.randrange(len(rows))] for _ in rows]
        lo_b = [r for r in s if _bin(r["legal"], q) == 0]
        hi_b = [r for r in s if _bin(r["legal"], q) == 3]
        a = sum(not r["same"] for r in lo_b) / len(lo_b)
        bs.append(sum(not r["same"] for r in hi_b) / len(hi_b) / a if a else float("inf"))
    bs.sort()
    ratio = rate[3] / rate[0] if rate[0] else float("inf")
    out.append("")
    out.append(f"- 最高档 ÷ 最低档 = {ratio:.2f}（按决策点重抽 2000 次 {bs[49]:.2f}～{bs[1949]:.2f}）")
    out.append(f"- **J50**（最高档 ≥ 2 × 最低档，置信 70%）→ {'对' if ratio >= 2 else '错'}（看点估计）")
    if args.step0:
        # the record's own move (level-strong, another seed): compared in JSON form (to_dict gives tuples, the
        # record lists, so the row's "record" field is always false and is not used)
        acts = {r["g"]: r["actions"] for r in SP._lines(os.path.join(args.step0, "selfplay.jsonl"))}
        same_rec = [acts[r["g"]][r["at"]] == r["strong"] for r in rows]
        out.append(f"- 照报：level-strong 这次的选择和记录里当时的走法（同一个智能体、另一个种子）相同 "
                   f"{sum(same_rec) / len(same_rec):.1%}，即同档换种子的不同比例 {1 - sum(same_rec) / len(same_rec):.1%}；"
                   "分档：" + "、".join(f"第 {b + 1} 档 {1 - sum(x for x, r in zip(same_rec, rows) if _bin(r['legal'], q) == b) / len(by[b]):.1%}"
                                     for b in range(4)))
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


# ---- 1: how much of the gap the stronger budget closes ----

def _t1_turn(job):
    from svsim.core.engine import apply, legal_actions
    from svsim.search.lethal import state_key
    from svsim.tools.arena import make_agent
    st_row, spec, seed = job
    state, _ = TL._start_state(st_row)
    me, s, agent, n = state.active, state.clone(), make_agent(spec, seed), 0
    while not s.over and s.active == me and n < 300:
        apply(s, agent.act(s, legal_actions(s)))
        n += 1
    return st_row["k"], spec, seed, state_key(s), s


def _t1_play(job):
    from svsim.search.foresight import direction_rollout
    k, line, end, seed = job
    out = direction_rollout(end, direction="default", k=T1_K, seed=seed, opp_spec=SPEC, our_spec=SPEC)["default"]
    return {"k": k, "line": line, "seed": seed, "win": out["win"], "samples": out["samples"]}


def t1run(args):
    from multiprocessing import Pool
    from svsim.search.lethal import state_key
    recs = TL._records(os.path.join(args.step0, "selfplay.jsonl"))
    TL.REC.update(recs)
    starts, plans = SP._starts(args.step0)
    i_of = {st["k"]: i for i, st in enumerate(_m3_starts(args.step0))}
    rows = {st["k"]: st for st in starts}
    turn_jobs = [(rows[k], spec, T1_TURN + 100 * i_of[k] + r) for k in STARTS for spec in (STRONG, DEEP)
                 for r in range(T1_SEEDS)]
    with Pool(args.workers, initializer=SP._init, initargs=(recs,)) as pool:
        turns = pool.map(_t1_turn, turn_jobs)
        meta, play_jobs = [], []
        for k in STARTS:
            state, rec = TL._start_state(rows[k])
            status, salem_end = SP.turn_end(state, TL._salem_turn(rec, rows[k]["at"]))
            salem_key = state_key(salem_end)
            ends = {"salem": salem_end}
            for spec, line in ((STRONG, "strong"), (DEEP, "deep")):
                mine = [t for t in turns if t[0] == k and t[1] == spec]
                count = Counter(t[3] for t in mine)
                top = max(count.values())
                pick = min((t for t in mine if count[t[3]] == top), key=lambda t: t[2])
                ends[line] = pick[4]
                meta.append({"k": k, "line": line, "kinds": len(count), "mode_count": top, "mode_seed": pick[2],
                             "same_as_salem": pick[3] == salem_key,
                             "salem_count": sum(1 for t in mine if t[3] == salem_key)})
            seed = T1_PLAY + 500 * i_of[k]
            play_jobs += [(k, line, ends[line], seed) for line in ("salem", "strong", "deep")]
        played = pool.map(_t1_play, play_jobs)
    with open(args.out, "w") as fh:
        for m in meta:
            fh.write(json.dumps({"meta": True, **m}) + "\n")
        for p in played:
            fh.write(json.dumps(p) + "\n")
    print(f"写进了 {args.out}")


def _m3_starts(step0):
    """M4's start order (direction.py _m3_starts): the index i of each start."""
    import direction
    return direction._m3_starts(step0)[0]


def _pair(a, b, n_boot=2000):
    d = [x - y for x, y in zip(a, b)]
    rng = random.Random(0)
    bs = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(n_boot))
    return sum(d) / len(d), bs[int(0.025 * n_boot) - 1], bs[int(0.975 * n_boot) - 1]


def t1read(args):
    rows = SP._lines(args.rows)
    meta = {(r["k"], r["line"]): r for r in rows if r.get("meta")}
    play = {(r["k"], r["line"]): r for r in rows if not r.get("meta")}
    out = ["条件：对手卡表已知（牌序、手牌未知）。「最强」能补上多少运营差距（README-gap.md 第 1 件）\n",
           "| k | Salem | level-strong | 1043 | Salem − 1043（区间） | Salem − ls（区间） | 1043 − ls（区间） | 1043 补上 | ls / 1043 的回合末 |",
           "|---|---|---|---|---|---|---|---|---|"]
    caught, better, num, den = 0, 0, [], []
    for k in STARTS:
        s, l, d = (play[(k, x)]["samples"] for x in ("salem", "strong", "deep"))
        assert len(s) == len(l) == len(d) == T1_K and len({play[(k, x)]["seed"] for x in ("salem", "strong", "deep")}) == 1
        sd, sl, dl = _pair(s, d), _pair(s, l), _pair(d, l)
        caught += sd[1] <= 0
        better += sd[2] < 0
        ws, wl, wd = (sum(x) / len(x) for x in (s, l, d))
        num.append((d, l))
        den.append((s, l))
        share = f"{(wd - wl) / (ws - wl):.0%}" if ws - wl > 0 else "—"

        def m(line):
            r = meta[(k, line)]
            return f"{r['kinds']} 种，取 {r['mode_count']}/8" + ("，=Salem" if r["same_as_salem"] else "") + \
                   (f"，Salem 的出现 {r['salem_count']}" if r["salem_count"] and not r["same_as_salem"] else "")
        out.append(f"| {k} | {ws:.3f} | {wl:.3f} | {wd:.3f} | {sd[0]:+.3f}（{sd[1]:+.3f}～{sd[2]:+.3f}） | "
                   f"{sl[0]:+.3f}（{sl[1]:+.3f}～{sl[2]:+.3f}） | {dl[0]:+.3f}（{dl[1]:+.3f}～{dl[2]:+.3f}） | {share} | "
                   f"{m('strong')} / {m('deep')} |")
    rng = random.Random(0)

    def pooled(pairs_num, pairs_den, rnd=None):
        tn = td = 0.0
        for (a, b), (c, e) in zip(pairs_num, pairs_den):
            idx = range(len(a)) if rnd is None else [rnd.randrange(len(a)) for _ in a]
            tn += sum(a[j] - b[j] for j in idx) / len(a)
            td += sum(c[j] - e[j] for j in idx) / len(a)
        return tn / td if td else float("nan")
    est = pooled(num, den)
    bs = sorted(pooled(num, den, rng) for _ in range(2000))
    out.append("")
    out.append(f"- **1043 补上的差距（6 个合起来）**：{est:.0%}（每个开头内按种子重抽 2000 次 {bs[49]:.0%}～{bs[1949]:.0%}）")
    out.append(f"- 追平（Salem − 1043 的下沿 ≤ 0）：{caught} / 6；其中 1043 明显更好（上沿 < 0）{better} 个")
    out.append(f"- **J49**（至少 4 / 6 追平，置信 50%）→ {'对' if caught >= 4 else '错'}")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("t2sample")
    a.add_argument("step0")
    a.add_argument("--out", required=True)
    a = sub.add_parser("t2run")
    a.add_argument("step0")
    a.add_argument("--sample", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=3)
    a = sub.add_parser("t2read")
    a.add_argument("rows")
    a.add_argument("--sample", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--step0", default=None, help="stage-0 dir: also compare with the record's own move")
    a = sub.add_parser("t1run")
    a.add_argument("step0")
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=3)
    a = sub.add_parser("t1read")
    a.add_argument("rows")
    a.add_argument("--out", required=True)
    args = ap.parse_args()
    {"t2sample": t2sample, "t2run": t2run, "t2read": t2read, "t1run": t1run, "t1read": t1read}[args.cmd](args)


if __name__ == "__main__":
    main()
