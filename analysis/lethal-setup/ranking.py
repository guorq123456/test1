"""The ranking set (README-clock.md, "排序集"): on M4's 85 starts, Salem's and the bot's turn ends with their G_end
(M4 default, the re-test for the 6) and an evaluator's score of each; sign agreement of dV with dG where |dG| >= 0.10.
Turn ends and scores as the builder's analysis/puzzles3/ops.py (turn_end / judge_end).
Condition: the opponent's deck list is known (order and hand not).

    python ranking.py build <stage-0 dir> --out ranking/rows.jsonl                      # G_end and the installed score
    python ranking.py score <stage-0 dir> --rows ranking/rows.jsonl --spec SPEC --name cand   # add a column
    python ranking.py read ranking/rows.jsonl [--vs cand] --out ranking/read.txt
"""
import argparse
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "turn-level"))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))
import setup_prob as SP          # noqa: E402
import turn_level as TL          # noqa: E402

RETESTED = (320, 313, 445, 455, 329, 518)
MIN_DG = 0.10


def turn_end(state, actions):
    """ops.py turn_end: the turn's actions short of EndTurn, then the end-of-turn abilities (the opponent not
    started)."""
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.search.evaluate import after_end_of_turn
    s = state.clone()
    for a in actions:
        a = from_dict(a) if isinstance(a, dict) else a
        if isinstance(a, EndTurn) or s.over:
            break
        apply(s, a)
    return s if s.over else after_end_of_turn(s)


def judge(end, me, weights):
    """ops.py judge_end's win probability."""
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import evaluate
    if end.over:
        return 1.0 if end.winner == me else 0.0 if end.winner == 1 - me else 0.5
    z = evaluate(end, me, weights, False)
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z / SCALE))))


def _weights(spec):
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    return _search(make_agent(spec, 0)).weights


def _ends(step0):
    """{k: (start row, me, Salem's turn end, the bot's turn end)} for M4's 85 starts."""
    import direction
    TL.REC.update(TL._records(os.path.join(step0, "selfplay.jsonl")))
    starts, plans = direction._m3_starts(step0)
    out = {}
    for i, st in enumerate(starts):
        state, rec = TL._start_state(st)
        salem = TL._salem_turn(rec, st["at"])
        bot = next(p for p in plans[st["k"]]["plans"] if p["kind"] == "bot")["actions"]
        out[st["k"]] = (i, st, state.active, turn_end(state, salem), turn_end(state, bot))
    return out


def build(args):
    m4 = {(r["k"], r["line"]): r for r in SP._lines(os.path.join(HERE, "m4_rows.jsonl")) if r["direction"] == "default"}
    re = {(r["k"], r["line"]): r for r in SP._lines(os.path.join(HERE, "puzzles", "retest_rows.jsonl"))}
    m3 = {r["k"]: r["class"] for r in SP._lines(os.path.join(HERE, "m3_rows.jsonl"))}
    ends = _ends(args.step0)
    W = _weights(args.installed)
    with open(args.out, "w") as fh:
        for k, (i, st, me, se, be) in sorted(ends.items(), key=lambda kv: kv[1][0]):
            src = re if k in RETESTED else m4
            row = {"k": k, "i": i, "own_turn": st["own_turn"], "class": m3[k],
                   "g_salem": src[(k, "salem")]["win"], "g_bot": src[(k, "bot")]["win"],
                   "g_src": "retest K=48" if k in RETESTED else "M4 K=12",
                   "v": {"installed": [judge(se, me, W), judge(be, me, W)]}}
            fh.write(json.dumps(row) + "\n")
    print(f"写进了 {args.out}（{len(ends)} 个开头）")


def score(args):
    rows = SP._lines(args.rows)
    ends = _ends(args.step0)
    W = _weights(args.spec)
    for r in rows:
        i, st, me, se, be = ends[r["k"]]
        r["v"][args.name] = [judge(se, me, W), judge(be, me, W)]
        r.setdefault("specs", {})[args.name] = args.spec
    with open(args.rows, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"{args.name} 的打分加进了 {args.rows}")


