"""Turn-level policy iteration, step 0: the turn-level regret audit (README.md here; written before any of its games).

This part picks the turn starts; the candidates, T and G_end wait for the build line's candidate generator.

    cd <svsim checkout> && python -m svsim.learn.netdata --games 150 --deck ramp --opponent ramp \\
        --agent level-strong --explore 0 --seed 65900000 --out selfplay.jsonl
    cd <svsim checkout> && PYTHONPATH=.:<this folder>:<this folder>/../card-value python3 <this> starts \\
        selfplay.jsonl --out starts.jsonl

starts.jsonl, one line per turn start, numbered k:
  k 0-299    self-play: every own-turn start (the first main-phase decision of each turn, either seat) of the 150
             games, sorted by (g, action index, seat), shuffled by Random(65910000), the first 300;
  k 300-     Salem's turns (seat 0) in his 27 games: every turn start of his, less the turns he won the game in and
             the turns his record stops inside; the 10 games, then the 17, each by (game id, action index).
  {"k", "src": "selfplay" | "salem", "game": g (self-play) or the game id, "at": the action index, "seat",
   "own_turn": the mover's turns taken, "batch": 1 (the 10 games) | 2 (the 17) | null}

    ... plans selfplay.jsonl starts.jsonl --out plans.jsonl [--workers 12] [--only K,K,...]
    ... teacher selfplay.jsonl starts.jsonl plans.jsonl --out teacher.jsonl [--workers 12]
    ... pickgend starts.jsonl plans.jsonl --out gend_starts.jsonl
    ... gend selfplay.jsonl starts.jsonl plans.jsonl gend_starts.jsonl --out gend.jsonl [--k 16] [--workers 12]

plans: the build line's search.candidates.generate (ce6f95a) at each start, the bot level-strong (v2s), seed
65960000 + k; at Salem's starts his own turn as the "salem" kind. Each plan is kept as its actions on the real
position and as action keys (search.mcts.action_key: card ids and places, the same in every determinization).

A plan on a determinization (`replay`): its keys in order; the plan's end of turn ends the turn there; a key with
no legal match (or one the plan's restriction forbids) hands the rest of the turn to the plan kind's own policy, as
the generator would have gone on (`finisher`): the bot (v2s) for bot / second / third / salem, the bot under the
restriction for keep:<id> / save / noevo, the race planner for race ("end" can't fail). So on the prefix the
determinization shares with the real position the plan is replayed, and where it differs (a card drawn during the
turn, as a rule) the kind is regenerated from there. Where it failed is recorded: the replay failure rate is
reported by kind, with how much of the plan was played first. T and G_end use the same rule.

teacher: T of every plan, the n30 teacher's scoring (crossturn_agent.CrossTurnAgent(mcts-raw:100+learned+phased,
next_turn, next_search 30, samples 8), as teacher_eval.measure): the same 8 determinizations for every plan (the
agent's own rng, seed 65920000 + 2k + s), each plan's turn by `replay`, then the opponent's turn and the own next
turn as the teacher plays them, scored by the ENDED model. Not CrossTurnAgent.outcomes itself: its forbids() takes
restriction names only, and its own turn goes on with the policy head after a line's end of turn (a whole turn
ending early, "end" or Salem's, would be played on).

gend: G_end of every plan at the picked starts: determinization j of start m from Random(65930000 + 100 m + j),
each plan's turn by `replay` (a failure: the kind's policy, seed 10 x that), then the bot mcts:100+plan+learned+
phased to the end (seeds 10 x that + 3 for the mover, + 1 for the opponent), as the discrimination experiment's
G_end. In T a failure's policy has the seed 10 x (65920000 + 2k + s) + the determinization's index.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))

import salem_discrim as D        # noqa: E402  (Salem's games and turns, the discrimination experiment's)
import student_data as SD        # noqa: E402  (own_turn_starts, the student's positions')

BANK = 65900000
N_SELFPLAY = 300
SALEM_FILES = ("salem_games_10.json", "salem_games_17.json")
BOT = "v2s"                                  # level-strong, the bot whose turns are audited
TEACHER = "mcts-raw:100+learned+phased"      # the n30 teacher's base (teacher_eval.measure)
GEND_BOT = "mcts:100+plan+learned+phased"    # the discrimination experiment's G_end bot
N_GEND, N_GEND_SALEM = 150, 100
RESTRICTED = ("keep", "save", "noevo")       # the plan kinds that carry a restriction


def salem_games():
    out = []
    for batch, f in enumerate(SALEM_FILES, 1):
        recs = json.load(open(os.path.join(HERE, "..", "card-value", f), encoding="utf-8"))["records"]
        out.append((batch, recs))
    return out


def salem_turns():
    """(batch, game id, action index) of every Salem turn start, less his winning turns and the turns the record
    stops inside."""
    out = []
    for batch, recs in salem_games():
        for gid in sorted(recs):
            for at in D.salem_turn_starts(recs[gid]):
                if D.used_this_turn(recs[gid], at)[1] or not D.turn_complete(recs[gid], at):
                    continue
                out.append((batch, gid, at))
    return out


def starts(args):
    games = SD._lines(args.selfplay)
    allp = sorted((rec["g"], at, seat) for rec in games for at, seat in SD.own_turn_starts(rec))
    random.Random(BANK + 10000).shuffle(allp)
    by_g = {rec["g"]: rec for rec in games}
    rows = []
    for g, at, seat in allp[:N_SELFPLAY]:
        st = SD._state_at(by_g[g], at)
        rows.append({"src": "selfplay", "game": g, "at": at, "seat": seat,
                     "own_turn": st.players[seat].turns_taken, "batch": None})
    recs = {gid: r for _, rs in salem_games() for gid, r in rs.items()}
    for batch, gid, at in salem_turns():
        st = D.state_at(recs[gid], at)
        rows.append({"src": "salem", "game": gid, "at": at, "seat": st.active,
                     "own_turn": st.players[st.active].turns_taken, "batch": batch})
    with open(args.out, "w", encoding="utf-8") as fh:
        for k, r in enumerate(rows):
            fh.write(json.dumps({"k": k, **r}) + "\n")
    n_salem = sum(r["src"] == "salem" for r in rows)
    print(f"自对弈 {len(games)} 局，{len(allp)} 个自己回合的开头，取 {min(len(allp), N_SELFPLAY)} 个；"
          f"Salem {n_salem} 个回合（10 局 {sum(r['batch'] == 1 for r in rows)}，17 局 {sum(r['batch'] == 2 for r in rows)}）；"
          f"共 {len(rows)} 个开头")


# --- plans ---------------------------------------------------------------------------------------

def _norm(x):
    """A key with lists as tuples (JSON round trips turn tuples into lists)."""
    return tuple(_norm(v) for v in x) if isinstance(x, (list, tuple)) else x


def _key(s, a):
    from svsim.search.mcts import _locator, action_key
    return _norm(action_key(s, a, _locator(s, s.active)))


REC = {}                                     # (src, game) -> record, in each worker


def _set_bank(bank):
    global BANK
    BANK = bank


def _init(recs, bank):
    REC.update(recs)
    _set_bank(bank)


def _records(selfplay):
    out = {("selfplay", r["g"]): r for r in SD._lines(selfplay)}
    for _, rs in salem_games():
        out.update({("salem", gid): r for gid, r in rs.items()})
    return out


def _start_state(st_row):
    rec = REC[(st_row["src"], st_row["game"])]
    return SD._state_at(rec, st_row["at"]), rec


def _salem_turn(rec, at):
    """Salem's recorded turn from `at`: its actions, the end of turn included."""
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    st = SD._state_at(rec, at)
    me, out = st.active, []
    for a in rec["actions"][at:]:
        if st.over or st.active != me:
            break
        act = from_dict(a)
        out.append(act)
        apply(st, act)
    if out and not isinstance(out[-1], EndTurn) and not st.over:
        out.append(EndTurn())
    return out


