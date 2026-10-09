"""The value network's self-play data (the architecture thread 2026-10-09 02:18; README.md here): one row per search
decision of level-strong's self-play in the original Ramp mirror, with the search's root value, the game's result,
the turn and the seeds; games held out by index.

    python -m svsim.learn.netdata --games 50000 --deck ramp --opponent ramp --agent level-strong --explore 0 \\
        --seed 65900000 --workers 16 --out selfplay.jsonl                                       (the games)
    cd <svsim checkout> && PYTHONPATH=. python3 <this> export selfplay.jsonl --out decisions.jsonl \\
        [--encoder MODULE:FUNCTION] [--workers 16]
    python3 <this> summary decisions.jsonl

netdata already keeps everything a decision needs: the record replays the game exactly (seed, actions), and its
record["search"][i] holds the search's visits per legal move, the best child's value and the root's center, from
which learn.netdata.search_value gives the searching player's win probability. So the state encoding (the build
line's format) can be computed afterwards from the records; --encoder MODULE:FUNCTION(state, player) -> list adds
it to each row at export.

Row: g, i (action index), player, turn, own_turn (the player's turns taken), legal (moves), root_p (search_value),
visits, result (1 / 0.5 / 0 for the player), split ("val" when g % 20 == 0, else "train"), seeds (game seed,
the two agents' seeds), and "x" when an encoder is given.

Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import importlib
import json
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import from_dict
from svsim.core.engine import apply
from svsim.tools import records

HOLD_OUT = 20
ENCODER = None


def _init(encoder):
    global ENCODER
    if encoder:
        mod, fn = encoder.split(":")
        ENCODER = getattr(importlib.import_module(mod), fn)


def decisions(line):
    from svsim.learn.netdata import search_value
    rec = json.loads(line)
    st = records.start(rec)
    out = []
    winner = rec.get("winner")
    split = "val" if rec["g"] % HOLD_OUT == 0 else "train"
    for i, a in enumerate(rec["actions"]):
        thought = rec["search"][i] if i < len(rec.get("search", [])) else None
        if thought:
            me = st.active
            row = {"g": rec["g"], "i": i, "player": me, "turn": st.turn, "own_turn": st.players[me].turns_taken,
                   "legal": len(thought["visits"]), "root_p": round(search_value(thought), 5),
                   "visits": thought["visits"],
                   "result": 1.0 if winner == me else 0.0 if winner == 1 - me else 0.5,
                   "split": split, "seed": rec["seed"], "agent_seeds": rec.get("agent_seeds")}
            if ENCODER is not None:
                row["x"] = list(ENCODER(st, me))
            out.append(row)
        apply(st, from_dict(a))
    return out


def export(args):
    lines = [x for x in open(args.selfplay, encoding="utf-8") if x.strip()]
    n = 0
    with Pool(args.workers, initializer=_init, initargs=(args.encoder,)) as pool, \
            open(args.out, "w", encoding="utf-8") as fh:
        for rows in pool.imap(decisions, lines, chunksize=8):
            for r in rows:
                fh.write(json.dumps(r) + "\n")
            n += len(rows)
    print(f"{len(lines)} 局，{n} 个搜索决策")


def summary(args):
    import math
    rows = [json.loads(x) for x in open(args.decisions, encoding="utf-8") if x.strip()]
    for split in ("train", "val"):
        rs = [r for r in rows if r["split"] == split]
        if not rs:
            continue
        games = len({r["g"] for r in rs})
        eps = 1e-6
        ll = -sum(r["result"] * math.log(max(r["root_p"], eps)) + (1 - r["result"]) * math.log(max(1 - r["root_p"], eps))
                  for r in rs) / len(rs)
        print(f"{split}：{games} 局，{len(rs)} 个决策，每局 {len(rs) / games:.1f} 个；"
              f"搜索根值对终局胜负的 log loss {ll:.4f}（价值网络留出 log loss 的对照之一）")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("export")
    a.add_argument("selfplay")
    a.add_argument("--out", required=True)
    a.add_argument("--encoder", default=None)
    a.add_argument("--workers", type=int, default=16)
    b = sub.add_parser("summary")
    b.add_argument("decisions")
    args = ap.parse_args()
    {"export": export, "summary": summary}[args.cmd](args)


if __name__ == "__main__":
    main()
