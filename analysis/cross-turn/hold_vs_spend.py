"""Hold or spend, on Salem's own turns in the cell "an A card in hand, out of reach": played to the end.

    cd <svsim checkout> && PYTHONPATH=.:<test1>/analysis/cross-turn:<test1>/analysis/card-value:<test1>/analysis/mirror-regression \
        python3 <this> analysis/mirror-regression/salem_games.json analysis/mirror-regression/evolve_probes.json \
        [--k 16] [--workers 4] --out rows.jsonl
    python3 <this> --report rows.jsonl

Background (the architecture thread, 18:34Z): 1 号's second round of "selective hold" forks lost
8-11 points against their controls, in this very cell, so it is either that holding a point there
loses, or that the bot holds badly or can't cash in what it holds. On each of Salem's turns of the
cell (evolve_probes.json; the standard table's cell, Erntz's unevolved side left out), two branches
from the same determinization (Salem's seat: own deck order, the opponent's hand and deck from its
known 40 cards, the random numbers; the same 2 x k determinizations and agent seeds for both):
- branch 1, Salem's own turn: his actions replayed; if a replayed action is not legal on this
  determinization (a card he drew is not the card drawn here), v2s finishes the turn in his class
  (no evolution if he held);
- branch 2, the other class by the bot: v2s's search with evolving vetoed if Salem evolved, or made
  to evolve (ending the turn vetoed while an evolution is legal and none was made) if he held;
the constraints hold for that one turn only; then v2 against v2, free, to the end (if the bot
spends a kept point on a poor target the next turn, that is part of what is measured). Kept per
turn: the target branch 2 evolved (its tier by the standard table's grouping) and the A cards in
Salem's hand. Per turn: mean of (branch 1 - branch 2) over the determinizations, a
win-rate difference (positive: Salem's choice did better), and its 95% interval; over all turns the
mean ± 95% (turns resampled), and by Salem's choice (held / spent).
Condition: the opponent's 40-card list is known (order and hand not).

Two definitions of the cell (the architecture thread, 21:28Z): the old one reads "out of reach" along
the line Salem played (no tier-2 follower ever evolvable on his field that turn: the standard table's);
the new one, from now on, "no legal play this turn reaches it", as 1 号's forks compute it
(learn.netdata._fork_point / _reached): a follower is within reach if it is on the field not yet evolved
or in hand costing no more than the turn's play points (max PP, plus the extra PP if it is ready); the
tiers and their order stay (A reachable, else only B, else an A card in hand). Both labels are kept per
row; --cell old / new / both picks the turns to run (both: either). The continuation after the
constrained turn is v2 against v2 (--finish v2s for the re-check the thread asked for: the same turns,
the same determinizations and seeds). A turn's seed comes from its place among the old cell's turns
(950000 + n, as in the first run), or 950100 + n among the turns only the new cell has.
"""
import argparse
import json
import math
import os
import random
import sys
from collections import Counter
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import EndTurn, Evolve
from svsim.core.engine import apply, legal_actions

V2, V2S = "mcts:100+plan+learned+phased", "mcts:200+plan+learned+phased"
CELL = "2 档在手够不着"
GAMES, TURNS, INFO = {}, {}, {}
FINISH = {"spec": V2}


def vetoing(spec, seed, veto):
    from realized import agent_with_veto
    return agent_with_veto(spec, seed, veto)


def no_evolve(s, a):
    return isinstance(a, Evolve)


def must_evolve(s, a):
    if not isinstance(a, EndTurn):
        return False
    p = s.players[s.active]
    return not p.evolved_this_turn and any(isinstance(x, Evolve) for x in legal_actions(s))


def finish(st, me, sd):
    from svsim.tools.arena import make_agent
    agents = {me: make_agent(FINISH["spec"], sd + 3), 1 - me: make_agent(FINISH["spec"], sd + 1)}
    while not st.over:
        apply(st, agents[st.active].act(st, legal_actions(st)))
    return 1.0 if st.winner == me else 0.0 if st.winner == 1 - me else 0.5


def branch_salem(base, me, actions, held, sd):
    st = base.clone()
    diverged = False
    for a in actions:
        if st.over or st.active != me:
            break
        if a in legal_actions(st):
            apply(st, a)
        else:
            diverged = True
            break
    if diverged and not st.over and st.active == me:
        agent = vetoing(V2S, sd, no_evolve if held else None)
        while not st.over and st.active == me:
            apply(st, agent.act(st, legal_actions(st)))
    return (finish(st, me, sd) if not st.over else (1.0 if st.winner == me else 0.0)), diverged