def _plans_job(st_row):
    import time
    from svsim.core.actions import EndTurn, to_dict
    from svsim.core.engine import apply
    from svsim.search.candidates import generate
    state, rec = _start_state(st_row)
    salem = _salem_turn(rec, st_row["at"]) if st_row["src"] == "salem" else None
    t = time.process_time()
    cands = generate(state, spec=BOT, seed=BANK + 60000 + st_row["k"], salem=salem)
    cpu = time.process_time() - t
    plans = []
    for c in cands:
        s, keys = state.clone(), []
        for a in c.actions:
            keys.append(_key(s, a))
            if isinstance(a, EndTurn) or s.over:
                break
            apply(s, a)
        plans.append({"kind": c.kind, "merged": c.merged, "times": c.times, "keys": keys,
                      "actions": [to_dict(a) for a in c.actions]})
    return {"k": st_row["k"], "src": st_row["src"], "cpu": cpu, "plans": plans}


def plans(args):
    from multiprocessing import Pool
    rows = SD._lines(args.starts)
    if args.only:
        want = {int(x) for x in args.only.split(",")}
        rows = [r for r in rows if r["k"] in want]
    with Pool(args.workers, initializer=_init, initargs=(_records(args.selfplay), args.bank)) as pool, \
            open(args.out, "w", encoding="utf-8") as fh:
        for n, out in enumerate(pool.imap_unordered(_plans_job, rows), 1):
            fh.write(json.dumps(out) + "\n")
            fh.flush()
            if n % 25 == 0:
                print(f"{n}/{len(rows)}", flush=True)
    print(f"{len(rows)} 个开头的候选写进了 {args.out}")


