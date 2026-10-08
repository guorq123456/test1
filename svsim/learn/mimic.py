"""A prior that mimics the player (main line (b), route B; the architecture session, 2026-10-07 23:55).

Salem chose to try making the search's root prior lean towards the moves he makes, before closing (b)
(docs/architecture.md §9.2 "留进化点"). Two policy heads share one encoding:

- the self-play head, fitted to the visit counts (π) of v2's own search in Ramp mirror self-play
  (learn.netdata records, "search"), as learn.policy's head was;
- the player's head, fitted to the moves the player made (one-hot; their side only, moves marked as
  mistakes left out, as learn.data.choices does);

and the prior is the mixture  P = w x P_player + (1 - w) x P_self-play  (`MimicPrior`, arena "+mimic=W").

The encoding has no card ids and no deck ids (the player's two hard rules: no per-card values, no
features that name a deck). A position is the version-3 contexts of both sides' evolution and
super-evolution points (learn.features.contexts: turns since unlocking, payoff reachable now or later,
payoff left in the deck, ...), plus the turn, play points, points left, life, boards and hands. A move is
what kind it is, and for the evolution decisions what it spends a point on:

- evolve / super-evolve: the target's payoff tier (learn.payoff.tier, measured in the role sandbox, not a
  card table), its cost, whether it came down this turn (a big follower played and evolved), whether it
  can attack this turn, the points left after it, and whether a higher-tier payoff in hand is out of reach
  (spending on a poor target while holding a good one);
- ending the turn: whether an evolution was still legal (ending without evolving) and the best tier it
  could have gone to, and the play points left unused;
- playing a card: its cost, whether it is a follower, its payoff tier, whether it could still be evolved
  this turn after it (the first half of "play the big one and evolve it"), whether it uses all the play
  points;
- attacking: the leader or a follower, whether the target dies, whether the attacker dies.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.learn.policy import KINDS, PolicyNet, _kind, _source, _target

MIMIC = Path(__file__).resolve().parent / "policies" / "mimic"
TIERS = (0, 1, 2)


def position(state) -> list[float]:
    """The position from the side to act, without card or deck ids."""
    from svsim.core.engine import EVOLVE_TURN
    from svsim.learn.features import contexts
    me = state.active
    p, o = state.players[me], state.players[1 - me]
    mine_e, mine_s = contexts(state, me, False)
    theirs_e, theirs_s = contexts(state, 1 - me, True)
    since = p.turns_taken - EVOLVE_TURN[state.first == me]
    side = lambda q: [len(q.followers) / 5.0, sum(f.atk for f in q.followers) / 20.0,
                      sum(max(f.life, 0) for f in q.followers) / 20.0]
    return (mine_e + mine_s + theirs_e + theirs_s +
            [p.turns_taken / 10.0, max(since, -1) / 5.0, p.pp / 10.0, p.max_pp / 10.0, float(p.bonus_ready),
             p.ep / 3.0, p.sep / 2.0, o.ep / 3.0, o.sep / 2.0, p.leader_hp / 20.0, o.leader_hp / 20.0,
             len(p.hand) / 9.0, len(o.hand) / 9.0] + side(p) + side(o))


def decision(state, legal) -> dict:
    """What every move of one decision is compared with: whether an evolution is legal and the best tier
    it could go to, and the best tier of a payoff in hand that can't be played now."""
    from svsim.learn.payoff import tier
    me = state.active
    p = state.players[me]
    evolvable = [state.in_play(a.uid) for a in legal if isinstance(a, Evolve)]
    pp = p.pp + (1 if p.bonus_ready and not p.bonus_active else 0)
    return {"evolve_legal": bool(evolvable),
            "evolve_best": max((tier(c.defn) for c in evolvable if c is not None), default=0),
            "held_out_of_reach": max((tier(c.defn) for c in p.hand if c.defn.is_follower and c.cost > pp), default=0),
            "pp": pp}


MOVE_WIDTH = len(KINDS) + 3 + 5 + 3 + 3 + 4 + 3


