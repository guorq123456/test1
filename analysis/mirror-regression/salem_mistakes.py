"""Salem's 27 games, every decision of his re-searched by v2s: regret against the bot's choice, and lethals missed.

    cd <svsim checkout> && PYTHONPATH=.:<test1>/analysis/mirror-regression python3 <this> \
        analysis/mirror-regression/salem_games.json --k 8 --workers 4 --out salem_mistakes.jsonl
    python3 <this> --report salem_mistakes.jsonl [--top15 OUT.md]

The architecture thread (2026-10-08 00:03Z): Salem did not mark mistakes in these games ("应该有部分失误和噪声，
可能需要你自己进行数据分析"), and the build session's B (imitating his games) wants them filtered. For every
decision of Salem's (seat 0; play, attack, evolve, end turn, any other choice; a turn with one legal move
is not a decision):
- v2s's own search (the ISMCTS of mcts:200+plan+learned+phased, which deals the opponent's unseen cards from
  their known 40 at every iteration) is run K times on the position with K seeds; each root move's value is
  turned back into a win chance (the search keeps sigmoid((score - centre) / scale); the evaluation's score
  is 8 x logit) and averaged over the runs. The best move is the one the runs visited most (the search's
  own choice; taking the highest average value would pick noise). Regret = Q(best) - Q(his move), in
  win-rate points (negative when his move averaged higher than the bot's choice).
- At the start of each of his turns, search.lethal's LethalSearch with 5000 nodes and no screen (as the
  smoke probe) looks for a sure lethal.
Flags: F1 (a hard mistake) on every decision of a turn that started with a sure lethal he did not take
(the side to act did not win that turn); F2 (a suspected mistake) on a decision with regret >= 15 points,
but only for decisions not about evolving. About evolving (never flagged; it is what B is to learn):
evolving or super-evolving a target, ending the turn with a point left while an evolution was legal and
none made, and playing a card he evolved later that turn.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

V2S = "mcts:200+plan+learned+phased"
F2_POINTS = 15.0


def to_win(q, centre, scale):
    q = min(max(q, 1e-9), 1 - 1e-9)
    score = centre + scale * math.log(q / (1 - q))
    return 1 / (1 + math.exp(-max(min(score / 8.0, 60.0), -60.0)))


def describe(s, a):
    from glossary import common
    from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard, UseBonusPP

    def nm(uid):
        if uid is not None and uid < 0:
            return "主战者" if -uid - 1 != s.active else "自己主战者"
        c = s.on_field(uid) or s.in_hand(s.active, uid)
        if c is None:
            for p in s.players:
                for x in p.field:
                    if x.uid == uid:
                        c = x
        return common(c.defn.name_zh or c.defn.name) if c is not None else str(uid)
    if isinstance(a, PlayCard):
        c = s.in_hand(s.active, a.uid)
        t = "，目标 " + "、".join(nm(x) for x in a.targets) if a.targets else ""
        return f"出 {common(c.defn.name_zh or c.defn.name) if c else a.uid}{t}"
    if isinstance(a, Attack):
        return f"{nm(a.attacker)} 攻击 {nm(a.target)}"
    if isinstance(a, Evolve):
        t = "，目标 " + "、".join(nm(x) for x in a.targets) if a.targets else ""
        return f"{'超进化' if a.super_ else '进化'} {nm(a.uid)}{t}"
    if isinstance(a, EndTurn):
        return "结束回合"
    if isinstance(a, UseBonusPP):
        return "用额外 PP"
    return type(a).__name__


def category(s, a, legal, later):
    """(category, about evolving?)"""
    from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
    if isinstance(a, Evolve):
        return ("超进化" if a.super_ else "进化"), True
    if isinstance(a, EndTurn):
        if any(isinstance(x, Evolve) for x in legal) and not s.players[s.active].evolved_this_turn:
            return "有点不进化而结束回合", True
        return "结束回合", False
    if isinstance(a, PlayCard):
        if any(isinstance(x, Evolve) and x.uid == a.uid for x in later):
            return "下牌并进化", True
        return "出牌", False
    if isinstance(a, Attack):
        return "攻击", False
    return type(a).__name__, False


def search_values(search, s, legal, k, seed):
    from svsim.search.mcts import _locator, action_key
    where = _locator(s, s.active)
    keys = {action_key(s, a, where): a for a in legal}
    acc, visits = defaultdict(list), Counter()
    for j in range(k):
        search.rng = random.Random(seed * 1000 + j)
        search._next = None
        search.choose(s.clone())
        root, centre = search.last_root, search.center
        for key, child in root.children.items():
            if key in keys and child.visits > 0:
                acc[key].append(to_win(search.estimate(child), centre, search.scale))
                visits[key] += child.visits
    return keys, {key: sum(v) / len(v) for key, v in acc.items()}, visits


def game_job(job):
    gid, rec, k = job
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.search.lethal import LethalSearch
    from svsim.search.mcts import _locator, action_key
    from svsim.tools import records
    from svsim.tools.arena import make_agent
    agent = make_agent(V2S, 7)
    inner = agent
    while not (hasattr(inner, "search") and hasattr(inner.search, "last_root")):
        inner = inner.base
    search = inner.search
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    rows, turn_rows, lethal_turn, turn_no = [], [], None, None
    for i, a in enumerate(acts):
        if st.over:
            break
        if st.phase == Phase.MAIN and st.active == 0:
            if turn_no != st.turn:                                   # a new turn of Salem's
                if turn_rows:
                    rows += turn_rows
                turn_rows, turn_no = [], st.turn
                lethal_turn = bool(LethalSearch(max_nodes=5000, seed=rec["seed"], screen=None).solve(st.clone()).sure)
                turn_start = i
            legal = legal_actions(st)
            if len(legal) > 1:
                later = []
                for b in acts[i + 1:]:
                    if type(b).__name__ == "EndTurn":
                        break
                    later.append(b)
                cat, evo = category(st, a, legal, later)
                keys, q, visits = search_values(search, st, legal, k, rec["seed"] + i)
                where = _locator(st, 0)
                his = action_key(st, a, where)
                best = max(visits, key=visits.get) if visits else None
                regret = 100 * (q[best] - q[his]) if best is not None and his in q else None
                turn_rows.append({
                    "game": gid, "global_turn": st.turn, "own_turn": st.players[0].turns_taken,
                    "action_index": i, "turn_start": turn_start, "category": cat, "about_evolving": evo,
                    "his": describe(st, a), "best": describe(st, keys[best]) if best is not None else None,
                    "same": best == his, "q_his": q.get(his), "q_best": q.get(best) if best is not None else None,
                    "regret": regret, "legal": len(legal), "visits_his": visits.get(his, 0),
                    "visits_best": visits.get(best, 0), "lethal_at_turn_start": lethal_turn,
                    "F2": (not evo) and regret is not None and regret >= F2_POINTS})
        apply(st, a)
    if turn_rows:
        rows += turn_rows
    # F1: a turn that started with a sure lethal Salem did not win in
    won_turn = None
    if rec.get("winner") == 0:
        won_turn = max((r["global_turn"] for r in rows), default=None)
    for r in rows:
        r["F1"] = bool(r["lethal_at_turn_start"]) and r["global_turn"] != won_turn
    return rows


def report(path, top15=None):
    from glossary import common  # noqa: F401
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    pct = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))] if xs else float("nan")
    reg = [r["regret"] for r in rows if r["regret"] is not None]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(rows)} 个决策（只有一个合法动作的不算），"
          f"{len({r['game'] for r in rows})} 局。遗憾 = Q(v2s 选的) − Q(他的)，胜率点。")
    print(f"  遗憾：中位 {statistics.median(reg):.1f}，p90 {pct(reg, 0.9):.1f}，平均 {sum(reg) / len(reg):.1f}；"
          f"和 v2s 选的一样 {sum(r['same'] for r in rows) / len(rows):.0%}")
    print(f"  F1（回合开始有必杀没杀）{sum(r['F1'] for r in rows)} 个决策，"
          f"{len({(r['game'], r['global_turn']) for r in rows if r['F1']})} 个回合；F2（非进化类遗憾 ≥ {F2_POINTS:.0f}）"
          f"{sum(r['F2'] for r in rows)} 个决策")
    print("\n  按动作类别：")
    for cat in sorted({r["category"] for r in rows}, key=lambda c: -sum(r["category"] == c for r in rows)):
        xs = [r["regret"] for r in rows if r["category"] == cat and r["regret"] is not None]
        if xs:
            evo = any(r["about_evolving"] for r in rows if r["category"] == cat)
            print(f"    {cat:<14}{'（进化类，只报不筛）' if evo else '':<12} {len(xs):>5} 个：中位 {statistics.median(xs):.1f}，"
                  f"p90 {pct(xs, 0.9):.1f}，≥15 的 {sum(x >= F2_POINTS for x in xs) / len(xs):.0%}")
    ev = [r["regret"] for r in rows if r["about_evolving"] and r["regret"] is not None]
    print(f"  进化类合计：{len(ev)} 个，中位 {statistics.median(ev):.1f}，p90 {pct(ev, 0.9):.1f}（只报不筛）")
    print("\n  每局 F1 / F2：")
    for g in sorted({r["game"] for r in rows}):
        sub = [r for r in rows if r["game"] == g]
        print(f"    {g}：{len(sub)} 个决策，F1 {len({r['global_turn'] for r in sub if r['F1']})} 回合，F2 {sum(r['F2'] for r in sub)}")
    if top15:
        games = sorted({r["game"] for r in rows})
        top = sorted((r for r in rows if r["F2"]), key=lambda r: -r["regret"])[:15]
        lines = ["# Salem 那 27 局里 bot 认为差得最多的 15 步（请确认）", "",
                 "条件：对手卡表已知（牌序、手牌未知）。每一步都在同一个局面上，用 v2s 搜 8 次取平均。",
                 "「差多少」是 bot 估的胜率差：它自己选的那步，减去你走的那步。只列非进化类的步骤，进化相关的不在这里。",
                 "bot 也会看错，所以这只是请你确认：哪些是真失误、哪些是 bot 没看懂。", ""]
        for n, r in enumerate(top, 1):
            lines.append(f"{n}. 第 {games.index(r['game']) + 1} 局（{r['game']}）你的第 {r['own_turn'] + 1} 回合："
                         f"你 {r['his']}；bot 想 {r['best']}；差 {r['regret']:.0f} 个胜率点。")
        open(top15, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main():
    if "--report" in sys.argv:
        args = sys.argv[sys.argv.index("--report") + 1:]
        top = args[args.index("--top15") + 1] if "--top15" in args else None
        report(args[0], top)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("games")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", nargs="*", default=None, help="game ids")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    recs = json.load(open(args.games, encoding="utf-8"))["records"]
    done = set()
    try:
        done = {json.loads(line)["game"] for line in open(args.out, encoding="utf-8") if line.strip()}
    except FileNotFoundError:
        pass
    jobs = [(g, r, args.k) for g, r in recs.items() if g not in done and (not args.only or g in args.only)]
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for rows in pool.imap_unordered(game_job, jobs, chunksize=1):
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"  {rows[0]['game'] if rows else '?'}：{len(rows)} 个决策", flush=True)


if __name__ == "__main__":
    main()
