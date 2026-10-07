"""Is the planner's keep value (the teacher) right about what Salem kept? Against the one-turn search's Q.

    cd <svsim checkout at f5441df or later> && PYTHONPATH=. python3 <this> POSITIONS_JSON \
        [--probes CROSS_TURN_JSON] [--seeds 2] [--samples 8] [--workers 4] [--out rows.json]

At the start of each of Salem's turns (Salem's 10 Ramp mirror games), the
planner of svsim.agents.crossturn_agent (base search mcts-raw:100+learned+
phased, next_turn=True: through the opponent's turn and the own next turn by
the policy head, ENDED model) searches, reads its principal line and measures
each restriction against the line on the same determinizations:
  keep:<card>  keep a card the line plays           (Salem kept it: "kept")
  save         keep the bonus play point it presses (Salem's bonus PP still there after the turn)
  noevo        don't evolve                         (Salem didn't evolve this turn)
Teacher's value: mean over determinizations of (restriction - line), a win
probability difference; z = mean / its paired standard error.
Control (the same search tree, no look past the turn): the best value of a
line in the tree that obeys the restriction minus the best of one that breaks
it (the search's own estimates; lines run through every visited node to a leaf).

Agreement: a measurement agrees with Salem when its sign is Salem's choice
(above 0 where Salem kept, below 0 where Salem used). Reported for the teacher,
the teacher counting only |z| > 1, and the control, on the same items.
"""
import argparse
import json
import math
from collections import defaultdict
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import EndTurn, Evolve, PlayCard, UseBonusPP, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

GAMES = {}


def salem_turns(gid):
    rec = GAMES[gid]
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    i, out = 0, []
    while i < len(acts) and not st.over:
        if st.active != 0 or type(acts[i]).__name__ == "Mulligan":
            apply(st, acts[i])
            i += 1
            continue
        start, turn = i, []
        while i < len(acts) and st.active == 0 and not st.over:
            turn.append((st.clone(), acts[i]))
            apply(st, acts[i])
            i += 1
        out.append((start, turn, st.clone()))
    return out


def salem_choice(turn, after):
    """What Salem did with each kind of resource this turn."""
    used = set()
    for s, a in turn:
        mine = {c.uid: c.defn.card_id for c in s.players[0].hand}
        uids = ([a.uid] if isinstance(a, PlayCard) else []) + list(getattr(a, "targets", ()))
        used |= {mine[u] for u in uids if u in mine}
    won = after.over and after.winner == 0
    return {"used": used, "evolved": any(isinstance(a, Evolve) for _, a in turn),
            "bonus_kept": (not won) and after.players[0].bonus_ready,
            "had_bonus": turn[0][0].players[0].bonus_ready}


def label(restriction, choice):
    if restriction == "save":
        return "kept" if choice["bonus_kept"] else "used"
    if restriction == "noevo":
        return "used" if choice["evolved"] else "kept"
    cid = int(restriction.split(":")[1])
    return "used" if cid in choice["used"] else "kept"


def breaks(restriction, key):
    """Whether an action key (search.mcts.action_key) breaks the restriction."""
    if restriction == "save":
        return key == ("B",)
    if restriction == "noevo":
        return key[0] == "E"
    cid = int(restriction.split(":")[1])
    if key[0] == "P" and key[1][0] == "H" and key[1][1] and key[1][2] == cid:
        return True
    return False


def control(search, root, restriction):
    """Best line obeying the restriction minus best line breaking it, in the search's tree."""
    best = {True: float("-inf"), False: float("-inf")}

    def walk(node, broke):
        if not node.children:
            best[broke] = max(best[broke], search.estimate(node))
            return
        for key, child in node.children.items():
            if child.visits:
                walk(child, broke or breaks(restriction, key))
    walk(root, False)
    if best[True] == float("-inf") or best[False] == float("-inf"):
        return None
    return best[False] - best[True]


