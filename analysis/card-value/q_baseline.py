"""Does a card's value to the one-turn search match what Salem kept? The control for conditional card values.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> POSITIONS_JSON [--agent SPEC] [--seeds 2] [--workers 4] \
        [--probes CROSS_TURN_JSON] [--out rows.json]

Labels (Salem): at the start of each of Salem's turns, the cards in hand that
could be played then (a legal PlayCard); a card is "used" if Salem played or
discarded a copy of it during the turn, else "kept". Copies count as one card.

Value (the one-turn search): the agent's ISMCTS searches the turn's first
decision; its tree holds lines through the rest of the turn. For a card c:
best value of a line that never plays or discards c, minus best value of a
line that does (lines run through every visited node to a leaf; values are the
search's own estimates). Positive: the search would rather keep c this turn.

Agreement: within a turn, over pairs (a card Salem kept, a card Salem used),
the share where the kept card has the higher value (ties count half): 50% is
chance. Also the share of cards whose value has the sign of Salem's choice
(covers turns where Salem kept every playable card, e.g. passing with Vorlalai
in hand). Reported over all turns and over the cross-turn probe set's turns.
A teacher's measure (a planner's keep value) can be scored by the same labels.
"""
import argparse
import json
from collections import defaultdict
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import PlayCard, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

GAMES = {}


def _init_games(games):
    """Pool initializer: fill this module's GAMES in each worker (under spawn, as on Windows, a bound
    GAMES.update would only update a pickled copy)."""
    GAMES.update(games)


def salem_turns(gid):
    """(index of the turn's first action, state then, Salem's actions of the turn) for seat 0."""
    rec = GAMES[gid]
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    i, out = 0, []
    while i < len(acts) and not st.over:
        if st.active != 0 or type(acts[i]).__name__ == "Mulligan":
            apply(st, acts[i])
            i += 1
            continue
        start, snap, turn = i, st.clone(), []
        while i < len(acts) and st.active == 0 and not st.over:
            turn.append((st.clone(), acts[i]))
            apply(st, acts[i])
            i += 1
        out.append((start, snap, turn))
    return out


def labels(snap, turn):
    """{card_id: "kept" | "used"} for the cards Salem could play at the turn's start."""
    hand = {c.uid: c.defn.card_id for c in snap.players[0].hand}
    playable = {hand[a.uid] for a in legal_actions(snap) if isinstance(a, PlayCard) and a.uid in hand}
    used = set()
    for s, a in turn:
        mine = {c.uid: c.defn.card_id for c in s.players[0].hand}
        for uid in [getattr(a, "uid", None)] * isinstance(a, PlayCard) + list(getattr(a, "targets", ())):
            if uid in mine:
                used.add(mine[uid])
    return {cid: ("used" if cid in used else "kept") for cid in playable}


def search_of(agent):
    inner = agent
    while not (hasattr(inner, "search") and hasattr(inner.search, "last_root")):
        inner = inner.base
    return inner.search


def lines(search, node, used=frozenset()):
    """(value, card ids played or discarded) for every line from `node` to a leaf of the tree."""
    if not node.children:
        yield search.estimate(node), used
        return
    for key, child in node.children.items():
        if child.visits == 0:
            continue
        # mcts.action_key: ("P", card, targets, modes), ("E", follower, super, targets, modes); a card in
        # one's own hand is ("H", True, card id, cost), so a target of that form is a discard
        more = set()
        if key[0] == "P" and key[1][0] == "H" and key[1][1]:
            more.add(key[1][2])
        targets = key[2] if key[0] == "P" else key[3] if key[0] == "E" else ()
        for t in targets:
            if isinstance(t, tuple) and t[:2] == ("H", True):
                more.add(t[2])
        yield from lines(search, child, used | more)