# --- replaying a plan on a determinization ---------------------------------------------------------

def _veto(kind):
    from svsim.agents.crossturn_agent import forbids
    return forbids(kind) if kind.split(":")[0] in RESTRICTED else None


def finisher(kind, me, seed):
    """finish(s): the rest of `me`'s turn by the plan kind's own policy (as search.candidates.generate plays it)."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.search import candidates as C

    def decider():                                  # built only when a replay fails
        if kind == "race":
            from svsim.search.turnplan import TurnPlanAgent
            from svsim.tools.arena import make_agent
            base = C._search_of(make_agent(BOT, seed)).weights
            return TurnPlanAgent(max_nodes=300, samples=2, seed=seed, weights=C.ClockScore(base, nodes=200)).act
        if kind == "end":
            return lambda s, legal: EndTurn()
        return C._agent_decider(BOT, seed, _veto(kind))

    def finish(s):
        decide = decider()
        while not s.over and s.active == me:
            legal = legal_actions(s)
            a = decide(s, legal)
            if a not in legal:
                a = EndTurn()
            if isinstance(a, EndTurn):
                return                              # the caller ends the turn
            apply(s, a)
    return finish


def replay(s, me, keys, veto, finish) -> int | None:
    """Play a plan's keys on `s` (the mover `me`), stopping at its end of turn (the turn is left for the caller to
    end). A key with no legal match, or one `veto` forbids: finish(s) plays the rest of the turn, and the key's
    index is returned; None if the plan went through."""
    from svsim.core.engine import apply, legal_actions
    for i, key in enumerate(keys):
        if s.over or s.active != me:
            return None
        if key == ("T",):
            return None
        match = next((a for a in legal_actions(s) if _key(s, a) == key), None)
        if match is None or (veto is not None and veto(s, match)):
            finish(s)
            return i
        apply(s, match)
    if not s.over and s.active == me:                # a plan without its end of turn (not expected)
        finish(s)
        return len(keys)
    return None


# --- T ----------------------------------------------------------------------------------------------

PLANS = {}                                   # k -> plans row, in each worker


def _init_teacher(recs, plans_rows, bank):
    REC.update(recs)
    PLANS.update(plans_rows)
    _set_bank(bank)


def _teacher_job(job):
    import random
    import time
    from svsim.agents.crossturn_agent import CrossTurnAgent
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    st_row, s_idx = job
    k = st_row["k"]
    state, _ = _start_state(st_row)
    me = state.active
    seed = BANK + 20000 + 2 * k + s_idx
    t = time.process_time()
    agent = CrossTurnAgent(make_agent(TEACHER, seed), samples=8, seed=seed, next_turn=True, next_search=30)
    plans_k = PLANS[k]["plans"]
    seeds = [agent.rng.getrandbits(64) for _ in range(agent.samples)]
    values = {p["kind"]: [] for p in plans_k}
    failed = {p["kind"]: [] for p in plans_k}
    for j, sd in enumerate(seeds):
        base = determinize(state, me, random.Random(sd))
        for p in plans_k:
            s = base.clone()
            keys = [_norm(x) for x in p["keys"]]
            failed[p["kind"]].append(replay(s, me, keys, _veto(p["kind"]), finisher(p["kind"], me, 10 * seed + j)))
            agent._their_turn(s, me)
            values[p["kind"]].append(agent._value(s, me))
    return {"k": k, "s": s_idx, "seed": seed, "cpu": time.process_time() - t, "values": values, "failed": failed,
            "n_keys": {p["kind"]: len(p["keys"]) for p in plans_k}}


def teacher(args):
    from multiprocessing import Pool
    plans_rows = {r["k"]: r for r in SD._lines(args.plans)}
    rows = [r for r in SD._lines(args.starts) if r["k"] in plans_rows]
    jobs = [(r, s) for r in rows for s in (0, 1)]
    with Pool(args.workers, initializer=_init_teacher,
              initargs=(_records(args.selfplay), plans_rows, args.bank)) as pool, \
            open(args.out, "w", encoding="utf-8") as fh:
        for n, out in enumerate(pool.imap_unordered(_teacher_job, jobs), 1):
            fh.write(json.dumps(out) + "\n")
            fh.flush()
            if n % 50 == 0:
                print(f"{n}/{len(jobs)}", flush=True)
    print(f"{len(jobs)} 个（开头 × 种子）的老师 T 写进了 {args.out}")


# --- G_end ------------------------------------------------------------------------------------------

def pickgend(args):
    """The G_end starts: Salem's turns whose own plan doesn't merge with the bot's (a different turn end), at most
    100, then self-play starts up to 150; both shuffled by one Random(65950000), Salem's list first."""
    plans_rows = {r["k"]: r for r in SD._lines(args.plans)}
    rows = [r for r in SD._lines(args.starts) if r["k"] in plans_rows]

    def differs(k):
        kinds = {p["kind"]: p for p in plans_rows[k]["plans"]}
        return "salem" in kinds and "bot" in kinds
    salem = sorted(r["k"] for r in rows if r["src"] == "salem" and differs(r["k"]))
    selfp = sorted(r["k"] for r in rows if r["src"] == "selfplay")
    rng = random.Random(BANK + 50000)
    rng.shuffle(salem)
    rng.shuffle(selfp)
    pick = salem[:N_GEND_SALEM]
    pick += selfp[:N_GEND - len(pick)]
    with open(args.out, "w", encoding="utf-8") as fh:
        for m, k in enumerate(pick):
            fh.write(json.dumps({"m": m, "k": k}) + "\n")
    print(f"Salem 和 bot 打法不同的回合 {len(salem)} 个，取 {min(len(salem), N_GEND_SALEM)}；"
          f"自对弈补 {len(pick) - min(len(salem), N_GEND_SALEM)} 个；共 {len(pick)} 个 G_end 开头")


