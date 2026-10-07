"""Salem's holds against the bot's, sliced by a payoff tiering of the evolution targets: mine, or the simulator's.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> analysis/mirror-regression/salem_games.json \
        --tiers mine|payoff [--probes analysis/mirror-regression/evolve_probes.json --results v2s=FILE ...] \
        [--selfplay LABEL FILE ...]

Tierings (2 pays off well, 1 some, 0 plain):
- mine: the grouping in evolve_waiting.py by what the evolution does (A = 2: Burnite, Erntz,
  Lumiore & Argente; B = 1: Vorlalai, Normagdala, Kimika);
- payoff: `svsim.learn.payoff.tier(defn)` of the simulator branch (measured in its sandbox, no card
  list; needs a checkout that has it).
Every turn of the player at whose decisions an evolution was legal at least once (not won that turn)
falls in one cell, by the best tier among the turn's legal targets, and when that is 0, whether a
card of tier 1 or more was in hand at the turn's start (out of reach this turn); the tier-1 cell
is split again by whether a tier-2 card was in hand. Reported: each cell's hold rate (did not evolve) for Salem and for each self-play label (both seats), and with
--probes and --results the bot's pass rate on evolve_hold / evolve_use probes by cell.
"""
import gzip
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evolve_targets import player_turns, salem_turns  # noqa: E402
from svsim.core.actions import Evolve  # noqa: E402
from svsim.core.engine import legal_actions  # noqa: E402

MINE = {"焦灰的安纳提玛·班德奈特": 2, "约束的《正义》·伊兰翠": 2, "金银绚烂·璐米欧儿&雅尔贞特": 2,
        "古旧天刀·波菈莱": 1, "禁牙的变貌·诺玛格达拉": 1, "满面笑容的烹饪·琪米卡": 1}
CELLS = ("够得着 2 档", "够得着 1 档", "2 档在手够不着", "1 档在手够不着", "只有 0 档")


def tier_fn(kind):
    if kind == "mine":
        return lambda defn: MINE.get(defn.name_zh or defn.name, 0)
    from svsim.learn.payoff import tier
    return lambda defn: tier(defn) if defn.is_follower else 0


def cell(turn, tier):
    """The turn's cell, and whether a card of a higher tier than the best reachable one was in hand."""
    me = turn[0][0].active
    reach = max((tier(s.on_field(a.uid).defn) for s, _ in turn for a in legal_actions(s) if isinstance(a, Evolve)),
                default=0)
    hand = max((tier(c.defn) for c in turn[0][0].players[me].hand), default=0)
    if reach:
        return CELLS[2 - reach], hand > reach
    return (CELLS[4 - hand] if hand else CELLS[4]), hand > 0


def rows_of(turns, tier):
    out = []
    for turn in turns:
        could = any(isinstance(a, Evolve) for s, _ in turn for a in legal_actions(s))
        used = any(isinstance(a, Evolve) for _, a in turn)
        if could or used:
            c, better = cell(turn, tier)
            out.append({"cell": c, "better_in_hand": better, "held": not used})
    return out


def table(label, rows):
    held = sum(r["held"] for r in rows)
    print(f"\n{label}：能进化的回合 {len(rows)} 个，忍住 {held}（{held / max(len(rows), 1):.0%}）")
    for c in CELLS:
        sub = [r for r in rows if r["cell"] == c]
        h = sum(r["held"] for r in sub)
        print(f"  {c:<10} {len(sub):>4} 个回合  忍住 {h:>3}（{h / max(len(sub), 1):.0%}）")
        if c == CELLS[1]:
            for b, title in ((True, "手里有 2 档"), (False, "手里没有 2 档")):
                s2 = [r for r in sub if r["better_in_hand"] == b]
                h2 = sum(r["held"] for r in s2)
                print(f"    {title:<8} {len(s2):>4} 个回合  忍住 {h2:>3}（{h2 / max(len(s2), 1):.0%}）")


def main():
    kind = sys.argv[sys.argv.index("--tiers") + 1]
    tier = tier_fn(kind)
    games = json.load(open(sys.argv[1], encoding="utf-8"))["records"]
    print(f"档位：{kind}")
    if kind == "payoff":
        names = {}
        for rec in games.values():
            for _, turn in player_turns(rec, (0,)):
                for c in turn[0][0].players[0].hand:
                    names[c.defn.name_zh or c.defn.name] = tier(c.defn)
        print("  Salem 卡组里的档：" + "，".join(f"{n} {t}" for n, t in sorted(names.items(), key=lambda x: -x[1])))
    table("Salem", rows_of([t for rec in games.values() for _, t in player_turns(rec, (0,))], tier))
    args = sys.argv
    for i, a in enumerate(args):
        if a == "--selfplay":
            label, path = args[i + 1], args[i + 2]
            opener = gzip.open if path.endswith(".gz") else open
            with opener(path, "rt", encoding="utf-8") as f:
                turns = [t for line in f if line.strip() for _, t in player_turns(json.loads(line))]
            table(f"{label}（自对弈两边）", rows_of(turns, tier))
    if "--probes" not in args:
        return
    probes = json.load(open(args[args.index("--probes") + 1], encoding="utf-8"))["positions"]
    by_game = {}
    pcell = {}
    for p in probes:
        if p["game"] not in by_game:
            by_game[p["game"]] = dict(salem_turns(games[p["game"]]))
        pcell[p["id"]] = (p["category"], cell(by_game[p["game"]][p["at"]], tier)[0])
    for i, a in enumerate(args):
        if a == "--results":
            label, path = args[i + 1].split("=", 1)
            ok = defaultdict(lambda: [0, 0])
            for line in open(path, encoding="utf-8"):
                m = re.match(r"(\S+)\s+(\d+)/(\d+)$", line.strip())
                if m and m.group(1) in pcell:
                    k = pcell[m.group(1)]
                    ok[k][0] += int(m.group(2))
                    ok[k][1] += int(m.group(3))
            print(f"\n{label} 的探针通过率，按格：")
            for cat in ("evolve_hold", "evolve_use"):
                for c in CELLS:
                    if (cat, c) in ok:
                        a_, n = ok[(cat, c)]
                        print(f"  {cat} / {c}：{a_}/{n}（{a_ / n:.0%}）")


if __name__ == "__main__":
    main()
