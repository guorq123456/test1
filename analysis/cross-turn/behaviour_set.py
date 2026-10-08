"""The behaviour acceptance set for the build session's B (imitating Salem's games): positions and labels.

    cd <svsim checkout> && PYTHONPATH=.:<test1>/analysis/cross-turn:<test1>/analysis/card-value:<test1>/analysis/mirror-regression \
        python3 <this> analysis/mirror-regression/salem_games.json analysis/mirror-regression/evolve_probes.json \
        --out analysis/cross-turn/behaviour_set_b.json

The architecture thread (23:55Z): Salem's 24 held turns of the acceptance table (evolve_hold, counted: the
turns where Erntz came down unevolved are left out) and the 9 turns where he spent a point in the key cell
"A 档在手、够不着" (all on his own turns 4-5, just after unlocking; evolve_use), with, per position: the game
(key in salem_games.json's "records"), the action index the turn starts at (the probe's "at": the state is
records.start(record) with record["actions"][:at] applied, Salem (seat 0) to act), the own turn and the
global turn, Salem's choice, the tier cell under both definitions of "out of reach" (by the line he played:
the standard table's; by what the position allowed: 1 号's forks' rule, hold_vs_spend.new_cell), and the
standard table's other cells. The one turn that is in the key cell only by the second definition (a spend)
is added and marked, so both definitions can be computed.
"""
import argparse
import json

from evolve_hold_review import TIER, standard_row
from evolve_targets import salem_turns
from glossary import common
from hold_vs_spend import CELL, LABEL, new_cell
from svsim.core.actions import Evolve


def choice(turn):
    evo = [(s.on_field(a.uid).defn.name_zh or "", a.super_) for s, a in turn if isinstance(a, Evolve)]
    if not evo:
        return "留（不进化）"
    return "花：" + "、".join(("超进化 " if sup else "进化 ") + common(n) for n, sup in evo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("games")
    ap.add_argument("probes")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    games = json.load(open(args.games, encoding="utf-8"))["records"]
    probes = json.load(open(args.probes, encoding="utf-8"))["positions"]
    rows = []
    for p in probes:
        if p["category"] not in ("evolve_hold", "evolve_use"):
            continue
        turn = dict(salem_turns(games[p["game"]]))[p["at"]]
        row = standard_row(turn)
        if row is None or row.get("erntz_plain"):
            continue
        old, new = row["tier"], new_cell(turn)
        held = p["category"] == "evolve_hold"
        if held:
            group = "留点（24）"
        elif old == CELL:
            group = "关键格的花点（9）"
        elif new == CELL:
            group = "只在按局面可能下进关键格的花点（1）"
        else:
            continue
        s0 = turn[0][0]
        p0 = s0.players[0]
        rows.append({
            "group": group,
            "probe_id": p["id"],
            "category": p["category"],
            "check": p["check"],
            "game": p["game"],
            "at": p["at"],
            "own_turn": p["context"]["own_turn"],
            "first": p["context"]["first"],
            "global_turn": s0.turn,
            "pp": f"{p0.pp}/{p0.max_pp}",
            "ep_sep": [p0.ep, p0.sep],
            "salem": choice(turn),
            "a_cards_in_hand": sorted({common(c.defn.name_zh or "") for c in p0.hand if TIER(c.defn) == 2}),
            "cell_by_line_played": LABEL[old],
            "cell_by_position": LABEL[new],
            "payoff_in_hand_out_of_reach": row["class"] == "收益牌在手、本回合够不着",
            "normal_only": bool(row["normal_only"]),
        })
    order = {"留点（24）": 0, "关键格的花点（9）": 1, "只在按局面可能下进关键格的花点（1）": 2}
    rows.sort(key=lambda r: (order[r["group"]], r["game"], r["at"]))
    out = {
        "condition": "对手卡表已知（牌序、手牌未知）",
        "games_file": "analysis/mirror-regression/salem_games.json",
        "probes_file": "analysis/mirror-regression/evolve_probes.json",
        "salem_seat": 0,
        "state": "records.start(records[game]) then records[game]['actions'][:at] applied; seat 0 (Salem) to act",
        "positions": rows,
    }
    json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(r["group"] for r in rows))
    print(Counter((r["group"], r["cell_by_line_played"], r["cell_by_position"]) for r in rows))


if __name__ == "__main__":
    main()
