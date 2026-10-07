"""Self-play games for the value network, and every position in them as training rows.

    python -m svsim.learn.netdata --games 2000 --out games.jsonl          # play (resumable)

Games are stored as records (tools.records: the deal and the actions), one per
line, so positions can be encoded again with other features without playing
again. Each decision the search made also keeps what the search thought
(record["search"][i], aligned with record["actions"]; None where the lethal
search or the planner chose): the visits of each legal move in
legal_actions order ("visits"), and the search's value of its best move
("value", squashed against the starting position's score "center"), the
targets of a policy head and of a value trained on search values. With probability `explore` a move is replaced by a random legal one, so
the network also sees the positions that bad moves lead to: the search scores
every move it tries, most of them moves the bot would never play, and an
evaluation that has only seen its own good positions guesses wildly there (the
hidden-layer model of 2026-10-06 lost 22 to 78).

`rows(record)` replays a game and yields every position the search can be
asked to score, labelled with the game's result for the player scoring it:
each decision point, for the player to act (phase ACT: inside their turn,
its start included), and the position after each turn's end-of-turn
abilities, before the next turn starts, for the player who ended it (phase
ENDED; MCTS stops a line there). With the opponent's turn played out
(`mcts-reply`), the leaf is the start of the player's next turn, an ACT
position.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from multiprocessing import Pool

ACT, ENDED = 0, 1


def play(job):
    """One self-play game (`spec` on both sides) as a record, with exploration. With `fork` (job[7]), a
    list of two records instead: the game, and a branch of it from the first turn a side could keep its
    evolution points for a payoff card out of reach (or had just unlocked evolving) in which it keeps
    them until the card comes within reach (at most 3 turns; 2 after an unlock), then plays on;
    record["branch"] says which is which, from which action ("i") and for which side."""
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    g, seed, deck, opponent, spec, explore = job[:6]
    hold = job[6] if len(job) > 6 else 0.0
    fork = job[7] if len(job) > 7 else False
    triggers = tuple(job[8]) if len(job) > 8 and job[8] else ("payoff", "deck", "unlock")
    mode = job[9] if len(job) > 9 and job[9] else "all"          # the branch's hold: see _keep
    rng = random.Random(seed * 7919 + g)
    seat = g % 2
    cards = [None, None]
    cards[seat], cards[1 - seat] = decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])
    agents = [make_agent(spec, seed * 1000 + 2 * g + i) for i in (0, 1)]
    state = new_game(cards[0], cards[1], seed=seed * 100003 + g)
    record = R.new_record(cards[0], cards[1], seed * 100003 + g, state.first, f"{spec} / {spec}")
    record["g"], record["explore"] = g, explore
    record["names"] = [deck, opponent] if seat == 0 else [opponent, deck]   # ui.session.DECKS keys by seat
    _identity(record, cards, seed * 7919 + g, [seed * 1000 + 2 * g + i for i in (0, 1)])
    record["search"] = []
    if not fork:
        _run(state, agents, record, rng, explore, hold)
        return record
    snapshot = {}
    _run(state, agents, record, rng, explore, 0.0, snapshot=snapshot, triggers=triggers)
    if not snapshot:
        return [record]
    branch = json.loads(json.dumps({k: v for k, v in snapshot["record"].items()}))
    branch_agents = [make_agent(spec, seed * 1000 + 2 * g + i + 500000) for i in (0, 1)]
    branch_rng = random.Random()
    branch_rng.setstate(snapshot["rng"])
    info = {k: snapshot[k] for k in ("i", "player", "turn", "trigger", "target")}
    record["branch"] = dict(info, kind="control")
    branch["branch"] = dict(info, kind="hold", agent_seeds=[seed * 1000 + 2 * g + i + 500000 for i in (0, 1)],
                            rng_state=snapshot["rng"])   # random.Random().setstate((3, tuple(x[1]), None))
    branch["branch"]["hold"] = mode
    _run(snapshot["state"], branch_agents, branch, branch_rng, explore, 0.0, keep=dict(info, held=0, mode=mode))
    return [record, branch]


def _run(state, agents, record, rng, explore, hold, snapshot=None, keep=None,
         triggers=("payoff", "deck", "unlock")) -> None:
    """Play `state` out, adding to `record`. `snapshot` (a dict): fill it at the first fork point (see
    play). `keep`: the branch's side keeps its points (no evolving) as play describes."""
    from svsim.core.engine import apply, legal_actions
    from svsim.tools import records as R
    held = {}                                       # (player, turn) -> the restriction held this turn
    vetoes = [_search(a).veto if _search(a) is not None else None for a in agents]
    starts = set()
    while not state.over:
        legal = legal_actions(state)
        search = _search(agents[state.active])
        start = state.phase.name == "MAIN" and (state.active, state.turn) not in starts
        if start:
            starts.add((state.active, state.turn))
            p = state.players[state.active]             # the root hand and deck of the turn (search._root_deck)
            record.setdefault("turn_starts", []).append({"i": len(record["actions"]), "player": state.active,
                                                         "hand": [c.uid for c in p.hand],
                                                         "deck": [c.uid for c in p.deck]})
        if hold and search is not None and state.phase.name == "MAIN":
            _hold(state, search, vetoes[state.active], held, hold, rng, record)
        if snapshot is not None and not snapshot and start:
            trigger = _fork_point(state, triggers)
            if trigger is not None:
                snapshot.update(state=state.clone(), rng=rng.getstate(), i=len(record["actions"]),
                                player=state.active, turn=state.turn, trigger=trigger[0], target=trigger[1],
                                record=json.loads(json.dumps(record)))
        if keep is not None and start and state.active == keep["player"] and search is not None:
            _keep(state, search, vetoes[state.active], keep, record)
        if search is not None:
            search.last_root = None
        planner = _planner(agents[state.active])
        if planner is not None:
            planner.last_plan = None
        action = agents[state.active].act(state, legal)
        record["search"].append(_thought(state, legal, search))
        if planner is not None and planner.last_plan is not None:      # a cross-turn planner measured
            record.setdefault("plans", []).append(_plan(state, len(record["actions"]), planner.last_plan,
                                                        record["names"]))
        if explore and len(legal) > 1 and state.players[state.active].turns_taken >= 1 and rng.random() < explore:
            action = rng.choice(legal)
        R.add(record, action)
        apply(state, action)
    record["winner"] = state.winner