def _agree(r, name):
    dg = r["g_salem"] - r["g_bot"]
    dv = r["v"][name][0] - r["v"][name][1]
    return 0.5 if abs(dv) < 1e-12 else float((dv > 0) == (dg > 0))


def read(args):
    rows = SP._lines(args.rows)
    sel = [r for r in rows if abs(r["g_salem"] - r["g_bot"]) >= MIN_DG - 1e-12]
    rng = random.Random(0)
    picks = [[sel[rng.randrange(len(sel))] for _ in sel] for _ in range(2000)]

    def share(name, subset=None):
        s = sel if subset is None else subset
        return sum(_agree(r, name) for r in s) / len(s) if s else float("nan")

    def interval(f):
        bs = sorted(f(p) for p in picks)
        return bs[49], bs[1949]
    out = ["条件：对手卡表已知（牌序、手牌未知）。排序集：Salem 回合末对 bot 回合末，评估器和 G_end 同号的比例（README-clock.md）\n",
           f"- 开头 {len(rows)} 个；|ΔG| ≥ {MIN_DG} 的 {len(sel)} 个（Salem 更好 {sum(r['g_salem'] > r['g_bot'] for r in sel)} 个，"
           f"bot 更好 {sum(r['g_salem'] < r['g_bot'] for r in sel)} 个）"]
    names = ["installed"] + ([args.vs] if args.vs else [])
    for name in names:
        lo, hi = interval(lambda p: sum(_agree(r, name) for r in p) / len(p))
        out.append(f"- **{name}** 同号率 **{share(name):.1%}**（按开头重抽 2000 次 {lo:.1%}～{hi:.1%}）")
    if args.vs:
        d = share(args.vs) - share("installed")
        lo, hi = interval(lambda p: (sum(_agree(r, args.vs) for r in p) - sum(_agree(r, "installed") for r in p)) / len(p))
        out.append(f"- **{args.vs} − installed**：{100 * d:+.1f} 个百分点（{100 * lo:+.1f}～{100 * hi:+.1f}）；"
                   f"**J56**（≥ +5，置信 40%）→ {'对' if 100 * d >= 5 - 1e-9 else '错'}")
    out.append("\n| M3 类 | 开头（\\|ΔG\\| ≥ 0.10） | Salem 更好 | " + " | ".join(f"{n} 同号率" for n in names) + " |")
    out.append("|---|---|---|" + "---|" * len(names))
    for cls in sorted({r["class"] for r in sel}, key=lambda c: -sum(r["class"] == c for r in sel)):
        sub = [r for r in sel if r["class"] == cls]
        out.append(f"| {cls} | {len(sub)} | {sum(r['g_salem'] > r['g_bot'] for r in sub)} | " +
                   " | ".join(f"{share(n, sub):.0%}" for n in names) + " |")
    better = [r for r in sel if r["g_salem"] > r["g_bot"]]
    worse = [r for r in sel if r["g_salem"] < r["g_bot"]]
    out.append("")
    out.append("- 按 G_end 哪边更好分开：" + "；".join(
        f"{lab} {len(sub)} 个，" + "、".join(f"{n} {share(n, sub):.0%}" for n in names) for lab, sub in
        (("Salem 更好", better), ("bot 更好", worse))))
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("build")
    a.add_argument("step0")
    a.add_argument("--out", required=True)
    a.add_argument("--installed", default="level-strong")
    a = sub.add_parser("score")
    a.add_argument("step0")
    a.add_argument("--rows", required=True)
    a.add_argument("--spec", required=True)
    a.add_argument("--name", required=True)
    a = sub.add_parser("read")
    a.add_argument("rows")
    a.add_argument("--vs", default=None)
    a.add_argument("--out", required=True)
    args = ap.parse_args()
    {"build": build, "score": score, "read": read}[args.cmd](args)


if __name__ == "__main__":
    main()
