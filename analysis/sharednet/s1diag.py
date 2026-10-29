"""S1's diagnostics (the architecture thread 2026-10-29 08:20Z, item 1): why a better predictor did not play better.

    python analysis/sharednet/s1diag.py leaves --net analysis/scaling/models/net-s1-20k.npz --n 56 --games 14 \
        --seed 85892000 --out analysis/sharednet/s1/diag-leaves.json
    python analysis/sharednet/s1diag.py rank --records runs/s1/rec --holdout analysis/sharednet/s1/holdout-games.json \
        --net analysis/scaling/models/net-s1-20k.npz --decisions 1500 --out analysis/sharednet/s1/diag-rank.json

`leaves`: X = mcts:N+plan+setnet=NET+netmid+netany plays --games games of B-r1 against mcts:100+plan (the deckgate's
matchups by offset, X in seat g % 2, seeds --seed + g); every call of X's SetNetEnded.score is counted by what scored
it: a finished game; the net's turn-end branch (player_moves_next False, the scored player not to act); the net's
mid-turn branch (player_moves_next False, the scored player to act); the hand-written score (player_moves_next True:
the search asks for the score of a position where the scored player moves next, which SetNetEnded leaves to its base,
the hand-written evaluate, unless +netreply answers it).

`rank`: the held-out decks' games (S1's validation: decks no net saw), at searched decisions of the recorded
mcts:100+plan (two distinct moves or more, every k-th so that about --decisions are taken, spread over the games): each
distinct move's child (EndTurn: the position after the end-of-turn abilities, search.evaluate.after_end_of_turn; else
the move applied) scored for the mover by the net (turn-end branch when the mover no longer acts, mid-turn branch when
it does) and by the hand-written score (evaluate, player_moves_next = the mover acts), and searched afresh by
mcts:400+plan (agent seed: the deal's key + the action index). Reported, over the decisions: how often each scorer's
best child is mcts:400+plan's choice (top-1), the mean Spearman correlation of each scorer's values with
mcts:400+plan's visits over the children (decisions with 3 children or more), and the same top-1 for the game's own
mcts:100+plan (its recorded visits).

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import gzip
import glob
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def leaves_main(args) -> None:
    from svsim.cards.pool import POOL
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.learn import setnet as SN
    from svsim.tools.arena import make_agent
    from svsim.tools.deckgate import matchups, read_field
    counts: Counter = Counter()
    original = SN.SetNetEnded.score

    def counted(self, state, player, player_moves_next=False):
        if state.winner is not None:
            counts["finished"] += 1
        elif player_moves_next and state.active == player and self.answers_reply(state, player):
            counts["net_reply"] += 1
        elif not player_moves_next and (self.any_pairing or (state.players[player].deck_name,
                                                            state.players[1 - player].deck_name) in self.pairs):
            counts["net_mid" if (self.mid_turn and state.active == player) else "net_end"] += 1
        else:
            counts["hand_written_moves_next" if player_moves_next else "hand_written_other"] += 1
        return original(self, state, player, player_moves_next)

    SN.SetNetEnded.score = counted
    field = read_field(args.field)
    order = matchups(len(field))
    x_spec = f"mcts:{args.n}+plan+setnet={args.net}+netmid+netany"
    for g in range(args.games):
        a, b = order[g % len(order)]
        seed = args.seed + g
        seat = g % 2
        cards = [None, None]
        cards[seat], cards[1 - seat] = [POOL[i] for i in field[a][1]], [POOL[i] for i in field[b][1]]
        agents = [None, None]
        agents[seat] = make_agent(x_spec, 2 * seed + seat)
        agents[1 - seat] = make_agent("mcts:100+plan", 2 * seed + 1 - seat + 7919)
        state = new_game(cards[0], cards[1], seed=seed)
        while not state.over:
            if state.active == seat:
                apply(state, agents[seat].act(state, legal_actions(state)))
            else:
                apply(state, agents[1 - seat].act(state, legal_actions(state)))
        print(json.dumps({"game": g, **counts}), flush=True)
    total = sum(counts.values())
    out = {"x": x_spec, "games": args.games, "seed": args.seed, "calls": total,
           "share": {k: round(v / total, 4) for k, v in sorted(counts.items())}, "counts": dict(counts),
           "condition": "对手卡表已知（牌序、手牌未知）"}
    _write(out, args.out)


def _records(folder: str):
    for path in sorted(glob.glob(str(Path(folder) / "rec-*.jsonl.gz"))):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)


def _spearman(x, y) -> float | None:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return None
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def rank_main(args) -> None:
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.learn.netdata import _search
    from svsim.learn.setnet import SetNet
    from svsim.learn.setpolicy import distinct
    from svsim.search.evaluate import after_end_of_turn, evaluate
    from svsim.search.mcts import _locator, action_key
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    held = set(json.loads(Path(args.holdout).read_text(encoding="utf-8")))
    net = SetNet.load(args.net)
    # every searched decision with two distinct moves or more, then every k-th
    sites = []
    for record in _records(args.records):
        if record["seed"] not in held:
            continue
        thoughts = record.get("search") or []
        for i, (state, _action) in enumerate(R.steps(record)):
            t = thoughts[i] if i < len(thoughts) else None
            if t is None or state.phase != Phase.MAIN:
                continue
            sites.append((record["seed"], i))
    step = max(1, len(sites) // args.decisions)
    chosen = set(sites[::step][:args.decisions])
    tally = {"decisions": 0, "net_top1": 0, "hand_top1": 0, "recorded_top1": 0, "net_hand_same_top1": 0}
    corr = {"net": [], "hand": [], "recorded": []}
    for record in _records(args.records):
        key = record["seed"]
        if key not in held:
            continue
        thoughts = record.get("search") or []
        for i, (state, _action) in enumerate(R.steps(record)):
            if (key, i) not in chosen:
                continue
            legal = legal_actions(state)
            t = thoughts[i]
            if len(legal) != len(t["visits"]):
                continue
            reps, group = distinct(state, legal)
            if len(reps) < 2:
                continue
            me = state.active
            net_v, hand_v = [], []
            for a in reps:
                if isinstance(a, EndTurn):
                    child = after_end_of_turn(state)
                else:
                    child = state.clone()
                    apply(child, a)
                if child.winner is not None:
                    v = 1e6 if child.winner == me else (-1e6 if child.winner == 1 - me else 0.0)
                    net_v.append(v)
                    hand_v.append(v)
                    continue
                moves_next = child.active == me
                net_v.append(net.logit(child, me, mid=moves_next))
                hand_v.append(evaluate(child, me, player_moves_next=moves_next))
            recorded = np.zeros(len(reps))
            for j, g in enumerate(group):
                recorded[g] = max(recorded[g], t["visits"][j])
            teacher = make_agent("mcts:400+plan", key + i)
            pick = teacher.act(state.clone(), legal)
            search = _search(teacher)
            where = _locator(state, me)
            keys = [action_key(state, a, where) for a in reps]
            visits = np.zeros(len(reps))
            if search is not None and search.last_root is not None:
                for j, k in enumerate(keys):
                    child = search.last_root.children.get(k)
                    visits[j] = child.visits if child is not None else 0
            best = keys.index(action_key(state, pick, where)) if action_key(state, pick, where) in keys else None
            if best is None:
                continue
            tally["decisions"] += 1
            tally["net_top1"] += int(int(np.argmax(net_v)) == best)
            tally["hand_top1"] += int(int(np.argmax(hand_v)) == best)
            tally["recorded_top1"] += int(int(np.argmax(recorded)) == best)
            tally["net_hand_same_top1"] += int(int(np.argmax(net_v)) == int(np.argmax(hand_v)))
            for name, vals in (("net", net_v), ("hand", hand_v), ("recorded", recorded)):
                r = _spearman(vals, visits)
                if r is not None:
                    corr[name].append(r)
            if tally["decisions"] % 100 == 0:
                print(json.dumps(tally), flush=True)
    n = tally["decisions"]
    out = {"net": args.net, "decisions": n, "every": step, "teacher": "mcts:400+plan",
           "top1": {k: round(tally[k] / n, 4) for k in ("net_top1", "hand_top1", "recorded_top1",
                                                         "net_hand_same_top1")},
           "spearman_with_teacher_visits": {k: {"mean": round(float(np.mean(v)), 4), "n": len(v),
                                                "se": round(float(np.std(v) / math.sqrt(len(v))), 4)}
                                            for k, v in corr.items() if v},
           "counts": tally, "condition": "对手卡表已知（牌序、手牌未知）"}
    _write(out, args.out)


def _write(out: dict, path: str | None) -> None:
    text = json.dumps(out, indent=1, ensure_ascii=False)
    print(text)
    if path:
        Path(path).write_text(text + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("leaves")
    l.add_argument("--net", required=True)
    l.add_argument("--n", type=int, default=56)
    l.add_argument("--games", type=int, default=14)
    l.add_argument("--seed", type=int, required=True)
    l.add_argument("--field", default="analysis/sharednet/fields/B-r1.txt")
    l.add_argument("--out", default=None)
    r = sub.add_parser("rank")
    r.add_argument("--records", required=True)
    r.add_argument("--holdout", required=True)
    r.add_argument("--net", required=True)
    r.add_argument("--decisions", type=int, default=1500)
    r.add_argument("--out", default=None)
    args = ap.parse_args()
    {"leaves": leaves_main, "rank": rank_main}[args.cmd](args)


if __name__ == "__main__":
    main()
