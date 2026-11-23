"""The players' environment report, one per period (player prompt: 「公共环境报告，每期一份：排行榜（每个成员的匿名编号、职业、
相对 CR、名次区间）、成员之间的胜率表、基线成员的卡表、存档卡组清单、锚点对战的结果、公共题的结果（不标是谁写的）」).

    python -m ladder.report POOL --out PUBDIR [--anchors-dir DIR [--anchors-period N]] [--puzzle RESULT-PUBLIC.json ...]
                            [--note "what changed in the rules this period"] [--games-period N]

Writes PUBDIR/report-P<period>.md and PUBDIR/report-P<period>.json. Only anonymous ids, classes and numbers: no
owner, no version, no entry period, no list of a player's member (red line). Baseline members are marked (they
belong to nobody). Two readings forced by the red line (DEVIATIONS A42, A43):
- "存档卡组清单" is public/decklists.md (the reference lists), not the lists of members that left the pool: those are
  a player's lists.
- The win tables count one period's games only (by default the last period that has games): cumulative counts
  would tell how long a member has been in the pool (its entry period).
- The anchor results (S11, A48): the last anchor run (one per period, every member against every anchor on fresh
  seeds, its own frozen copy included), per member class and tier and for the whole pool, whole percent with a 95%
  interval, without counts or ids. Fresh seeds every period: an unchanged member's figures move too, so a change in a
  class's figure doesn't say that someone in it changed (the fixed seeds of A40 did, hence the single pooled figure
  of A43 before S11).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for _p in (str(HERE.parent), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def game_periods(pool) -> dict:
    """game id -> the period it was started in (from the start events)."""
    out = {}
    for line in pool.events_path.read_text(encoding="utf-8").splitlines():
        ev = json.loads(line)
        if ev.get("ev") == "start":
            out[ev["id"]] = ev["period"]
    return out


def win_table(pool, period: int | None = None) -> tuple[dict, dict, int | None]:
    """(member x member, member x opponent class, the period counted): [won, decided] over the decided games of one
    period (default: the last period that has decided games), by anon id."""
    from ladder.pool import CRAFT_ZH
    anon = {m.mid: m.anon for m in pool.members.values()}
    craft = {m.mid: m.craft for m in pool.members.values()}
    started = game_periods(pool)
    games = []
    for line in pool.events_path.read_text(encoding="utf-8").splitlines():
        ev = json.loads(line)
        if ev.get("ev") == "game" and ev.get("decided"):
            games.append(ev)
    if period is None:
        period = max((started[g["id"]] for g in games), default=None)
    pair, by_class = {}, {}
    for ev in games:
        if started[ev["id"]] != period:
            continue
        a, b = ev["members"]
        w = ev["winner"]
        for me, opp, won in ((a, b, w == 0), (b, a, w == 1)):
            d = pair.setdefault(anon[me], {}).setdefault(anon[opp], [0, 0])
            d[0] += won
            d[1] += 1
            c = by_class.setdefault(anon[me], {}).setdefault(CRAFT_ZH[craft[opp]], [0, 0])
            c[0] += won
            c[1] += 1
    return pair, by_class, period


def build(pool_dir, anchors_dir=None, puzzles=(), note="", games_period=None, anchors_period=None) -> dict:
    from ladder import leaderboard as L
    from ladder.pool import CRAFT_ZH, period_kind
    pool, series = L.load(pool_dir)
    board = L.public_board(pool, series)
    active = {m.anon for m in pool.active()}
    pair, by_class, counted = win_table(pool, games_period)
    anchors, a_period = [], None
    if anchors_dir:
        from ladder.anchors import classes
        a_period, anchors = classes(Path(anchors_dir), anchors_period)
    per_class = {}
    for m in pool.active():
        per_class[CRAFT_ZH[m.craft]] = per_class.get(CRAFT_ZH[m.craft], 0) + 1
    return {"period": pool.period, "kind": period_kind(pool.period), "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "members": len(pool.active()), "per_class": per_class, "note": note, "board": board,
            "games_period": counted, "anchors_period": a_period,
            "wins_vs_class": {a: v for a, v in by_class.items() if a in active},
            "wins_vs_member": {a: v for a, v in pair.items() if a in active},
            "anchors": anchors, "puzzles": [json.loads(Path(p).read_text(encoding="utf-8")) for p in puzzles]}


def _pct(w, n):
    return f"{100 * w / n:.0f}%（{w}/{n}）" if n else "—"


def markdown(r: dict) -> str:
    from ladder.pool import CRAFT_ZH
    kind = {"deck": "卡组期", "strategy": "策略期", "baseline": "基线"}[r["kind"]]
    out = [f"# 环境报告 第 {r['period']} 期（{kind}）", "",
           f"写于 {r['time']}（主持方）。池子里 {r['members']} 个成员：" +
           "、".join(f"{k} {v}" for k, v in r["per_class"].items()) + "。只有匿名编号，看不出是谁的、第几期进来的、第几版。", ""]
    if r["note"]:
        out += ["## 这一期的变化", "", r["note"], ""]
    out += ["## 排行榜", "", "满 100 局的成员。相对 CR = 最近 2000 局（不足就用全部）的平均减池子平均；区间 95%。名次在职业内，写成"
            "「最好～最差」：最好 = 1 + 区间整个在它上面的成员数，最差 = 职业里的成员数 − 区间整个在它下面的成员数。"
            "「基线」是池子开始时的七个基线成员。", ""]
    for craft in CRAFT_ZH.values():
        rows = [b for b in r["board"] if b["craft"] == craft]
        if not rows:
            continue
        out += [f"### {craft}", "", "| 编号 | 相对 CR | 区间 | 名次 | |", "|---|---|---|---|---|"]
        for b in rows:
            out.append(f"| {b['anon']} | {b['rel_cr']:+.0f} | {b['lo']:+.0f}～{b['hi']:+.0f} | {b['best']}～{b['worst']} | "
                       f"{'基线' if b['baseline'] else ''} |")
        out.append("")
    gp = r["games_period"]
    span = "还没有分出胜负的对局" if gp is None else f"第 {gp} 期分出胜负的对局"
    out += ["## 胜率表（对每个职业）", "", f"{span}（只算一期：累计的局数会看出成员在池子里待了多久）。逐个成员对逐个成员的表"
            "在同名 .json 里（wins_vs_member）。", "",
            "| 编号 | " + " | ".join(CRAFT_ZH.values()) + " |", "|---|" + "---|" * 7]
    for a, v in sorted(r["wins_vs_class"].items()):
        out.append(f"| {a} | " + " | ".join(_pct(*v.get(c, [0, 0])) for c in CRAFT_ZH.values()) + " |")
    out.append("")
    if r["anchors"]:
        tiers = [t for t in ("基线快照", "名人堂") if any(x["tier"] == t for x in r["anchors"])]
        cell = {(x["craft"], x["tier"]): f"{x['rate']}%（{x['lo']}～{x['hi']}%）" for x in r["anchors"]}
        out += ["## 锚点对战", "", f"第 {r['anchors_period']} 期结束时，池子里每个成员（当时那一版）对每个锚点各打同样多的局，"
                "种子每期新抽。锚点：基线快照（七副基线卡组 + 默认打法）和名人堂（每期各职业第一名冻结）。按成员的职业合起来，"
                "取整到百分之一，括号里是 95% 区间；不标编号、不给局数。种子每期都换，没改打法的成员数字也会动。", "",
                "| 职业 | " + " | ".join(f"对{t}" for t in tiers) + " |", "|---|" + "---|" * len(tiers)]
        for c in list(CRAFT_ZH.values()) + ["全池"]:
            if any((c, t) in cell for t in tiers):
                out.append(f"| {c} | " + " | ".join(cell.get((c, t), "—") for t in tiers) + " |")
        out.append("")
    for p in r["puzzles"]:
        out += [f"## 公共题 {p['puzzle']}　{p['title']}", "", "不标是谁写的；「选手 N」的编号每道题重新打乱。", "",
                "| 打法 | 胜率 | 区间 | 比默认打法（百分点） |", "|---|---|---|---|"]
        for e in p["entries"]:
            d = e.get("vs_default_pp")
            out.append(f"| {e['entry']} | {100 * e['rate']:.0f}% | {100 * e['lo']:.0f}%～{100 * e['hi']:.0f}% | "
                       f"{f'{d[0]:+.1f}（{d[1]:+.1f}～{d[2]:+.1f}）' if d else '—'} |")
        if p.get("agreement"):
            out += ["", "同一个局面选同一步的比例：", ""]
            out += [f"- {a['a']} 和 {a['b']}：{a['same']:.0%}（{a['points']} 个局面）" for a in p["agreement"] if a["same"] is not None]
        out.append("")
    out += ["## 卡表", "", "基线成员的卡表和全部参考卡表见 decklists.md；卡牌常用名见 card-glossary.md。", ""]
    return "\n".join(out)


def main(argv=None):
    for s in (sys.stdout, sys.stderr):           # a redirected or piped console is cp1252 on Windows (ENVIRONMENT
        try:                                      # pitfall 1; 11-23 review: a player's agent pipes the output)
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                         # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(prog="python -m ladder.report")
    ap.add_argument("pool")
    ap.add_argument("--out", required=True)
    ap.add_argument("--anchors-dir")
    ap.add_argument("--anchors-period", type=int, help="the anchor run shown (default: the last)")
    ap.add_argument("--puzzle", action="append", default=[])
    ap.add_argument("--note", default="")
    ap.add_argument("--games-period", type=int, help="the period whose games the win tables count (default: the last)")
    a = ap.parse_args(argv)
    r = build(Path(a.pool), a.anchors_dir, a.puzzle, a.note, a.games_period, a.anchors_period)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"report-P{r['period']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / f"report-P{r['period']}.md").write_text(markdown(r), encoding="utf-8")
    print(out / f"report-P{r['period']}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
