"""When players spend their evolution points over a whole game: Salem, the bots Salem played, self-play.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --salem analysis/mirror-regression/salem_games.json \
        [--selfplay LABEL FILE ...] [--json out.json]

Each player has 2 evolution and 2 super-evolution points (4 in all); one
evolution a turn, from own turn 5 (going first) / 4 (second), super-evolution
from 7 / 6. Per game and side:
- uses: the own turns on which a point was spent (an Evolve action);
- t4: the own turn of the 4th point (None if fewer than 4 were spent); reported over the games that
  spent all four, and over all games with an unspent 4th point counted as one turn after the side's
  last own turn (so more games spending all four can't move it by itself);
- left8: points left at the start of own turn 8 (games that reached it);
- unused: points left when the game ended;
- dry: own turns played after the last point was spent (0 if points remain).
Grouped as all games and long games (24 or more turns in all). --salem reads
Salem's games (seat 0 Salem, seat 1 the web bot, by batch); --selfplay reads
learn.netdata records or plain records (both seats).
"""
import argparse
import gzip
import json
import statistics
from collections import defaultdict

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import Evolve, from_dict
from svsim.core.engine import apply
from svsim.tools import records

LONG = 24


def lines_of(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [line for line in f if line.strip()]


def pacing(record, seats=(0, 1)):
    st = records.start(record)
    uses = {0: [], 1: []}
    left8 = {0: None, 1: None}
    last_turn = None
    for data in record["actions"]:
        a = from_dict(data)
        if (st.turn, st.active) != last_turn:
            last_turn = (st.turn, st.active)
            p = st.players[st.active]
            if p.turns_taken == 8 and left8[st.active] is None:
                left8[st.active] = p.ep + p.sep
        if isinstance(a, Evolve):
            uses[st.active].append(st.players[st.active].turns_taken)
        apply(st, a)
        if st.over:
            break
    out = []
    for s in seats:
        p = st.players[s]
        u = uses[s]
        out.append({"seat": s, "first": st.first == s, "uses": u, "t4": u[3] if len(u) >= 4 else None,
                    "left8": left8[s], "unused": p.ep + p.sep, "own_turns": p.turns_taken,
                    "dry": (p.turns_taken - u[-1]) if u and p.ep + p.sep == 0 else 0,
                    "turns": st.turn, "won": st.winner == s})
    return out


def summary(rows):
    if not rows:
        return None
    t4 = [r["t4"] for r in rows if r["t4"] is not None]
    l8 = [r["left8"] for r in rows if r["left8"] is not None]
    gap = [r["uses"][3] - r["uses"][0] for r in rows if len(r["uses"]) >= 4]
    # over every game: a side that did not spend its 4th point counts as reaching it one turn after its last
    # (not reached), so a change in how many games spend all four does not move the mean by itself
    t4_all = [r["t4"] if r["t4"] is not None else r["own_turns"] + 1 for r in rows]
    return {"games": len(rows), "all4": len(t4) / len(rows), "t4": statistics.mean(t4) if t4 else float("nan"),
            "t4_all": statistics.mean(t4_all),
            "gap": statistics.mean(gap) if gap else float("nan"),
            "left8": statistics.mean(l8) if l8 else float("nan"), "n8": len(l8),
            "unused": statistics.mean(r["unused"] for r in rows),
            "dry": statistics.mean(r["dry"] for r in rows),
            "first_use": statistics.mean(r["uses"][0] - (5 if r["first"] else 4) for r in rows if r["uses"])
            if any(r["uses"] for r in rows) else float("nan")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salem", default=None)
    ap.add_argument("--selfplay", nargs=2, action="append", default=[], metavar=("LABEL", "FILE"))
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    groups = []
    if args.salem:
        data = json.load(open(args.salem, encoding="utf-8"))
        salem, bots = [], defaultdict(list)
        for gid, rec in data["records"].items():
            meta = data.get("meta", {}).get(gid, {})
            s, b = pacing(rec)
            salem.append({**s, "game": gid})
            bots[meta.get("version") or "旧网页 bot"].append({**b, "game": gid})
        groups.append((f"Salem（{len(salem)} 局）", salem))
        for k, v in bots.items():
            groups.append((f"{k}（对 Salem，{len(v)} 局）", v))
    for label, path in args.selfplay:
        rows = [r for line in lines_of(path) for r in pacing(json.loads(line))]
        groups.append((f"{label}（{len(rows) // 2} 局）", rows))
    print(f"{'来源':<28}{'组':>6}{'局×方':>7}{'4点用完':>8}{'第4点回合':>10}{'(全部局)':>9}{'1→4间隔':>9}{'第8回合剩点':>12}{'(n)':>5}"
          f"{'终局剩点':>9}{'用完后空转回合':>14}{'首次用点晚几回合':>16}")
    for label, rows in groups:
        for g, sub in (("全部", rows), (f"长局", [r for r in rows if r["turns"] >= LONG])):
            s = summary(sub)
            if s is None:
                continue
            print(f"{label:<28}{g:>6}{s['games']:>7}{s['all4']:>8.0%}{s['t4']:>10.1f}{s['t4_all']:>9.1f}{s['gap']:>9.1f}"
                  f"{s['left8']:>12.2f}"
                  f"{s['n8']:>5}{s['unused']:>9.2f}{s['dry']:>14.2f}{s['first_use']:>16.2f}")
    if args.json:
        json.dump({label: rows for label, rows in groups}, open(args.json, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