def branch_other(base, me, held, sd):
    """The other class by v2s, for this one turn only; returns the result and what it evolved (name, tier) if any."""
    from evolve_hold_review import TIER
    st = base.clone()
    agent = vetoing(V2S, sd, must_evolve if held else no_evolve)
    evolved = None
    while not st.over and st.active == me:
        a = agent.act(st, legal_actions(st))
        if isinstance(a, Evolve):
            c = st.on_field(a.uid)
            evolved = (c.defn.name_zh or c.defn.name, TIER(c.defn), a.super_)
        apply(st, a)
    return (finish(st, me, sd) if not st.over else (1.0 if st.winner == me else 0.0)), evolved


def measure(job):
    from svsim.core.view import determinize
    key, k, seed, spec = job
    FINISH["spec"] = spec
    st0, actions, held = TURNS[key]
    me = st0.active
    diffs, div, other_evolved, targets = [], 0, 0, []
    for j in range(2 * k):
        base = determinize(st0, me, random.Random(seed * 1000 + j))
        sd = seed * 1000 + 10 * j
        r1, d = branch_salem(base, me, actions, held, sd)
        r2, ev = branch_other(base, me, held, sd)
        diffs.append(r1 - r2)
        div += d
        other_evolved += ev is not None
        targets.append(ev)
    return {"key": key, "held": held, "diffs": diffs, "diverged": div, "other_evolved": other_evolved,
            "targets": targets, "seed": seed, "finish": spec, **INFO[key]}


def new_cell(turn):
    """The tier cell with "within reach" as 1 号's forks compute it: on the field not yet evolved, or in hand
    costing at most the turn's play points (max PP, plus the extra PP if ready)."""
    from evolve_hold_review import TIER
    s0 = turn[0][0]
    p = s0.players[s0.active]
    pp = p.max_pp + (1 if p.bonus_ready else 0)
    reach = max([TIER(f.defn) for f in p.followers if not f.evolved] +
                [TIER(c.defn) for c in p.hand if c.defn.is_follower and c.cost <= pp] + [0])
    hand = max([TIER(c.defn) for c in p.hand] + [0])
    if reach:
        return "够得着 2 档" if reach == 2 else "够得着 1 档"
    return "2 档在手够不着" if hand == 2 else "1 档在手够不着" if hand == 1 else "都没有"


def load_turns(games_path, probes_path, which="old"):
    from evolve_hold_review import TIER, standard_row
    from evolve_targets import salem_turns
    games = json.load(open(games_path, encoding="utf-8"))["records"]
    probes = json.load(open(probes_path, encoding="utf-8"))["positions"]
    out = {}
    for p in probes:
        if p["category"] not in ("evolve_hold", "evolve_use"):
            continue
        turns = dict(salem_turns(games[p["game"]]))
        turn = turns[p["at"]]
        row = standard_row(turn)
        if row is None or row.get("erntz_plain"):
            continue
        old, new = row["tier"] == CELL, new_cell(turn) == CELL
        if not {"old": old, "new": new, "both": old or new}[which]:
            continue
        key = f"{p['game']}@{p['at']}"
        out[key] = (turn[0][0], [a for _, a in turn], p["category"] == "evolve_hold", p)
        st0 = turn[0][0]
        evo = [("超进化 " if a.super_ else "进化 ") + (s.on_field(a.uid).defn.name_zh or "") for s, a in turn
               if isinstance(a, Evolve)]
        INFO[key] = {"own_turn": p["context"]["own_turn"], "first": p["context"]["first"],
                     "cell_old": row["tier"], "cell_new": new_cell(turn),
                     "salem_action": "、".join(evo) if evo else "不进化",
                     "a_in_hand": sorted({c.defn.name_zh for c in st0.players[0].hand if TIER(c.defn) == 2})}
    return out


LABEL = {"2 档在手够不着": "A 档在手、够不着", "够得着 2 档": "A 档够得着", "够得着 1 档": "最好只够得着 B 档",
         "1 档在手够不着": "B 档在手、够不着", "都没有": "都没有"}