def _identity(record, cards, rng_seed: int, agent_seeds: list) -> None:
    """What a later pairing of play-outs (the hand-value thread's G_end) and the deck-profile work need
    besides the deal and the actions (docs/architecture.md §10): each seat's named deck (cards.decks.NAMED,
    "" for another) and deck hash (cards in id order), the seed of the exploration's random numbers and the agents' seeds;
    record["turn_starts"] adds each turn's hand and deck (card uids) as the search's root saw them, and a
    fork branch its agents' seeds and the random numbers' state it continued from."""
    from svsim.cards import decks
    record["deck_keys"] = [decks.identify(c) or "" for c in cards]
    record["deck_hashes"] = [decks.to_hash(sorted(c, key=lambda d: d.card_id)) for c in cards]   # canonical
    record["rng_seed"], record["agent_seeds"] = rng_seed, agent_seeds


def _fork_point(state, triggers=("payoff", "deck", "unlock")):
    """("payoff", card id) if the side to act could evolve and has a payoff follower in hand out of reach;
    ("deck", "tier2") if it has no tier-2 one in hand but drawing one (any) within two turns is at least 25%
    likely (one draw a turn); ("unlock", None) in its first two turns of evolving; else None."""
    from svsim.core.engine import EVOLVE_TURN
    from svsim.learn.payoff import tier
    p = state.players[state.active]
    first = state.first == state.active
    if p.ep <= 0 or p.turns_taken < EVOLVE_TURN[first]:
        return None
    pp = p.max_pp + (1 if p.bonus_ready else 0)
    later = sorted((c for c in p.hand if tier(c.defn) > 0 and c.cost > pp),
                   key=lambda c: (-tier(c.defn), c.cost))
    if later and "payoff" in triggers:
        return "payoff", later[0].defn.card_id
    if "deck" in triggers and not any(tier(c.defn) == 2 for c in p.hand):  # waiting for one still in the deck
        from svsim.learn.features import first_draw
        copies = sum(1 for c in p.deck if tier(c.defn) == 2)
        if copies and sum(first_draw(copies, len(p.deck), 2)) >= 0.25:
            return "deck", "tier2"
    if "unlock" in triggers and p.turns_taken - EVOLVE_TURN[first] <= 1:
        return "unlock", None
    return None


