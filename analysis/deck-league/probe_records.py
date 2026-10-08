"""Missed lethals and time per turn in league records, with tools.smoke's lethal probe.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --pair elf-t/elf-t --workers 2 --out probe.jsonl FILE[+FILE...]
    python3 <this> --report probe_a.jsonl probe_b.jsonl

The architecture thread (23:01Z): with the elf-t mirror rerun, the cost of 1 号's new default of the
agents' lethal check (af086ee, screen 200:1000:4) on this mirror, as the smoke runs measured it. At the
start of every turn of every game (a game repeated move for move counts once), search.lethal's
LethalSearch with tools.smoke's PROBE_NODES (50000, no screen; seeded by the game's seed) looks for a
sure lethal; a turn where it finds one and the side to act has not won by the end of that turn is a
missed lethal, as in tools.smoke. --cheap uses 1 号's banding instead of the full probe on every turn
(search.lethal's screen 1000 and near (50000, 4): a position whose damage estimate falls more than 4 short
of the enemy leader's defense gets 1000 nodes, the rest 50000); 1 号's smoke recheck found every recoverable
missed lethal within 1-4 points, and on three test games it found the same lethals, about 10x faster.
Time per turn here is the game's wall time over its turns (the league
keeps no per-turn time). The same probe on the records of both versions. Condition: the opponent's
40-card list is known (order and hand not).
"""
import argparse
import gzip
import json
import sys
from multiprocessing import Pool

PROBE_NODES = 50000
SCREEN = None          # --cheap: (1000, (50000, 4)), search.lethal's screen with a near band


def probe_game(rec):
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    from svsim.core.enums import Phase
    from svsim.search.lethal import LethalSearch
    from svsim.tools import records
    st = records.start(rec)
    screen, near = SCREEN if SCREEN else (None, None)
    probe = LethalSearch(max_nodes=PROBE_NODES, seed=rec["seed"], screen=screen, near=near)
    turns, cur = [], None
    for data in rec["actions"]:
        if st.phase == Phase.MAIN and (cur is None or cur["turn"] != st.turn):
            if cur is not None:
                cur["won"] = False
                turns.append(cur)
            found = probe.solve(st.clone())
            cur = {"turn": st.turn, "player": st.active, "lethal": bool(found.sure), "complete": bool(found.complete)}
        apply(st, from_dict(data))
        if st.over:
            break
    if cur is not None:
        cur["won"] = st.winner == cur["player"]
        turns.append(cur)
    return turns


def job(g):
    turns = probe_game(g["record"])
    return {"k": g["k"], "seat_a": g["seat_a"], "seconds": g["seconds"], "turns_n": g["turns"],
            "lethal": sum(t["lethal"] for t in turns), "missed": sum(t["lethal"] and not t["won"] for t in turns),
            "incomplete": sum(not t["complete"] and not t["lethal"] for t in turns), "probed": len(turns)}


def load(paths, pairing):
    latest = {}
    for path in paths:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            if g["pair"] == pairing:
                latest[(g["k"], g["seat_a"])] = g
    by_k = {}
    for (k, _), g in sorted(latest.items()):
        by_k.setdefault(k, []).append(g)
    games = []
    for gs in by_k.values():
        if len(gs) == 2 and gs[0]["record"]["actions"] == gs[1]["record"]["actions"]:
            gs = gs[:1]
        games += gs
    return games


def report(paths):
    print("条件：对手卡表已知（牌序、手牌未知）。探针 = tools.smoke 的 LethalSearch（50000 节点，不设筛选）；"
          "每回合用时 = 整局墙钟 ÷ 回合数（双方合计）。")
    for path in paths:
        rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        secs = sum(r["seconds"] for r in rows)
        turns = sum(r["turns_n"] for r in rows)
        print(f"  {path.split('/')[-1]}：{len(rows)} 局，每回合 {1000 * secs / turns:.0f} ms；"
              f"探针找到必杀 {sum(r['lethal'] for r in rows)} 回合，没杀 {sum(r['missed'] for r in rows)} 回合"
              f"（{sum(r['missed'] > 0 for r in rows)} 局）；探针没搜完 {sum(r['incomplete'] for r in rows)} 回合 / "
              f"{sum(r['probed'] for r in rows)}")


def main():
    if "--report" in sys.argv:
        report(sys.argv[sys.argv.index("--report") + 1:])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("files")
    ap.add_argument("--pair", required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--cheap", action="store_true")
    ap.add_argument("--only", nargs="*", default=None, help="K:SEAT_A of the games to probe (e.g. the ones that differ)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    global SCREEN
    if args.cheap:
        SCREEN = (1000, (50000, 4))
    games = load(args.files.split("+"), args.pair)
    if args.only:
        keep = {tuple(int(x) for x in o.split(":")) for o in args.only}
        games = [g for g in games if (g["k"], g["seat_a"]) in keep]
    with Pool(args.workers) as pool, open(args.out, "w", encoding="utf-8") as fh:
        for r in pool.imap_unordered(job, games, chunksize=1):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


if __name__ == "__main__":
    main()
