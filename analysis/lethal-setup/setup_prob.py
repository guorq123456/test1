"""M2, setting up (README.md here): P_NL, the chance of a lethal on our next turn, at the turn end of Salem's line and
of level-strong's line from the same 235 starts in Salem's games (turn-level step 0's starts k = 300-534, RC 84d735e).
Condition: the opponent's deck list is known (order and hand not).

    check  the two lines rebuilt on the real start (no P_NL): replay failures, lines that win during the turn, starts
           where the two turn ends are the same (search.lethal.state_key)
    run    P_NL of each line's turn end by the builder's next_lethal_prob (k = 16, seed 66500000 + 100 i for the i-th
           start, the same seed for both lines); one row per start
    read   the report fixed beforehand (README "报什么")

Salem's line is his recorded turn (turn_level._salem_turn); level-strong's is step 0's "bot" plan (its actions as
played on the real start). A line that wins during its own turn scores P_NL = 1.
"""
import argparse
import importlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))
sys.path.insert(0, os.path.join(HERE, "..", "turn-level"))

import student_data as SD        # noqa: E402
import turn_level as TL          # noqa: E402

BANK = 66500000
K = 16
EARLY, MID = range(1, 4), range(4, 8)          # own turns 1-3, 4-7 (the midgame); 8 and later