def _gend_job(job):
    import random
    import time
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    st_row, m, k_half = job
    state, _ = _start_state(st_row)
    me = state.active
    plans_k = PLANS[st_row["k"]]["plans"]
    out = {p["kind"]: [] for p in plans_k}
    failed = {p["kind"]: [] for p in plans_k}
    t = time.process_time()
    for j in range(2 * k_half):
        sd = BANK + 30000 + 100 * m + j
        base = determinize(state, me, random.Random(sd))
        for p in plans_k:
            s = base.clone()
            keys = [_norm(x) for x in p["keys"]]
            failed[p["kind"]].append(replay(s, me, keys, _veto(p["kind"]), finisher(p["kind"], me, 10 * sd)))
            if not s.over and s.active == me:
                apply(s, EndTurn())
            agents = {me: make_agent(GEND_BOT, 10 * sd + 3), 1 - me: make_agent(GEND_BOT, 10 * sd + 1)}
            while not s.over:
                apply(s, agents[s.active].act(s, legal_actions(s)))
            out[p["kind"]].append(1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5)
    return {"m": m, "k": st_row["k"], "K": 2 * k_half, "cpu": time.process_time() - t, "results": out,
            "failed": failed}


def gend(args):
    from multiprocessing import Pool
    plans_rows = {r["k"]: r for r in SD._lines(args.plans)}
    starts_by_k = {r["k"]: r for r in SD._lines(args.starts)}
    jobs = [(starts_by_k[g["k"]], g["m"], args.k) for g in SD._lines(args.gend_starts)]
    with Pool(args.workers, initializer=_init_teacher,
              initargs=(_records(args.selfplay), plans_rows, args.bank)) as pool, \
            open(args.out, "w", encoding="utf-8") as fh:
        for n, out in enumerate(pool.imap_unordered(_gend_job, jobs), 1):
            fh.write(json.dumps(out) + "\n")
            fh.flush()
            if n % 10 == 0:
                print(f"{n}/{len(jobs)}", flush=True)
    print(f"{len(jobs)} 个开头的 G_end 写进了 {args.out}")