def _keep(state, search, own_veto, keep, record) -> None:
    """At the start of the branch side's turn: no evolving this turn while its target is out of reach.
    keep["mode"] "selective" (the architecture session's second round, 2026-10-07): evolving and
    super-evolving stay allowed on tier-2 followers (learn.payoff) and only spending a point on a tier-0 or
    tier-1 one is not, until some tier-2 follower is playable this turn or on the field: the branch then
    compares spending on a poor target with keeping the point for a good one, as the player does, not
    evolving with not evolving."""
    from svsim.core.actions import Evolve
    from svsim.learn.payoff import tier
    p = state.players[state.active]
    pp = p.max_pp + (1 if p.bonus_ready else 0)
    target = keep["target"]
    selective = keep.get("mode", "all") == "selective"
    if selective:
        wanted, target = (lambda d: tier(d) == 2), "tier2"
    else:
        wanted = (lambda d: tier(d) == 2) if target == "tier2" else (lambda d: d.card_id == target)
    on_field = (lambda f: wanted(f.defn) and not f.super_evolved) if selective else (lambda f: wanted(f.defn))
    reached = target is not None and (any(wanted(c.defn) and c.cost <= pp for c in p.hand) or
                                      any(on_field(f) for f in (p.followers if selective else p.field)))
    limit = 2 if keep["trigger"] == "unlock" else 3
    if reached or keep["held"] >= limit or keep["held"] < 0:
        keep["held"] = -1                          # done: the search plays on as usual
        search.veto = own_veto
        return
    keep["held"] += 1
    record.setdefault("holds", []).append({"i": len(record["actions"]), "player": state.active,
                                           "turn": state.turn, "hold": "poor" if selective else "noevo",
                                           "branch": True})
    if selective:
        def extra(s, a):
            if not isinstance(a, Evolve):
                return False
            f = next((f for f in s.players[s.active].field if f.uid == a.uid), None)
            return f is None or tier(f.defn) < 2
    else:
        extra = lambda s, a: isinstance(a, Evolve)
    search.veto = extra if own_veto is None else (lambda s, a: own_veto(s, a) or extra(s, a))


EARLY_HOLD = 0.4        # the chance in the first turns after unlocking (the bot spends at once; the player not)
LATER_HOLD = 0.5        # ... when a card that pays off an evolution is in hand but out of reach this turn


def _hold(state, search, own_veto, held, rate, rng, record) -> None:
    """Exploration of keeping evolution points: at the start of a turn in which the player could evolve,
    the search may not evolve (or, half the time if it could super-evolve, not super-evolve) for the rest
    of the turn, with probability `rate`, at least EARLY_HOLD within two turns of the unlock, at least
    LATER_HOLD with a payoff card (learn.payoff) in hand out of reach; record["holds"] lists them. Any
    position, ahead or behind, so the evaluation sees what points held later are worth in each."""
    from svsim.core.actions import Evolve
    from svsim.core.engine import EVOLVE_TURN, SUPER_EVOLVE_TURN
    key = (state.active, state.turn)
    if key not in held:
        p = state.players[state.active]
        first = state.first == state.active
        can_evolve = p.ep > 0 and p.turns_taken >= EVOLVE_TURN[first]
        can_super = p.sep > 0 and p.turns_taken >= SUPER_EVOLVE_TURN[first]
        choice = None
        if can_evolve or can_super:
            from svsim.learn.features import context
            ctx = context(state, state.active, False, super_=can_super and not can_evolve)
            if ctx[0] <= 2 / 5.0:
                rate = max(rate, EARLY_HOLD)
            if ctx[5] > 0 or ctx[6] > 0:              # a payoff follower in hand out of reach
                rate = max(rate, LATER_HOLD)
        if (can_evolve or can_super) and rng.random() < rate:
            choice = "nosuper" if can_super and (not can_evolve or rng.random() < 0.5) else "noevo"
            record.setdefault("holds", []).append({"i": len(record["actions"]), "player": state.active,
                                                   "turn": state.turn, "hold": choice})
        held[key] = choice
        if choice is None:
            search.veto = own_veto
        else:
            extra = (lambda s, a: isinstance(a, Evolve) and a.super_) if choice == "nosuper" else \
                (lambda s, a: isinstance(a, Evolve))
            search.veto = extra if own_veto is None else (lambda s, a: own_veto(s, a) or extra(s, a))


def _planner(agent):
    """The cross-turn planner inside an agent (agents.crossturn_agent), if there is one."""
    inner = agent
    for _ in range(5):
        if hasattr(inner, "last_plan"):
            return inner
        inner = getattr(inner, "base", None)
        if inner is None:
            return None
    return None


def _plan(state, i: int, plan: dict, names: list) -> dict:
    """A turn start's measurements by the cross-turn planner, with the position's context: the
    value of each candidate (the search's line, keep a card, keep the bonus play point, don't evolve)
    on each determinization, in record["plans"] (the position itself is record["actions"][:i]
    replayed). keep:<card id> minus line is the card's keep value (agents.crossturn_agent.keep_value)."""
    me = state.active
    p, o = state.players[me], state.players[1 - me]
    side = lambda cards: [[c.defn.card_id, c.atk, c.life, 2 if c.super_evolved else 1 if c.evolved else 0]
                          for c in cards if c.defn.is_follower]
    return {"i": i, "player": me, "turn": state.turn, "own_turn": p.turns_taken,
            "pp": p.max_pp, "next_pp": min(p.max_pp + 1, 10), "bonus": p.bonus_ready, "ep": p.ep, "sep": p.sep,
            "hand": [c.defn.card_id for c in p.hand], "board": side(p.field), "opp_board": side(o.field),
            "hp": p.leader_hp, "opp_hp": o.leader_hp, "opp_hand": len(o.hand), "deck": names[me],
            "opp_deck": names[1 - me], "line": plan["line"], "chosen": plan["chosen"],
            "next_turn": plan["next_turn"], "static": plan.get("static", False), "research": plan.get("research", 0),
            "samples": {r: [round(v, 5) for v in vs] for r, vs in plan["samples"].items()}}


