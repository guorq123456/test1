"""Build regression positions from Salem's ramp-dragon mirror games.

Each position is the start of one of Salem's turns (seat 0). The check is a
predicate on the whole turn an agent plays from there (see check.py). These
are tests of whether a bot reproduces a choice a strong player made in that
spot; they are not rules for the bot.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> GAME_JSON... > positions.json
"""
import json
import sys

from svsim.cards import library, decks  # noqa: F401  (registers card scripts)
from svsim.core.actions import from_dict
from svsim.core.engine import apply
from svsim.core.state import leader_uid
from svsim.tools import records

ERNTZ, BURNITE = "约束的《正义》·伊兰翠", "焦灰的安纳提玛·班德奈特"
RED = "赤流"
RAMPS = {"龙之启示", "金银绚烂·璐米欧儿&雅尔贞特"}


def name(c):
    return c.defn.name_zh or c.defn.name


def big(c):
    return c.atk >= 5 or c.life >= 6


def board(p):
    return [f"{name(c)} {c.atk}/{c.life}" for c in p.followers]


def turns(rec):
    """Yield (start index, state at the start, actions of the turn) for seat 0's turns."""
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    i = 0
    while i < len(acts) and type(acts[i]).__name__ == "Mulligan":
        apply(st, acts[i])
        i += 1
    while i < len(acts) and not st.over:
        if st.active != 0:
            apply(st, acts[i])
            i += 1
            continue
        start, snap = i, st.clone()
        turn = []
        while i < len(acts) and st.active == 0 and not st.over:
            turn.append((acts[i], st.clone()))
            apply(st, acts[i])
            i += 1
        yield start, snap, turn, st


def main(paths):
    out, recs = [], {}
    for path in paths:
        rec = json.load(open(path))["record"]
        if rec["names"] != ["ramp", "ramp"]:
            continue
        gid = path.split("/")[-1][:13]
        for start, snap, turn, after in turns(rec):
            p, o = snap.players
            ctx = {"own_turn": p.turns_taken, "pp": f"{p.pp}/{p.max_pp}", "hp": p.leader_hp,
                   "opp_hp": o.leader_hp, "hand": [name(c) for c in p.hand], "board": board(p),
                   "opp_board": board(o), "opp_hand": len(o.hand), "ep": p.ep, "sep": p.sep,
                   "bonus": p.bonus_ready}
            salem = []
            discards, reds, se, played = [], [], [], []
            for a, s in turn:
                k = type(a).__name__
                if k == "PlayCard":
                    c = s.in_hand(0, a.uid)
                    played.append(name(c))
                    hand_t = [name(x) for x in s.players[0].hand if x.uid in a.targets]
                    tgt = [s.on_field(t) for t in a.targets if s.on_field(t)]
                    discards += hand_t
                    if name(c) == RED and tgt:
                        reds.append(tgt[0])
                    salem.append(f"play {name(c)}" + (f" discard {hand_t}" if hand_t else "")
                                 + (f" -> {[name(t) for t in tgt]}" if tgt else ""))
                elif k == "Evolve":
                    c = s.on_field(a.uid)
                    if a.super_:
                        se.append(name(c))
                    salem.append(("super-evolve " if a.super_ else "evolve ") + name(c))
                elif k == "Attack":
                    c = s.on_field(a.attacker)
                    t = "leader" if a.target == leader_uid(1) else name(s.on_field(a.target))
                    salem.append(f"{name(c)} attacks {t}")
                elif k == "UseBonusPP":
                    salem.append("bonus PP")
                elif k == "EndTurn":
                    salem.append("end turn")
            base = {"game": gid, "at": start, "context": ctx, "salem_turn": salem}

            def add(category, check, why):
                out.append({"id": f"{gid}-t{p.turns_taken}-{category}", "category": category,
                            "check": check, "why": why, **base})

            if after.over and after.winner == 0:
                add("lethal", {"win_this_turn": True},
                    "Salem won on this turn (attacks, effects, or end-of-turn damage).")
            for card in (ERNTZ, BURNITE):
                if card in se:
                    other = BURNITE if card == ERNTZ else ERNTZ
                    add("super_evolve", {"super_evolves": card},
                        f"Salem super-evolved {card} here; opponent board {ctx['opp_board']}, "
                        f"{other} {'also' if other in ctx['hand'] else 'not'} in hand.")
            held = {ERNTZ, BURNITE} & set(ctx["hand"])
            if discards and held and not (held & set(discards)):
                add("discard", {"never_discards": sorted(held)},
                    f"Salem discarded {discards} and kept {sorted(held)}.")
            if reds:
                add("answer_threat", {"removes_biggest": True},
                    f"Salem's Spilling Red hit {[f'{name(t)} {t.atk}/{t.life}' for t in reds]}: "
                    "the biggest enemy follower goes this turn (by any means), and no Red is spent on a smaller one.")
            elif RED in ctx["hand"] and o.followers and not any(big(c) for c in o.followers):
                add("red_hold", {"no_red_on_small": True},
                    f"Salem held Spilling Red against only small followers {ctx['opp_board']}.")
            if ERNTZ in played and ERNTZ not in se and not any(x == f"evolve {ERNTZ}" for x in salem) \
                    and p.leader_hp <= 10 and (p.ep or p.sep):
                add("erntz_unevolved", {"plays_unevolved": ERNTZ},
                    f"At {p.leader_hp} hp Salem played {ERNTZ} unevolved (heal 8) with evolution points left.")
            if ctx["bonus"] and p.turns_taken == 1 and "bonus PP" not in salem:
                add("bonus_keep", {"keeps_bonus": True},
                    "Second player, own turn 1: Salem kept the bonus PP for a turn-2 ramp card.")
            if ctx["bonus"] and p.turns_taken == 2 and "bonus PP" in salem and RAMPS & set(played):
                add("bonus_ramp", {"bonus_then_ramp": sorted(RAMPS)},
                    "Second player, own turn 2: Salem spent the bonus PP on a 3-cost ramp card.")
        recs[gid] = rec
    json.dump({"source": "Salem's ramp-dragon mirror games against the web bot (mcts:200+plan+learned)",
               "records": {g: r for g, r in recs.items() if any(o_["game"] == g for o_ in out)},
               "positions": out}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
