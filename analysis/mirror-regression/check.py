"""Run an agent on the regression positions and report which checks it passes.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> positions.json AGENT [SEEDS] [--only CATEGORY] [--ids ID,ID]

AGENT is an arena spec (e.g. "mcts:200+plan+learned"), or "salem" to replay
Salem's own turn (every check should pass: this validates the checks). The
agent plays seat 0 from the start of the turn until the turn ends; the check
is a predicate on that whole turn. Set SVSIM_WEIGHTS to choose the learned
models (as the arena does).
"""
import json
import sys
from collections import defaultdict

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

RED = "赤流"
RECORDS = {}
RAMPS = {"龙之启示", "金银绚烂·璐米欧儿&雅尔贞特"}


def name(c):
    return c.defn.name_zh or c.defn.name


def start_state(pos):
    rec = RECORDS[pos["game"]]
    st = records.start(rec)
    for a in rec["actions"][:pos["at"]]:
        apply(st, from_dict(a))
    assert st.active == 0 and not st.over
    return st


def play_turn(pos, spec, seed):
    """The turn as a list of (kind, details), the state after it, and whether the
    biggest enemy follower at the start of the turn is gone at its end."""
    st = start_state(pos)
    if spec == "salem":
        acts = [from_dict(a) for a in RECORDS[pos["game"]]["actions"][pos["at"]:]]
        nxt = iter(acts)
        agent = None
    else:
        from svsim.tools.arena import make_agent
        agent = make_agent(spec, seed)
    biggest_uid = max(st.players[1].followers, key=lambda f: f.atk + f.life, default=None)
    biggest_uid = biggest_uid.uid if biggest_uid else None
    turn = []
    while st.active == 0 and not st.over:
        legal = legal_actions(st)
        a = next(nxt) if agent is None else agent.act(st, legal)
        k = type(a).__name__
        if k == "PlayCard":
            c = st.in_hand(0, a.uid)
            hand_t = [name(x) for x in st.players[0].hand if x.uid in a.targets]
            enemies = st.players[1].followers
            tgt = [st.on_field(t) for t in a.targets if st.on_field(t) and st.on_field(t).owner == 1]
            biggest = max((f.atk + f.life for f in enemies), default=0)
            turn.append(("play", dict(card=name(c), discards=hand_t,
                                      targets=[(name(t), t.atk, t.life) for t in tgt],
                                      target_is_biggest=all(t.atk + t.life == biggest for t in tgt))))
        elif k == "Evolve":
            turn.append(("se" if a.super_ else "evo", dict(card=name(st.on_field(a.uid)))))
        elif k == "UseBonusPP":
            turn.append(("bonus", {}))
        apply(st, a)
    gone = biggest_uid is not None and all(f.uid != biggest_uid for f in st.players[1].field)
    return turn, st, gone


def big(t):
    return t[1] >= 5 or t[2] >= 6


def passes(check, turn, after, biggest_gone=False):
    plays = [d for k, d in turn if k == "play"]
    reds = [d for d in plays if d["card"] == RED]
    won = after.over and after.winner == 0
    if check.get("win_this_turn") or (won and not ({"keeps_bonus", "bonus_then_ramp"} & set(check))):
        return won      # winning the turn answers every other question
    if "super_evolves" in check:
        return any(k == "se" and d["card"] == check["super_evolves"] for k, d in turn)
    if "never_discards" in check:
        return not any(x in check["never_discards"] for d in plays for x in d["discards"])
    if check.get("removes_biggest"):
        # the biggest enemy follower at the start of the turn is gone at its end (by any means),
        # and every Spilling Red that is cast goes at the biggest enemy follower at that moment
        return biggest_gone and all(d["target_is_biggest"] for d in reds)
    if check.get("no_red_on_small"):
        return not any(not big(t) for d in reds for t in d["targets"])
    if "plays_unevolved" in check:
        card = check["plays_unevolved"]
        return any(d["card"] == card for d in plays) and \
            not any(k in ("se", "evo") and d["card"] == card for k, d in turn)
    if check.get("keeps_bonus"):
        return not any(k == "bonus" for k, _ in turn)
    if "bonus_then_ramp" in check:
        return any(k == "bonus" for k, _ in turn) and any(d["card"] in RAMPS for d in plays)
    raise ValueError(check)


def main():
    flags_with_value = {"--only", "--ids"}
    args = [a for i, a in enumerate(sys.argv[1:], 1)
            if not a.startswith("--") and sys.argv[i - 1] not in flags_with_value]
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    ids = set(sys.argv[sys.argv.index("--ids") + 1].split(",")) if "--ids" in sys.argv else None
    path, spec = args[0], args[1]
    seeds = int(args[2]) if len(args) > 2 else 1
    data = json.load(open(path))
    RECORDS.update(data["records"])
    positions = data["positions"]
    by_cat = defaultdict(lambda: [0, 0])
    rows = []
    for pos in positions:
        if only and pos["category"] != only:
            continue
        if ids and pos["id"] not in ids:
            continue
        ok = 0
        for s in range(seeds if spec != "salem" else 1):
            turn, after, gone = play_turn(pos, spec, 1000 + s)
            ok += passes(pos["check"], turn, after, gone)
        n = seeds if spec != "salem" else 1
        by_cat[pos["category"]][0] += ok
        by_cat[pos["category"]][1] += n
        rows.append((pos["id"], ok, n))
        print(f"{pos['id']:<40} {ok}/{n}", flush=True)
    tot = [sum(v[0] for v in by_cat.values()), sum(v[1] for v in by_cat.values())]
    print("\nby category:")
    for c, (ok, n) in sorted(by_cat.items()):
        print(f"  {c:<16} {ok}/{n}")
    print(f"  {'total':<16} {tot[0]}/{tot[1]}")


if __name__ == "__main__":
    main()