def report(paths):
    """The rows of the v2 continuation as a table (both cell labels), then the three means under both
    definitions, for each continuation present (v2; v2s where re-checked)."""
    from glossary import common, label_first
    here = os.path.dirname(os.path.abspath(__file__))
    mr = os.path.join(here, "..", "mirror-regression")
    load_turns(os.path.join(mr, "salem_games.json"), os.path.join(mr, "evolve_probes.json"), "both")
    by_finish = {}
    for path in paths:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                r.update({k: INFO[r["key"]][k] for k in ("cell_old", "cell_new")})
                by_finish.setdefault(r.get("finish", V2), {})[r["key"]] = r
    rows = list(by_finish.get(V2, {}).values())
    def ci(xs):
        m = sum(xs) / len(xs)
        se = math.sqrt(sum((x - m) ** 2 for x in xs) / max(len(xs) - 1, 1) / len(xs))
        return m, 1.96 * se
    print("条件：对手卡表已知（牌序、手牌未知）。约束只管 Salem 做决定的那一回合，之后两边都由 v2 自由打到终局。")
    print("差 = Salem 的打法 − 另一类里 bot 的最好打法（正数：Salem 的选择打到终局更好），每行 32 次配对。\n")
    print("| 对局 | 回合 | 手里的 A 档 | Salem 的动作 | 另一类（bot）的动作 | 胜率差 ± 95% | 分支 1 走偏 | 新定义下的格 |")
    print("|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: r["key"]):
        m, h = ci(r["diffs"])
        n = len(r["diffs"])
        game = r["key"].split("@")[0]
        evs = [t for t in r["targets"] if t]
        if r["held"]:
            tiers = Counter(t[1] for t in evs)
            names = Counter(common(t[0]) for t in evs)
            other = (f"必须进化：{len(evs)}/{n} 次进化了，" + "、".join(f"{k}×{v}" for k, v in names.most_common(3))
                     + "（档位 " + "、".join(f"{k} 档 {v}" for k, v in sorted(tiers.items(), reverse=True)) + "）")
        else:
            other = "不进化"
        hand = "、".join(common(x) for x in r["a_in_hand"]) or "无"
        line = (f"| {game} | 第 {r['own_turn']} 回合（{'先' if r['first'] else '后'}手） | {hand} | "
                f"{'留' if r['held'] else '花'}：{rename_action(r['salem_action'], common)} | {other} | {m:+.3f} ± {h:.3f} | "
                f"{r['diverged']}/{n} | {LABEL[r['cell_new']]} |")
        print(label_first(line))
    for cell_key, title in (("cell_old", "旧定义（按 Salem 实际那条线）"), ("cell_new", "新定义（本回合任何合法出法都够不着）")):
        print(f"\n{title}：")
        for fin, name in ((V2, "v2 续打"), (V2S, "v2s 续打")):
            got = [r for r in by_finish.get(fin, {}).values() if r[cell_key] == CELL]
            if not got:
                continue
            rng = random.Random(19)
            for sub_title, sub in (("全部", got), ("Salem 留的", [r for r in got if r["held"]]),
                                   ("Salem 花的", [r for r in got if not r["held"]])):
                if not sub:
                    continue
                means = [sum(r["diffs"]) / len(r["diffs"]) for r in sub]
                m = sum(means) / len(means)
                bs = sorted(sum(means[rng.randrange(len(means))] for _ in means) / len(means) for _ in range(4000))
                print(f"  {name}，{sub_title}：{len(sub)} 个回合，平均 {m:+.3f}（95% {bs[100]:+.3f}～{bs[3899]:+.3f}，回合重抽）")


def rename_action(text, common):
    for word in ("超进化 ", "进化 "):
        if text.startswith(word):
            return word + common(text[len(word):])
    return text


def main():
    if "--report" in sys.argv:
        report([a for a in sys.argv[sys.argv.index("--report") + 1:] if not a.startswith("--")])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("games")
    ap.add_argument("probes")
    ap.add_argument("--k", type=int, default=16)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--cell", choices=("old", "new", "both"), default="old")
    ap.add_argument("--finish", choices=("v2", "v2s"), default="v2", help="the continuation to the end, both sides")
    ap.add_argument("--only", choices=("all", "held", "spent"), default="all")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    loaded = load_turns(args.games, args.probes, "both")
    old_keys = sorted(k for k in loaded if INFO[k]["cell_old"] == CELL)
    new_only = sorted(k for k in loaded if k not in old_keys)
    seed_of = {**{k: 950000 + n for n, k in enumerate(old_keys)}, **{k: 950100 + n for n, k in enumerate(new_only)}}
    pick = {"old": lambda k: INFO[k]["cell_old"] == CELL, "new": lambda k: INFO[k]["cell_new"] == CELL,
            "both": lambda k: True}[args.cell]
    held_ok = {"all": lambda h: True, "held": lambda h: h, "spent": lambda h: not h}[args.only]
    TURNS.update({k: v[:3] for k, v in loaded.items() if pick(k) and held_ok(v[2])})
    keys = sorted(TURNS)
    print(f"选中的回合：{len(keys)} 个（Salem 留 {sum(TURNS[k][2] for k in keys)}，花 {sum(not TURNS[k][2] for k in keys)}），"
          f"续打 {args.finish}", flush=True)
    done = set()
    if os.path.exists(args.out):
        done = {json.loads(line)["key"] for line in open(args.out, encoding="utf-8") if line.strip()}
    spec = V2 if args.finish == "v2" else V2S
    jobs = [(k, args.k, seed_of[k], spec) for k in keys if k not in done]
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for row in pool.imap_unordered(measure, jobs, chunksize=1):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(f"  {row['key']} 完成", flush=True)


if __name__ == "__main__":
    main()