def measure(job):
    gid, at, seed, samples = job
    from svsim.agents.crossturn_agent import NONE, CrossTurnAgent, principal_line, restrictions
    from svsim.tools.arena import make_agent
    rec = GAMES[gid]
    st = records.start(rec)
    for a in rec["actions"][:at]:
        apply(st, from_dict(a))
    agent = CrossTurnAgent(make_agent("mcts-raw:100+learned+phased", seed), samples=samples,
                           seed=seed, next_turn=True)
    agent.search.choose(st)
    root = agent.search.last_root
    line = principal_line(root)
    cands = restrictions(line)
    out = agent.outcomes(st, line, cands)
    res = {}
    for r in cands:
        if r == NONE:
            continue
        diffs = [a - b for a, b in zip(out[r], out[NONE])]
        n = len(diffs)
        mean = sum(diffs) / n
        se = math.sqrt(sum((d - mean) ** 2 for d in diffs) / max(n - 1, 1) / n)
        res[r] = {"teacher": mean, "se": se, "control": control(agent.search, root, r)}
    return gid, at, seed, res


def agree(v, lab):
    return 1.0 if (v > 0) == (lab == "kept") and v != 0 else 0.5 if v == 0 else 0.0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("positions")
    p.add_argument("--probes", default=None)
    p.add_argument("--seeds", type=int, default=2)
    p.add_argument("--samples", type=int, default=8)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--out", default=None)
    args = p.parse_args()
    GAMES.update(json.load(open(args.positions, encoding="utf-8"))["records"])
    choices, jobs = {}, []
    for gid in sorted(GAMES):
        for at, turn, after in salem_turns(gid):
            choices[(gid, at)] = (turn[0][0].players[0].turns_taken, salem_choice(turn, after))
            jobs += [(gid, at, 700 + k, args.samples) for k in range(args.seeds)]
    rows = []
    with Pool(args.workers, initializer=GAMES.update, initargs=(GAMES,)) as pool:
        for gid, at, seed, res in pool.imap_unordered(measure, jobs):
            own, choice = choices[(gid, at)]
            for r, v in res.items():
                rows.append({"game": gid, "at": at, "own_turn": own, "seed": seed, "restriction": r,
                             "salem": label(r, choice), **v})
    probe = set()
    if args.probes:
        probe = {(q["game"], q["at"]) for q in json.load(open(args.probes, encoding="utf-8"))["positions"]
                 if q["confidence"] in ("高", "中")}
    groups = [("全部回合", rows)]
    if probe:
        groups.append(("探针集（验收用的 20 个）的回合", [r for r in rows if (r["game"], r["at"]) in probe]))
    kinds = lambda r: "save" if r["restriction"] == "save" else "noevo" if r["restriction"] == "noevo" else "keep"
    print("老师：svsim.agents.crossturn_agent 的推演（mcts-raw:100+learned+phased 的主线，"
          f"{args.samples} 个确定化，推演到我方下回合）；对照：同一棵一回合搜索树的 Q 差")
    for title, rs in groups:
        print(f"\n{title}：{len(rs)} 次测量（{len({(r['game'], r['at']) for r in rs})} 个回合 × {args.seeds} 个种子）")
        by = defaultdict(list)
        for r in rs:
            by[kinds(r)].append(r)
            by["all"].append(r)
        print(f"{'限制':<7}{'次数':>6}{'Salem 留':>9}{'老师一致':>10}{'老师|z|>1':>11}{'(次)':>6}{'对照一致':>10}{'(次)':>6}")
        for k in ("keep", "save", "noevo", "all"):
            g = by.get(k, [])
            if not g:
                continue
            t = sum(agree(r["teacher"], r["salem"]) for r in g) / len(g)
            sig = [r for r in g if r["se"] > 0 and abs(r["teacher"]) > r["se"]]
            ts = sum(agree(r["teacher"], r["salem"]) for r in sig) / len(sig) if sig else float("nan")
            cg = [r for r in g if r["control"] is not None]
            c = sum(agree(r["control"], r["salem"]) for r in cg) / len(cg) if cg else float("nan")
            kept = sum(r["salem"] == "kept" for r in g)
            print(f"{k:<7}{len(g):>6}{kept:>9}{t:>10.0%}{ts:>11.0%}{len(sig):>6}{c:>10.0%}{len(cg):>6}")
    if args.out:
        json.dump(rows, open(args.out, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
