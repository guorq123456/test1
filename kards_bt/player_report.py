"""Event-by-event check of one player: did results match the model's expectation, and how did the rating move?

For every event the player entered:
* pre-event ratings of everyone come from a fit on results before the event's first match
  (same model as bt.py: decay, prior, ladder-invite credit), so each match gets an honest win probability;
* expected wins = sum of those probabilities, compared with actual wins;
* the rating change (after the event vs before) is split into the part caused by the player's own results
  in that event and the rest (decay of old results, opponents' results changing what old wins are worth).

    python3 player_report.py guorq123456 [--out report.md]
"""
import argparse
import csv
import os
import re
from collections import defaultdict
from datetime import timedelta

import bt
import invites

ELO = bt.ELO_SCALE


def ratings(matches, names, credits, t, args):
    """{player: elo} from results up to and including time t."""
    bt._JOB = (matches, names, args.half_life, args.prior_sd, 10 ** 6, credits, args.invite_half_life)
    return {r["player_id"]: r["elo"] for r in bt._snapshot_chunk([(t, "")])}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("player", help="display name or player_id")
    ap.add_argument("--half-life", type=float, default=240)
    ap.add_argument("--prior-sd", type=float, default=0.8)
    ap.add_argument("--invite-half-life", type=float, default=120)
    ap.add_argument("--out", help="write a Markdown report here")
    args = ap.parse_args()

    players = list(csv.DictReader(open(os.path.join(bt.DATA, "players.csv"))))
    names = {p["player_id"]: p["name"] for p in players}
    q = args.player.lower()
    pid = next(p["player_id"] for p in players
               if q in (p["player_id"].lower(), p["name"].lower()) or q in p["aliases"].lower().split(" / "))

    cats = {"open", "open_special", "official"}
    matches = bt.load_matches(cats, False)
    fit_before = lambda t: bt._fit_before(matches, t, args.half_life, args.prior_sd)  # noqa: E731
    credits = invites.credits(fit_before)

    rows = [r for r in csv.DictReader(open(os.path.join(bt.DATA, "matches.csv")))
            if r["valid"] == "1" and r["category"] in cats]
    span = defaultdict(lambda: [None, None])
    for r in rows:
        t = bt.parse_time(r["time"])
        s = span[r["event"]]
        s[0] = t if s[0] is None else min(s[0], t)
        s[1] = t if s[1] is None else max(s[1], t)
    mine = defaultdict(list)
    for r in rows:
        if pid in (r["p1"], r["p2"]):
            mine[r["event"]].append(r)
    place = {r["event"]: r["label"] for r in csv.DictReader(open(os.path.join(bt.DATA, "placements.csv")))
             if r["player_id"] == pid}

    out = [f"# {names[pid]}：逐站检验\n",
           "赛前分 = 用这站第一场之前的所有结果拟合；期望胜场 = 每场赛前胜率之和。"
           "变化拆成两部分：**本站战绩**（同一时刻、去掉本人这站对局再拟合一次，两者之差）"
           "（含天梯直邀的虚拟战绩）和**其他**（旧比赛衰减、对手后来的成绩改变旧胜负的含金量）。新人对手没有赛前分，按 1500 计。\n",
           "| 赛事 | 结果 | 胜-负 | 期望胜 | 差 | 赛前 | 赛后 | 变化 | 本站战绩 | 其他 |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    detail = []
    tot_w = tot_e = 0.0
    for event in sorted(mine, key=lambda e: span[e][0]):
        start, end = span[event]
        pre = ratings(matches, names, credits, start - timedelta(seconds=1), args)
        post = ratings(matches, names, credits, end, args)
        without = [m for m in matches if not (m[4] == event and pid in (m[1], m[2]))]
        # the ladder-invite credit (if any) belongs to this event's result too
        cr_wo = [c for c in credits if not (c[1] == pid and start <= c[0] <= end)]
        post_wo = ratings(without, names, cr_wo, end, args)
        me0 = pre.get(pid, 1500.0)
        w = l = 0
        exp = 0.0
        lines = []
        for r in sorted(mine[event], key=lambda r: r["time"]):
            opp = r["p2"] if r["p1"] == pid else r["p1"]
            won = (r["winner"] == "1") == (r["p1"] == pid)
            opp_elo = pre.get(opp, 1500.0)
            p = 1 / (1 + 10 ** ((opp_elo - me0) / 400))
            exp += p
            w, l = w + won, l + (not won)
            s1, s2 = (r["s1"], r["s2"]) if r["p1"] == pid else (r["s2"], r["s1"])
            score = f"{s1}-{s2}" if s1 not in ("", None) else ""
            lines.append(f"| {r['stage'] or ''} {r['round'] or ''} | {names.get(opp, opp)} | {opp_elo:.0f}"
                         f"{'' if opp in pre else '（新人）'} | {p:.0%} | {'胜' if won else '负'} {score} |")
        tot_w += w
        tot_e += exp
        after = post[pid]
        own = after - post_wo.get(pid, me0)
        label = place.get(event, "")
        out.append(f"| {event} | {label} | {w}-{l} | {exp:.1f} | {w - exp:+.1f} | {me0:.0f} | {after:.0f} | "
                   f"{after - me0:+.0f} | {own:+.0f} | {after - me0 - own:+.0f} |")
        detail += [f"\n### {event}（{start:%Y-%m-%d}）{label}\n", f"赛前 {me0:.0f} → 赛后 {after:.0f}\n",
                   "| 轮次 | 对手 | 对手赛前分 | 赛前胜率 | 结果 |", "|---|---|---|---|---|"] + lines
    n = sum(len(v) for v in mine.values())
    out.append(f"\n合计 {n} 场：实际 {tot_w:.0f} 胜，模型期望 {tot_e:.1f} 胜（{tot_w - tot_e:+.1f}）。\n")
    out.append("## 每场对局\n")
    text = re.sub(r"\bKards (Open|World)", r"KARDS \1", "\n".join(out + detail) + "\n")
    if args.out:
        open(args.out, "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