def values(job):
    gid, at, spec, seed = job
    from svsim.tools.arena import make_agent
    rec = GAMES[gid]
    st = records.start(rec)
    for a in rec["actions"][:at]:
        apply(st, from_dict(a))
    search = search_of(make_agent(spec, seed))
    search.choose(st)
    best_with, best_without = defaultdict(lambda: float("-inf")), defaultdict(lambda: float("-inf"))
    hand_ids = {c.defn.card_id for c in st.players[0].hand}
    for v, used in lines(search, search.last_root):
        for cid in hand_ids:
            if cid in used:
                best_with[cid] = max(best_with[cid], v)
            else:
                best_without[cid] = max(best_without[cid], v)
    out = {}
    for cid in hand_ids:
        w, wo = best_with[cid], best_without[cid]
        out[cid] = None if w == float("-inf") or wo == float("-inf") else wo - w
    return gid, at, seed, out


def agreement(rows, value_key="value"):
    """Share of (kept, used) pairs within a turn where the kept card scores higher (ties half)."""
    num = den = 0.0
    for r in rows:
        kept = [v for cid, (lab, v) in r[value_key].items() if lab == "kept" and v is not None]
        used = [v for cid, (lab, v) in r[value_key].items() if lab == "used" and v is not None]
        for k in kept:
            for u in used:
                den += 1
                num += 1.0 if k > u else 0.5 if k == u else 0.0
    return (num / den if den else float("nan")), int(den)


def sign_agreement(rows, value_key="value"):
    """Share of cards whose value has the sign of Salem's choice: above 0 for a card Salem kept, below
    0 for one Salem used (0 counts half). Covers turns where Salem kept or used everything."""
    num = den = 0.0
    for r in rows:
        for lab, v in r[value_key].values():
            if v is None:
                continue
            den += 1
            good = v > 0 if lab == "kept" else v < 0
            num += 1.0 if good else 0.5 if v == 0 else 0.0
    return (num / den if den else float("nan")), int(den)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("positions")
    p.add_argument("--agent", default="mcts:400+plan+learned+phased")
    p.add_argument("--seeds", type=int, default=2)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--probes", default=None, help="cross_turn.json: also report over its turns")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    GAMES.update(json.load(open(args.positions, encoding="utf-8"))["records"])
    turns, jobs = {}, []
    for gid in sorted(GAMES):
        for at, snap, turn in salem_turns(gid):
            lab = labels(snap, turn)
            if lab:
                turns[(gid, at)] = {"game": gid, "at": at, "own_turn": snap.players[0].turns_taken,
                                    "labels": lab, "runs": []}
                jobs += [(gid, at, args.agent, 500 + k) for k in range(args.seeds)]
    with Pool(args.workers, initializer=_init_games, initargs=(GAMES,)) as pool:
        for gid, at, seed, vals in pool.imap_unordered(values, jobs):
            turns[(gid, at)]["runs"].append(vals)
    rows = []
    for t in turns.values():
        mean = {}
        for cid, lab in t["labels"].items():
            vs = [r.get(cid) for r in t["runs"] if r.get(cid) is not None]
            mean[str(cid)] = (lab, sum(vs) / len(vs) if vs else None)
        rows.append({**{k: t[k] for k in ("game", "at", "own_turn")}, "value": mean})
    groups = [("全部回合", rows)]
    if args.probes:
        probe = {(p_["game"], p_["at"]) for p_ in json.load(open(args.probes, encoding="utf-8"))["positions"]}
        groups.append(("探针集的回合", [r for r in rows if (r["game"], r["at"]) in probe]))
    print(f"一回合搜索 {args.agent}，每个回合 {args.seeds} 次取平均")
    for title, sub in groups:
        share, pairs = agreement(sub)
        sign, cards = sign_agreement(sub)
        print(f"{title}：{len(sub)} 个回合；留下的牌比用掉的牌价值高 {share:.1%}（{pairs} 对，50% 为随机）；"
              f"价值的正负和 Salem 留 / 用一致 {sign:.1%}（{cards} 张）")
    if args.out:
        json.dump(rows, open(args.out, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