# --- report -------------------------------------------------------------------------------------

def _kind_of(plans_k):
    """kind -> the kept plan's kind it is (itself, or the plan it was merged into)."""
    out = {}
    for p in plans_k:
        out[p["kind"]] = p["kind"]
        for m in p["merged"]:
            out[m] = p["kind"]
    return out


def _z(diffs):
    n = len(diffs)
    mean = sum(diffs) / n
    var = sum((d - mean) ** 2 for d in diffs) / max(n - 1, 1) / n
    return mean / var ** 0.5 if var > 0 else (0.0 if mean == 0 else float("inf") if mean > 0 else float("-inf"))


def _ranks(x):
    """Average ranks (ties share their mean rank), as scipy.stats.rankdata."""
    import numpy as np
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x))
    r[order] = np.arange(1, len(x) + 1)
    for v in np.unique(x):
        tie = x == v
        r[tie] = r[tie].mean()
    return r


def _spearman(x, y):
    import numpy as np
    rx, ry = _ranks(x), _ranks(y)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def report(args):
    import numpy as np
    starts_by_k = {r["k"]: r for r in SD._lines(args.starts)}
    plans_rows = {r["k"]: r for r in SD._lines(args.plans)}
    per = {}                                        # k -> {kind: [16 values]}
    fails = {}
    for r in SD._lines(args.teacher):
        d = per.setdefault(r["k"], {})
        for kind, v in r["values"].items():
            d.setdefault(kind, []).extend(v)        # seed 0 then 1 or 1 then 0: the same order for every kind
        for kind, f in r["failed"].items():
            fails.setdefault(kind.split(":")[0], []).extend(f)
    rows = []
    for k, d in sorted(per.items()):
        if any(len(v) != 16 for v in d.values()):
            continue
        T = {kind: sum(v) / 16 for kind, v in d.items()}
        best = max(T, key=T.get)
        worst = min(T, key=T.get)
        z_bw = _z([a - b for a, b in zip(d[best], d[worst])]) if best != worst else 0.0
        cross = []                                  # pick the best on one seed's 8, measure it on the other's
        for a, b in ((slice(0, 8), slice(8, 16)), (slice(8, 16), slice(0, 8))):
            pick = max(d, key=lambda kind: sum(d[kind][a]))
            cross.append(100 * (sum(d[pick][b]) - sum(d["bot"][b])) / 8)
        rows.append({"k": k, "src": starts_by_k[k]["src"], "n": len(T), "T": T, "vals": d,
                     "cross": sum(cross) / 2,
                     "first": T["bot"] >= T[best], "regret": 100 * (T[best] - T["bot"]),
                     "noisy": not abs(z_bw) > 1.96, "kinds": _kind_of(plans_rows[k]["plans"]),
                     "ties": len(set(round(t, 12) for t in T.values())) < len(T)})
    rng = np.random.default_rng(0)

    def boot(sel, f):
        if not sel:
            return "—"
        point = f(sel)
        bs = [f([sel[i] for i in rng.integers(0, len(sel), len(sel))]) for _ in range(2000)]
        return f"{point:.3f}（{np.percentile(bs, 2.5):.3f}～{np.percentile(bs, 97.5):.3f}）"
    share_first = lambda sel: float(np.mean([r["first"] for r in sel]))       # noqa: E731
    mean_regret = lambda sel: float(np.mean([r["regret"] for r in sel]))      # noqa: E731
    print("条件：对手卡表已知（牌序、手牌未知）。区间按开头重抽 2000 次（重抽种子 0）。\n")
    print(f"开头 {len(rows)} 个；候选数 {dict(sorted(Counter_(r['n'] for r in rows).items()))}；"
          f"少于 4 个的 {sum(r['n'] < 4 for r in rows)} 个；有两个候选 T 完全打平的 {sum(r['ties'] for r in rows)} 个\n")
    print("**1. bot 主线的名次和后悔**（后悔 = 最好候选的 T − 主线的 T，胜率百分点）")
    for src in ("selfplay", "salem"):
        for label, sel in (("差距在噪声以上", [r for r in rows if r["src"] == src and not r["noisy"]]),
                           ("全部", [r for r in rows if r["src"] == src])):
            print(f"- {'自对弈' if src == 'selfplay' else 'Salem 局'}，{label}的开头 {len(sel)} 个："
                  f"主线排第一 {boot(sel, share_first)}，平均后悔 {boot(sel, mean_regret)} 个百分点")
    cross_regret = lambda sel: float(np.mean([r["cross"] for r in sel]))     # noqa: E731
    print("- 副读（分析线补的，不改 J20）：交叉种子的后悔，用一个种子的 8 个确定化挑最好的候选，在另一个种子上量它比主线好多少，"
          "两个方向平均；直接的后悔是 4～6 个带噪的值里取最大，偏高，这个不偏：")
    for src in ("selfplay", "salem"):
        sel = [r for r in rows if r["src"] == src]
        print(f"  - {'自对弈' if src == 'selfplay' else 'Salem 局'}，全部 {len(sel)} 个开头：{boot(sel, cross_regret)} 个百分点")
    sp = [r for r in rows if r["src"] == "selfplay" and not r["noisy"]]
    if sp:
        f, g = share_first(sp), mean_regret(sp)
        print(f"- **J20**（自对弈、差距在噪声以上）：排第一 {f:.1%} ≤ 50% 且平均后悔 {g:.2f} ≥ 2 个百分点 → "
              f"{'对' if f <= 0.5 and g >= 2 else '错'}；停线条件（≥ 70% 且 < 1）→ {'触发' if f >= 0.7 and g < 1 else '不触发'}")
    print("\n**2. 每类候选赢 bot 主线的比例**（T 大于主线；显著：16 个配对差 z > 1.96）")
    kinds = sorted({kk.split(":")[0] for r in rows for kk in r["kinds"]} - {"bot"})
    for kind in kinds:
        better = sig = n = 0
        for r in rows:
            ks = [kk for kk in r["kinds"] if kk.split(":")[0] == kind]
            for kk in ks:
                plan = r["kinds"][kk]
                n += 1
                if plan == "bot":
                    continue
                better += r["T"][plan] > r["T"]["bot"]
                sig += _z([a - b for a, b in zip(r["vals"][plan], r["vals"]["bot"])]) > 1.96
        if n:
            print(f"- {kind}：{n} 个，大于主线 {better / n:.1%}，显著大于 {sig / n:.1%}")
    print("\n**复现失败**（老师的 16 个确定化里，打法在某一步对不上、由这类候选自己的策略接着打的比例）")
    for kind, f in sorted(fails.items()):
        failed = [x for x in f if x is not None]
        print(f"- {kind}：{len(failed)}/{len(f)}（{len(failed) / len(f):.1%}）"
              + (f"，其中第一步就对不上的 {sum(x == 0 for x in failed)}" if failed else ""))
    salem_diff = [r for r in rows if r["src"] == "salem" and "salem" in r["T"]]
    print(f"\n**3. Salem 和 bot 打法不同的回合**（{len(salem_diff)} 个）")
    if salem_diff:
        print(f"- T 偏向 Salem 的比例：{boot(salem_diff, lambda sel: float(np.mean([r['T']['salem'] > r['T']['bot'] for r in sel])))}")
    if args.gend:
        G = {}
        for r in SD._lines(args.gend):
            G[r["k"]] = r
        sg = []
        for k, g in G.items():
            res = g["results"]
            if "salem" in res and "bot" in res:
                a, b = np.mean(res["salem"]), np.mean(res["bot"])
                sg.append(1.0 if a > b else 0.5 if a == b else 0.0)
        if sg:
            mean_sg = lambda sel: float(np.mean(sel))       # noqa: E731
            print(f"- G_end 偏向 Salem 的比例（{len(sg)} 个回合，相等算一半）：{boot(sg, mean_sg)}；"
                  f"**J21**（≥ 55%）→ {'对' if mean_sg(sg) >= 0.55 else '错'}")
        print("\n**4. T 和 G_end 的一致**（每个开头里候选之间的 Spearman，开头上平均）")
        rho_tg, rho_half = [], []
        for k, g in G.items():
            if k not in per:
                continue
            ks = [kk for kk in g["results"] if kk in per[k]]
            if len(ks) < 3:
                continue
            K = g["K"]
            gm = [np.mean(g["results"][kk]) for kk in ks]
            tm = [np.mean(per[k][kk]) for kk in ks]
            g1 = [np.mean(g["results"][kk][:K // 2]) for kk in ks]
            g2 = [np.mean(g["results"][kk][K // 2:]) for kk in ks]
            for out, (x, y) in ((rho_tg, (tm, gm)), (rho_half, (g1, g2))):
                v = _spearman(x, y)
                if v is not None:
                    out.append(v)
        if rho_tg:
            print(f"- T 对 G_end：{boot(rho_tg, lambda sel: float(np.mean(sel)))}（{len(rho_tg)} 个开头）")
        if rho_half:
            print(f"- G_end 两组之间（噪声的参照）：{boot(rho_half, lambda sel: float(np.mean(sel)))}"
                  f"（{len(rho_half)} 个开头）")
        gf = {}
        for g in G.values():
            for kind, f in g["failed"].items():
                gf.setdefault(kind.split(":")[0], []).extend(f)
        print("- G_end 的复现失败：" + "，".join(f"{kind} {sum(x is not None for x in f)}/{len(f)}"
                                         for kind, f in sorted(gf.items())))


def Counter_(it):
    from collections import Counter
    return Counter(it)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("starts")
    a.add_argument("selfplay")
    a.add_argument("--out", required=True)
    a = sub.add_parser("plans")
    a.add_argument("selfplay")
    a.add_argument("starts")
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=12)
    a.add_argument("--only", default=None, help="only these k (comma-separated)")
    a = sub.add_parser("teacher")
    a.add_argument("selfplay")
    a.add_argument("starts")
    a.add_argument("plans")
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=12)
    a = sub.add_parser("pickgend")
    a.add_argument("starts")
    a.add_argument("plans")
    a.add_argument("--out", required=True)
    a = sub.add_parser("gend")
    a.add_argument("selfplay")
    a.add_argument("starts")
    a.add_argument("plans")
    a.add_argument("gend_starts")
    a.add_argument("--out", required=True)
    a.add_argument("--k", type=int, default=16, help="determinizations per group (2 groups)")
    a.add_argument("--workers", type=int, default=12)
    a = sub.add_parser("report")
    a.add_argument("starts")
    a.add_argument("plans")
    a.add_argument("teacher")
    a.add_argument("--gend", default=None)
    for sp in sub.choices.values():
        sp.add_argument("--bank", type=int, default=BANK, help="the seed bank (another only for smoke tests)")
    args = ap.parse_args()
    _set_bank(args.bank)
    {"starts": starts, "plans": plans, "teacher": teacher, "pickgend": pickgend, "gend": gend,
     "report": report}[args.cmd](args)


if __name__ == "__main__":
    main()