def _lines(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def turn_end(state, actions):
    """Apply a turn's actions (Action objects or to_dict dicts) on a copy; ("ended" | "won" | "lost" | "fail at i",
    the state after the turn's EndTurn, or the finished game)."""
    from svsim.core.actions import EndTurn, from_dict, to_dict
    from svsim.core.engine import apply, legal_actions
    s = state.clone()
    me = s.active
    for i, a in enumerate(actions):
        a = from_dict(a) if isinstance(a, dict) else a
        want = to_dict(a)
        if not any(to_dict(x) == want for x in legal_actions(s)):
            return f"fail at {i}", s
        apply(s, a)
        if s.over:
            return ("won" if s.winner == me else "lost"), s
        if isinstance(a, EndTurn):
            return "ended", s
    return "fail at end", s                    # the actions ran out before the turn ended


def _starts(step0):
    starts = [r for r in _lines(os.path.join(step0, "starts.jsonl")) if r["src"] == "salem"]
    plans = {r["k"]: r for r in _lines(os.path.join(step0, "plans.jsonl"))}
    return sorted(starts, key=lambda r: r["k"]), plans


def _both(st_row, plans):
    from svsim.search.lethal import state_key
    state, rec = TL._start_state(st_row)
    salem = TL._salem_turn(rec, st_row["at"])
    bot = next(p for p in plans[st_row["k"]]["plans"] if p["kind"] == "bot")
    (fs, ss), (fb, sb) = turn_end(state, salem), turn_end(state, bot["actions"])
    same = fs == fb == "ended" and state_key(ss) == state_key(sb)
    return state, (fs, ss), (fb, sb), same


def _init(recs):
    TL.REC.update(recs)


def check(args):
    from collections import Counter
    TL.REC.update(TL._records(os.path.join(args.step0, "selfplay.jsonl")))
    starts, plans = _starts(args.step0)
    status = Counter()
    same = 0
    for st in starts:
        _, (fs, _), (fb, _), sm = _both(st, plans)
        status[("salem", fs.split(" ")[0])] += 1
        status[("bot", fb.split(" ")[0])] += 1
        same += sm
    print("条件：对手卡表已知（牌序、手牌未知）。M2 的两条线在真实开头上重放（不算 P_NL）\n")
    print(f"- 开头 {len(starts)} 个；两条线回合末相同（state_key）{same} 个")
    for who in ("salem", "bot"):
        print(f"- {who}：" + "、".join(f"{k} {v}" for (w, k), v in sorted(status.items()) if w == who))


def _job(job):
    i, st_row, plans_k, fn_path, bank = job
    mod, name = fn_path.split(":")
    nlp = getattr(importlib.import_module(mod), name)
    _, (fs, ss), (fb, sb), same = _both(st_row, {st_row["k"]: plans_k})
    seed = bank + 100 * i

    def p_nl(status, s):
        """(P_NL, the tool's detail): a line that won during its own turn 1 with no detail; the tool's "p" else."""
        if status == "won":
            return 1.0, None
        if status != "ended":
            return None, None
        out = nlp(s, K, seed, reply_spec="level-strong")
        return out["p"], out
    ps, ds = p_nl(fs, ss)
    pb, db = (ps, ds) if same else p_nl(fb, sb)
    return {"i": i, "k": st_row["k"], "own_turn": st_row["own_turn"], "seed": seed, "same": same,
            "salem_status": fs, "bot_status": fb, "salem": ps, "bot": pb, "salem_detail": ds, "bot_detail": db}


def run(args):
    from multiprocessing import Pool
    recs = TL._records(os.path.join(args.step0, "selfplay.jsonl"))
    starts, plans = _starts(args.step0)
    jobs = [(i, st, plans[st["k"]], args.fn, args.bank) for i, st in enumerate(starts)
            if not args.ks or st["k"] in args.ks][:args.limit or None]
    mode = "w"
    if args.resume and os.path.exists(args.out):
        # each row depends only on its start and seed: rows already written are kept, the rest computed and appended
        done = {r["k"] for r in _lines(args.out)}
        jobs = [j for j in jobs if j[1]["k"] not in done]
        mode = "a"
        print(f"接着跑：已有 {len(done)} 个开头，还剩 {len(jobs)} 个", flush=True)
    with Pool(args.workers, initializer=_init, initargs=(recs,)) as pool, open(args.out, mode, encoding="utf-8") as fh:
        for n, row in enumerate(pool.imap_unordered(_job, jobs), 1):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            if n % 20 == 0:
                print(f"{n}/{len(jobs)}", flush=True)
    print(f"{len(jobs)} 个开头写进了 {args.out}")


def read(args):
    import numpy as np
    rows = [r for r in _lines(args.rows) if r["salem"] is not None and r["bot"] is not None]
    rng = np.random.default_rng(0)

    def excl(p, d):
        """P_NL with the incomplete find_lethal samples left out (they are always 0): sum / (k - incomplete)."""
        if d is None:
            return p
        n = len(d["samples"]) - d["incomplete"]
        return sum(d["samples"]) / n if n > 0 else None
    for r in rows:
        r["salem_x"], r["bot_x"] = excl(r["salem"], r["salem_detail"]), excl(r["bot"], r["bot_detail"])

    def boot(sel, a="salem", b="bot"):
        d = np.array([r[a] - r[b] for r in sel])
        if not len(d):
            return float("nan"), float("nan"), float("nan")
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)

    def line(label, sel):
        if not sel:
            return f"- {label}：0 个开头"
        m, lo, hi = boot(sel)
        s, b = np.mean([r["salem"] for r in sel]), np.mean([r["bot"] for r in sel])
        anyp = np.mean([max(r["salem"], r["bot"]) > 0 for r in sel])
        sw = np.mean([r["salem"] > r["bot"] for r in sel])
        bw = np.mean([r["bot"] > r["salem"] for r in sel])
        return (f"- {label}：{len(sel)} 个开头；P_NL Salem {s:.3f}、bot {b:.3f}；差 {m:+.3f}（{lo:+.3f}～{hi:+.3f}）；"
                f"任一条 > 0 {anyp:.1%}；Salem > bot {sw:.1%}，bot > Salem {bw:.1%}")
    print("条件：对手卡表已知（牌序、手牌未知）。M2：铺垫，P_NL(Salem) − P_NL(bot)\n")
    dropped = len(_lines(args.rows)) - len(rows)
    print(f"- 复现失败、不算的开头 {dropped} 个；bot 的线当回合就赢的 {sum(r['bot_status'] == 'won' for r in rows)} 个，"
          f"Salem 的 {sum(r['salem_status'] == 'won' for r in rows)} 个")
    dets = [d for r in rows for d in {id(r["salem_detail"]): r["salem_detail"], id(r["bot_detail"]): r["bot_detail"]}.values() if d]
    searched = sum(e in ("lethal", "no lethal") for d in dets for e in d["ends"])
    inc = sum(d["incomplete"] for d in dets)
    print(f"- find_lethal 没跑完（没找到 sure 且撞到节点上限）：{inc} / {searched}（{inc / max(searched, 1):.1%}）")
    print(f"- 两条线 P_NL 都 ≥ 0.9 的开头：{np.mean([min(r['salem'], r['bot']) >= 0.9 for r in rows]):.1%}")
    print(line("**全部（主读数）**", rows))
    xs = [r for r in rows if r["salem_x"] is not None and r["bot_x"] is not None]
    m, lo, hi = boot(xs, "salem_x", "bot_x")
    print(f"- 去掉没跑完的样本：{len(xs)} 个开头；P_NL Salem {np.mean([r['salem_x'] for r in xs]):.3f}、"
          f"bot {np.mean([r['bot_x'] for r in xs]):.3f}；差 {m:+.3f}（{lo:+.3f}～{hi:+.3f}）")
    print(line("两条线不同的", [r for r in rows if not r["same"]]))
    print(line("去掉当回合就赢的", [r for r in rows if "won" not in (r["salem_status"], r["bot_status"])]))
    print(line("前期（自己第 1～3 回合）", [r for r in rows if r["own_turn"] in EARLY]))
    print(line("**中盘（第 4～7 回合）**", [r for r in rows if r["own_turn"] in MID]))
    print(line("后期（第 8 回合及以后）", [r for r in rows if r["own_turn"] >= 8]))
    print("\n逐回合：")
    for t in sorted({r["own_turn"] for r in rows}):
        print("  " + line(f"第 {t} 回合", [r for r in rows if r["own_turn"] == t]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("check")
    a.add_argument("step0", help="turn-level step 0's data folder (RC 84d735e: selfplay, starts, plans)")
    a = sub.add_parser("run")
    a.add_argument("step0")
    a.add_argument("--fn", default="svsim.search.foresight:next_lethal_prob", help="module:function of the builder's tool")
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=12)
    a.add_argument("--limit", type=int, default=0, help="only the first N starts (smoke tests)")
    a.add_argument("--ks", type=int, nargs="*", default=None, help="only these step-0 k (smoke tests)")
    a.add_argument("--bank", type=int, default=BANK, help="the seed bank (another only for smoke tests)")
    a.add_argument("--resume", action="store_true", help="keep the rows already in --out, compute the rest")
    a = sub.add_parser("read")
    a.add_argument("rows")
    args = ap.parse_args()
    {"check": check, "run": run, "read": read}[args.cmd](args)


if __name__ == "__main__":
    main()