def move(state, action, ctx: dict) -> list[float]:
    """One move, without card ids (see the module's docstring)."""
    from svsim.core.engine import EVOLVE_TURN
    from svsim.learn.payoff import tier
    me = state.active
    p = state.players[me]
    out = [0.0] * MOVE_WIDTH
    out[KINDS.index(_kind(action))] = 1.0
    base = len(KINDS)
    if isinstance(action, Evolve):                      # what the point is spent on
        card = state.in_play(action.uid)
        if card is not None:
            t = tier(card.defn)
            out[base + t] = 1.0
            left = (p.sep - 1) if action.super_ else (p.ep - 1)
            fresh = card.entered_turn == state.turn
            out[base + 3:base + 8] = [card.cost / 10.0, float(fresh), float(card.attacks_made == 0),
                                      max(left, 0) / 3.0, float(ctx["held_out_of_reach"] > t)]
    base += 8
    if isinstance(action, EndTurn):                     # ending the turn: with an evolution left undone?
        out[base:base + 3] = [float(ctx["evolve_legal"]), ctx["evolve_best"] / 2.0, ctx["pp"] / 10.0]
    base += 3
    if isinstance(action, PlayCard):
        card = _source(state, action)
        if card is not None:
            follower = card.defn.is_follower
            t = tier(card.defn) if follower else 0
            unlocked = p.turns_taken >= EVOLVE_TURN[state.first == me]
            out[base:base + 3] = [card.cost / 10.0, float(follower), float(card.cost >= ctx["pp"])]
            out[base + 3 + t] = float(follower)
            out[base + 6] = float(follower and unlocked and (p.ep > 0 or p.sep > 0))
    base += 3 + 4
    if isinstance(action, Attack):
        attacker = _source(state, action)
        where, target = _target(state, action)
        atk = attacker.atk if attacker is not None else 0
        out[base:base + 3] = [float(where == "enemy_leader"),
                              float(target is not None and atk >= max(target.life, 0)),
                              float(target is not None and attacker is not None and target.atk >= attacker.life)]
    return out


def rows(state, legal) -> np.ndarray:
    """[position + move] for each legal move."""
    pos = position(state)
    ctx = decision(state, legal)
    return np.array([pos + move(state, a, ctx) for a in legal], dtype=np.float64)


class MimicNet(PolicyNet):
    """learn.policy's head (one tanh layer, softmax over the legal moves) on this module's encoding."""

    def __init__(self, params: dict, mean, std, vocab=(), info: dict | None = None):
        super().__init__(params, mean, std, [], info)

    def scores(self, state, actions) -> np.ndarray:
        return self.scores_of(rows(state, actions))


# --- data ----------------------------------------------------------------------------

def selfplay_decisions(line: str) -> list:
    """(rows, π) for each decision of v2's search in one self-play record (both sides); fork branches are
    left out (they were played to a rule), their controls are plain games."""
    from svsim.learn.policy import decisions
    record = json.loads(line)
    if (record.get("branch") or {}).get("kind", "control") != "control":
        return []
    return [(rows(state, legal), np.asarray(pi)) for state, legal, pi, _ in decisions(record)]


def player_decisions(record: dict, player: int = 0, weight_of=None) -> list:
    """(rows, one-hot of the move made, weight) for each of `player`'s main-phase decisions with a choice, in
    one record; moves marked as mistakes (record["mistakes"]) are left out, as learn.data.choices does.
    `weight_of(k)`: the weight of the decision at action index k (0: left out; see `decision_weights`)."""
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.tools import records as R
    out = []
    mistakes = set(record.get("mistakes", []))
    for k, (state, action) in enumerate(R.steps(record)):
        if state.active != player or state.phase != Phase.MAIN or k in mistakes:
            continue
        legal = legal_actions(state)
        if action not in legal:
            break
        if len(legal) < 2:
            continue
        w = 1.0 if weight_of is None else weight_of(k)
        if w <= 0:
            continue
        target = np.zeros(len(legal))
        target[legal.index(action)] = 1.0
        out.append((rows(state, legal), target, w))
    return out