def _search(agent):
    """The ISMCTS inside an agent, if there is one."""
    inner = agent
    for _ in range(5):
        if hasattr(inner, "search") and hasattr(inner.search, "last_root"):
            return inner.search
        inner = getattr(inner, "base", None)
        if inner is None:
            return None
    return None


def _thought(state, legal, search):
    if search is None or search.last_root is None or not search.last_root.children:
        return None
    from svsim.search.mcts import _locator, action_key
    where = _locator(state, state.active)
    root = search.last_root
    visits = []
    for a in legal:
        child = root.children.get(action_key(state, a, where))
        visits.append(child.visits if child is not None else 0)
    best = max(root.children.values(), key=lambda c: c.visits)
    return {"visits": visits, "value": round(search.estimate(best), 5), "center": round(search.center, 4)}


def search_value(thought: dict | None, gain: float = 1.0) -> float | None:
    """The search's win probability for the player to act, from a decision's record["search"] entry:
    ISMCTS squashes (score - center) / 8 with score = 8 * gain * logit (models.SCALE), so the best
    line's logit is logit(value) / gain + center / (8 * gain)."""
    import math
    if not thought:
        return None
    v = min(max(thought["value"], 1e-6), 1 - 1e-6)
    z = math.log(v / (1 - v)) / gain + thought["center"] / (8.0 * gain)
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))


def rows(record: dict, with_search: bool = False, start: int = 0):
    """(phase, player, state, result) for every position the search may score (see module docstring);
    result is 1 for a win of `player`, 0 for a loss, 0.5 for a draw. The state is a copy. With
    `with_search`, a fifth item: the search's win probability at that decision (search_value), None
    for turn ends and decisions the search didn't make."""
    from svsim.core.actions import EndTurn
    from svsim.core.enums import Phase
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools import records as R
    winner = record["winner"]
    result = lambda p: 1.0 if winner == p else 0.0 if winner in (0, 1) else 0.5
    thoughts = record.get("search") or []
    gain = record.get("gain", 1.0)
    for i, (state, action) in enumerate(R.steps(record)):
        if state.phase != Phase.MAIN or i < start:       # `start`: from that action on (a branch's own part)
            continue
        me = state.active
        q = search_value(thoughts[i] if i < len(thoughts) else None, gain)
        yield (ACT, me, state.clone(), result(me)) + ((q,) if with_search else ())
        if isinstance(action, EndTurn):
            ended = after_end_of_turn(state)
            if not ended.over:
                yield (ENDED, me, ended, result(me)) + ((None,) if with_search else ())


def main() -> None:
    from svsim.ui.session import DECKS
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=2000)
    parser.add_argument("--deck", default="ramp", choices=sorted(DECKS))
    parser.add_argument("--opponent", default="ramp", choices=sorted(DECKS))
    parser.add_argument("--agent", default="mcts:100+plan+learned")
    parser.add_argument("--explore", type=float, default=0.03, help="chance of a random move at each decision")
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fork", action="store_true",
                        help="each game also as a branch keeping evolution points from its first fork point "
                             "(see play); both records are written")
    parser.add_argument("--fork-triggers", nargs="+", default=None, choices=("payoff", "deck", "unlock"),
                        help="with --fork: only these fork points (default all)")
    parser.add_argument("--fork-hold", default="all", choices=("all", "selective"),
                        help="with --fork: the branch keeps all its points (all), or only keeps them from tier-0 "
                             "and tier-1 targets (selective; see _keep)")
    parser.add_argument("--hold", type=float, default=0.0,
                        help="chance, at the start of a turn the player could evolve in, of not evolving (or not "
                             "super-evolving) for the rest of it (record['holds'])")
    args = parser.parse_args()
    done = set()
    if os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            done.add(json.loads(line)["g"])
    todo = [(g, args.seed, args.deck, args.opponent, args.agent, args.explore, args.hold, args.fork,
             args.fork_triggers, args.fork_hold) for g in range(args.games) if g not in done]
    t0 = time.time()
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for k, result in enumerate(pool.imap_unordered(play, todo), 1):
            for record in (result if isinstance(result, list) else [result]):
                fh.write(json.dumps(record) + "\n")
            fh.flush()
            if k % 100 == 0:
                print(f"{len(done) + k} games, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
