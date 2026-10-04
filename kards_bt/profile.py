"""One-screen profile of a player from the generated data files (no refitting).

Pulls together: current rating and rank, peak, peak-board rank, actual vs expected wins (residuals.py),
record by year / stage / opponent strength, score distribution, placements, frequent opponents, rating
trajectory and ladder invites. Run player_report.py for the per-event, per-match breakdown.

    python3 profile.py 禁忌之门
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

import invites
from placements import stage_name

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MAIN = {"8 强", "16 强", "总决赛", "邀请赛", "32 强", "淘汰赛"}


def load(name):
    return list(csv.DictReader(open(os.path.join(DATA, name))))


def main():
    q = " ".join(sys.argv[1:]).lower()
    players = load("players.csv")
    P = next((p for p in players if q in (p["name"].lower(), p["player_id"].lower()) or q in p["aliases"].lower().split(" / ")), None) \
        or next((p for p in players if q in p["name"].lower()), None)
    if not P:
        sys.exit(f"no player matches {q!r}")
    pid = P["player_id"]
    names = {p["player_id"]: p["name"] for p in players}
    rows = load("ratings_timeline.csv")
    ms = [m for m in load("matches.csv") if m["valid"] == "1" and m["category"] == "official"]
    peaks = load("peaks.csv")
    resid = {r["player_id"]: r for r in load("residuals.csv")}
    ev_start = {}
    for m in ms:
        ev_start[m["event"]] = min(ev_start.get(m["event"], m["time"]), m["time"])
    # placements.csv also covers Open-series events, which the ratings do not use
    pl = sorted(((r["event"], r["label"]) for r in load("placements.csv") if r["player_id"] == pid and r["event"] in ev_start),
                key=lambda x: ev_start[x[0]])
    peak_elo = {r["player_id"]: float(r["peak_elo"]) for r in peaks}
    debut = {}
    for m in sorted(ms, key=lambda m: m["time"]):
        for p in (m["p1"], m["p2"]):
            debut.setdefault(p, m["event"])

    def board(date):
        b = sorted((r for r in rows if r["date"] == date and int(r["results"]) >= 10), key=lambda r: -(float(r["elo"]) - float(r["se"])))
        return {r["player_id"]: i + 1 for i, r in enumerate(b)}

    ts = [r for r in rows if r["player_id"] == pid]
    if not ts:
        sys.exit(f"{P['name']} has no official-event ratings")
    last = ts[-1]
    cur = board(max(r["date"] for r in rows if r["event"]))
    pk = max(ts, key=lambda r: float(r["elo"]))
    ranked = [(board(d)[pid], d) for d in sorted({r["date"] for r in ts if r["event"]}) if pid in board(d)]
    best = min(ranked) if ranked else ("–", "未上榜")
    pkr = next(((i + 1, r) for i, r in enumerate(peaks) if r["player_id"] == pid), None)
    rs = resid.get(pid)

    print(f"{P['name']}  曾用名/账号: {P['aliases']} | {P['accounts']}")
    print(f"现在: BT {float(last['elo']):.0f} ±{float(last['se']):.0f}，当前榜 #{cur.get(pid, '–')}，{last['results']} 场，最近出赛 {last['last_played']}")
    print(f"峰值: BT {float(pk['elo']):.0f}（{pk['date']}），最高名次 #{best[0]}（{best[1]}）"
          + (f"；巅峰榜 #{pkr[0]}，{pkr[1]['peak_score']}（{pkr[1]['peak_date']}，当时 #{pkr[1]['rank_then']}）" if pkr else "；巅峰榜未入（不足 10 场）"))
    if rs:
        print(f"vs 预期: 生涯 {rs['wins']}/{rs['matches']} 胜，期望 {rs['expected']}，差 {float(rs['diff']):+}（z {float(rs['z']):+}）；"
              f"近 24 个月 {rs['recent_wins']}-{int(rs['recent_n']) - int(rs['recent_wins'])}，期望 {rs['recent_expected']}，差 {float(rs['recent_diff']):+}（z {float(rs['recent_z']):+}）")

    yr, st, strong, newo, opp, scores = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), [0, 0], [0, 0], defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for m in ms:
        if pid not in (m["p1"], m["p2"]):
            continue
        o = m["p2"] if m["p1"] == pid else m["p1"]
        won = (m["winner"] == "1") == (m["p1"] == pid)
        i = 0 if won else 1
        yr[m["time"][:4]][i] += 1
        st["正赛" if stage_name(m["event"], m["stage"], m["stage_type"]) in MAIN else "预选/小组/瑞士"][i] += 1
        opp[o][i] += 1
        if peak_elo.get(o, 1500) >= 1540:
            strong[i] += 1
        if debut.get(o) == m["event"]:
            newo[i] += 1
        sc = f"{m['s1']}-{m['s2']}" if m["p1"] == pid else f"{m['s2']}-{m['s1']}"
        scores[sc][i] += 1
    f = lambda v: f"{v[0]}-{v[1]}（{v[0] / max(1, sum(v)):.0%}）"  # noqa: E731
    print("按年: " + "  ".join(f"{y} {f(v)}" for y, v in sorted(yr.items())))
    print("按阶段: " + "  ".join(f"{k} {f(v)}" for k, v in st.items()) + f"   对强手(巅峰≥1540) {f(strong)}   对首次参赛新人 {f(newo)}")
    print("比分分布: " + "  ".join(f"{k}×{sum(v)}" for k, v in sorted(scores.items(), key=lambda x: -sum(x[1]))))
    n_main = sum(1 for e, l in pl if re.search(r"8 强|16 强|总决赛|邀请赛|淘汰赛", l))
    tops = [(e, l) for e, l in pl if re.search(r"第 [1-3] 名", l) and re.search(r"8 强|16 强|总决赛|邀请赛", l)]
    print(f"参加 {len(pl)} 站，正赛 {n_main} 次，正赛前三 {len(tops)} 次: " + "; ".join(f"{e} {l}" for e, l in tops))
    print("全部名次: " + "; ".join(f"{e} {l}" for e, l in pl))
    print("常见对手: " + ", ".join(f"{names.get(o, o)} {v[0]}-{v[1]}" for o, v in sorted(opp.items(), key=lambda x: -sum(x[1]))[:8]))
    print("走势(季度): " + " ".join(f"{r['date'][:7]}:{float(r['elo']):.0f}" for r in ts if r["date"][5:] in ("01-01", "04-01", "07-01", "10-01")))
    print(f"天梯直邀: {sum(1 for mth in invites.months() if pid in mth[3])} 次")


if __name__ == "__main__":
    main()