def decision_weights(path: str, drop_flags=(), soft: float | None = None) -> dict:
    """{(record id, action index): weight} from a JSON-lines file of the player's decisions (the analysis
    session's salem_mistakes.jsonl: "game", "at", "regret" as a share of win rate, "flags", "evolve"):
    0 for a decision carrying any of `drop_flags`, exp(-regret / soft) with `soft` for one that isn't an
    evolution decision; 1 otherwise (and for decisions not in the file)."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            key = (str(d["game"]), int(d["at"]))
            if set(d.get("flags") or ()) & set(drop_flags):
                out[key] = 0.0
            elif soft and not d.get("evolve") and d.get("regret") is not None:
                out[key] = float(np.exp(-max(float(d["regret"]), 0.0) / soft))
    return out


def stack(items: list):
    """(X, starts, target, weights) for PolicyNet.train from [(rows, target[, weight])]."""
    X = np.concatenate([it[0] for it in items])
    target = np.concatenate([it[1] for it in items])
    starts = np.cumsum([0] + [len(it[0]) for it in items[:-1]])
    weights = np.array([it[2] if len(it) > 2 else 1.0 for it in items])
    return X, starts, target, weights


# --- the prior ---------------------------------------------------------------------------

class MimicPrior:
    """P = w x the player's head + (1 - w) x the self-play head, for the matchup the heads were fitted on
    (their info["matchup"], named decks); no prior (None) elsewhere."""

    def __init__(self, w: float, folder: Path | None = None):
        folder = Path(folder) if folder else MIMIC
        self.w = w
        self.player = MimicNet.load(folder / "player.npz")
        self.selfplay = MimicNet.load(folder / "selfplay.npz")
        self.matchup = tuple(self.player.info.get("matchup", "ramp-ramp").split("-", 1))

    def priors(self, state, actions):
        from svsim.learn.model import deck_key
        me = state.active
        if (deck_key(state, me), deck_key(state, 1 - me)) != self.matchup:
            return None
        X = rows(state, actions)
        mix = np.zeros(len(actions))
        for w, net in ((self.w, self.player), (1 - self.w, self.selfplay)):
            if w > 0:
                z = net.scores_of(X)
                z = np.exp(z - z.max())
                mix += w * z / z.sum()
        return mix


# --- fitting ---------------------------------------------------------------------------------

def main() -> None:
    """python -m svsim.learn.mimic selfplay --games A.jsonl [B.jsonl] --limit 600 --out DIR
    python -m svsim.learn.mimic player --games salem_games.json --player 0 [--leave-out ID ...] --out DIR"""
    import argparse
    from multiprocessing import Pool
    parser = argparse.ArgumentParser(description="fit the mimic prior's heads (learn.mimic)")
    parser.add_argument("head", choices=("selfplay", "player"))
    parser.add_argument("--games", nargs="+", required=True,
                        help="selfplay: learn.netdata JSON lines; player: a JSON of {'records': {id: record}} "
                             "or JSON lines of records")
    parser.add_argument("--out", required=True)
    parser.add_argument("--matchup", default="ramp-ramp")
    parser.add_argument("--player", type=int, default=0, help="the player's seat in the records")
    parser.add_argument("--leave-out", nargs="*", default=[], help="record ids not to fit on (held-out folds)")
    parser.add_argument("--decisions", default=None,
                        help="player: JSON lines of the player's decisions with flags and regret (decision_weights)")
    parser.add_argument("--drop-flags", nargs="*", default=[], help="player: leave out decisions with these flags")
    parser.add_argument("--soft", type=float, default=None,
                        help="player: weight exp(-regret / SOFT) for decisions that aren't evolution decisions")
    parser.add_argument("--limit", type=int, default=600, help="selfplay: games at most")
    parser.add_argument("--hidden", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.head == "selfplay":
        lines = []
        for path in args.games:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if (json.loads(line).get("branch") or {}).get("kind", "control") == "control":
                        lines.append(line)
                    if len(lines) >= args.limit:
                        break
            if len(lines) >= args.limit:
                break
        with Pool(args.workers) as pool:
            per_game = pool.map(selfplay_decisions, lines, chunksize=4)
        ids = [str(i) for i in range(len(per_game))]
    else:
        records = {}
        for path in args.games:
            text = Path(path).read_text(encoding="utf-8")
            try:
                whole = json.loads(text)
            except json.JSONDecodeError:
                whole = None
            if isinstance(whole, dict) and "records" in whole:
                records.update(whole["records"])
            else:
                for i, line in enumerate(text.splitlines()):
                    records[f"{Path(path).stem}:{i}"] = json.loads(line)
        ids = [k for k in records if k not in set(args.leave_out)]
        table = decision_weights(args.decisions, args.drop_flags, args.soft) if args.decisions else {}
        per_game = [player_decisions(records[k], args.player, lambda i, g=k: table.get((g, i), 1.0)) for k in ids]
    rng = np.random.default_rng(args.seed)                # held-out decisions for early stopping: by game
    order = rng.permutation(len(per_game))
    val_games = set(order[:max(1, len(per_game) // 8)].tolist())
    fit = [d for g, ds in enumerate(per_game) if g not in val_games for d in ds]
    val = [d for g, ds in enumerate(per_game) if g in val_games for d in ds]
    X, starts, target, weights = stack(fit)
    Xv, sv, tv, wv = stack(val)
    print(f"{args.head}: {len(per_game)} games, {len(fit)} decisions to fit, {len(val)} held out, {X.shape[1]} inputs",
          flush=True)
    net = MimicNet.train(X, starts, target, [], Xv, sv, tv, hidden=args.hidden, seed=args.seed,
                         weights=weights, weights_val=wv,
                         info={"head": args.head, "matchup": args.matchup, "games": args.games,
                               "left_out": args.leave_out, "decisions": len(fit) + len(val),
                               "decisions_file": args.decisions, "drop_flags": args.drop_flags, "soft": args.soft,
                               "mistakes_filtered": bool(args.decisions)})
    net.__class__ = MimicNet
    name = "player" if args.head == "player" else "selfplay"
    net.save(out / f"{name}.npz")
    top = np.mean([int(np.argmax(net.scores_of(d[0])) == int(np.argmax(d[1]))) for d in val]) if val else float("nan")
    print(f"saved {out / (name + '.npz')}: held-out cross entropy {net.info['cross_entropy']:.4f}, "
          f"top choice = the target's {top:.1%}", flush=True)


if __name__ == "__main__":
    main()
