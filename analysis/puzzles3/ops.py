"""The three operations puzzles (the architecture thread 2026-10-10 08:46Z; the analysis line's d9f691e,
analysis/lethal-setup/puzzles/puzzles.md): original Ramp mirror, Salem low on defense facing a big threat; Salem
removes it with Spilling Red and stabilises with Erntz, the bot doesn't. Taken apart as the pirate puzzle was.
Condition: the opponent's deck list is known (order and hand not).

Per puzzle (k = 320, 518, 445 of turn-level step 0):
1. the position rebuilt from the record (turn_level._start_state; the agents determinize the opponent's hand
   themselves, nothing hidden is read by them);
2. level-strong, mcts:1043+plan+learned+phased and mcts:3000+plan+learned+phased each play the turn on 8 seeds
   (65960000 + k + 1000 j, as the waste diagnostic), their lines and turn ends kept;
3. at the turn's first decision, the search's root children: whether Salem's first action is among them, its visits
   and value against the chosen one's; whether any run reaches Salem's turn end;
4. the installed evaluation (level-strong's weights, the ENDED model the search scores turn ends with) on Salem's
   turn end and the bot's (step 0's line, and each run's): its win probability and, for the linear model, the
   features that make the difference (coefficient x standardized difference);
5. a class: "generation" (Salem's line never searched / not reachable) or "evaluation" (searched but scored lower).

    python3 ops.py STEP0_DIR ANA_DIR --out rows.jsonl [--seeds 8] [--workers 3]
    python3 ops.py --read rows.jsonl
"""
import argparse
import json
import os
import sys
import time

SPECS = ("level-strong", "mcts:1043+plan+learned+phased", "mcts:3000+plan+learned+phased")
KS = (320, 518, 445)
SEED = 65960000
G = {}


def _paths(ana):
    for sub in ("lethal-setup", "turn-level", "card-value"):
        p = os.path.join(ana, sub)
        if p not in sys.path:
            sys.path.insert(0, p)


def _init(step0, ana):
    _paths(ana)
    import setup_prob as SP
    import turn_level as TL
    TL.REC.update(TL._records(os.path.join(step0, "selfplay.jsonl")))
    starts, plans = SP._starts(step0)
    G["starts"] = {r["k"]: r for r in starts}
    G["plans"] = plans


def ended_model(weights, state, player):
    """The linear model the phased weights score `player`'s turn end with (as PhasedLearned.score finds it)."""
    from svsim.learn.phased import matchup_keys
    mine, theirs = state.players[player].deck_name, state.players[1 - player].deck_name
    keys = []
    if mine and theirs:
        keys.append((mine, theirs))
        if weights.aliases and mine == theirs and mine in weights.aliases:
            keys.append((weights.aliases[mine], weights.aliases[theirs]))
    keys += list(matchup_keys(state, player, weights.aliases))
    return next((weights.models[k + ("ended",)] for k in keys if k + ("ended",) in weights.models), None)


def turn_end(state, actions):
    """The position after the turn (end-of-turn abilities resolved, the opponent not started), as M3 reads it."""
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.search.evaluate import after_end_of_turn
    s = state.clone()
    for a in actions:
        a = from_dict(a) if isinstance(a, dict) else a
        if isinstance(a, EndTurn) or s.over:
            break
        apply(s, a)
    return s if s.over else after_end_of_turn(s)


def judge_end(end, me, weights):
    """(win probability under the installed evaluation, standardized feature vector of the ENDED model, its coef)."""
    import math
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import evaluate
    if end.over:
        return (1.0 if end.winner == me else 0.0), None
    z = evaluate(end, me, weights, False)
    p = 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z / SCALE))))
    m = ended_model(weights, end, me)
    if m is None:
        return p, None
    x = m.inputs(end, me)
    return p, {n: (c * (v - mu) / sd) for n, c, v, mu, sd in zip(m.names(), m.coef, x, m.mean, m.std)}


def _job(job):
    import turn_level as TL
    from svsim.core.actions import EndTurn, to_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    k, spec, j = job
    st = G["starts"][k]
    state, rec = TL._start_state(st)
    salem = TL._salem_turn(rec, st["at"])
    agent = make_agent(spec, SEED + k + 1000 * j)
    search = _search(agent)
    s, me, actions, root = state.clone(), state.active, [], None
    t0 = time.perf_counter()
    while not s.over and s.active == me:
        legal = legal_actions(s)
        a = agent.act(s, legal)
        if root is None:                              # the turn's first decision: the search's root children
            r = getattr(search, "last_root", None)
            where = _locator(s, me)
            sk = action_key(s, salem[0], where)
            ck = action_key(s, a, where)
            kids = sorted(((n.visits, n.value, key) for key, n in (r.children.items() if r else [])), reverse=True)
            rank = next((i for i, (_, _, key) in enumerate(kids) if key == sk), None)
            root = {"children": len(kids), "legal": len(legal), "salem_rank": rank,
                    "salem_visits": kids[rank][0] if rank is not None else 0,
                    "salem_value": round(kids[rank][1], 4) if rank is not None else None,
                    "chosen_visits": next((v for v, _, key in kids if key == ck), 0),
                    "chosen_value": next((round(val, 4) for _, val, key in kids if key == ck), None),
                    "chosen_is_salem": ck == sk}
        actions.append(a)
        if isinstance(a, EndTurn):
            break
        apply(s, a)
    ms = (time.perf_counter() - t0) * 1000
    return {"k": k, "spec": spec, "j": j, "actions": [to_dict(a) for a in actions], "root": root, "ms": round(ms)}


def run(args):
    from multiprocessing import Pool
    jobs = [(k, spec, j) for spec in SPECS for k in args.ks for j in range(args.seeds)]
    with Pool(args.workers, initializer=_init, initargs=(args.step0, args.ana)) as pool, \
            open(args.out, "w", encoding="utf-8") as fh:
        for r in pool.imap_unordered(_job, jobs):
            fh.write(json.dumps(r) + "\n")
            fh.flush()


def read(args):
    _init(args.step0, args.ana)
    import turn_level as TL
    from collections import Counter
    from svsim.core.actions import from_dict
    from svsim.search.lethal import state_key
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    from svsim.ui.text import describe_line
    W = _search(make_agent("level-strong", 0)).weights
    rows = [json.loads(x) for x in open(args.read) if x.strip()]
    out = ["条件：对手卡表已知（牌序、手牌未知）。三道运营局面题：拆解\n"]
    verdicts = {}
    for k in args.ks:
        st = G["starts"][k]
        state, rec = TL._start_state(st)
        me = state.active
        salem = TL._salem_turn(rec, st["at"])
        bot0 = [from_dict(a) for a in next(p for p in G["plans"][k]["plans"] if p["kind"] == "bot")["actions"]]
        s_end, b_end = turn_end(state, salem), turn_end(state, bot0)
        s_key = state_key(s_end)
        ps, fs = judge_end(s_end, me, W)
        pb, fb = judge_end(b_end, me, W)
        out.append(f"## 题 k = {k}\n")
        out.append("- Salem 的线：" + "；".join(describe_line(state, salem)))
        out.append("- 第 0 步 bot 的线：" + "；".join(describe_line(state, bot0)))
        out.append(f"- 现装评估器给回合末的胜率：**Salem {ps:.3f}**，第 0 步 bot 的线 {pb:.3f}")
        if fs and fb:
            diff = sorted(((fs[n] - fb[n], n) for n in fs), key=lambda t: -abs(t[0]))
            out.append("- 差最大的特征（Salem − bot，logit 贡献）：" + "，".join(f"{n} {d:+.3f}" for d, n in diff[:8]))
        sel = [r for r in rows if r["k"] == k]
        out.append("\n| 规格 | 种子 | 选了 Salem 的第一步 | Salem 第一步在根节点（名次 / 访问 / 值） | 选中的（访问 / 值） | 根节点子节点 / 合法 | 回合末胜率（现装） | 和 Salem 回合末相同 |\n|---|---|---|---|---|---|---|---|")
        reach = 0
        for spec in SPECS:
            for r in sorted((r for r in sel if r["spec"] == spec), key=lambda r: r["j"]):
                acts = [from_dict(a) for a in r["actions"]]
                e = turn_end(state, acts)
                p, _ = judge_end(e, me, W)
                same = state_key(e) == s_key
                reach += same
                ro = r["root"] or {}
                out.append(f"| {spec.split('+')[0]} | {r['j']} | {'是' if ro.get('chosen_is_salem') else '否'} | "
                           f"{ro.get('salem_rank')} / {ro.get('salem_visits')} / {ro.get('salem_value')} | "
                           f"{ro.get('chosen_visits')} / {ro.get('chosen_value')} | {ro.get('children')} / {ro.get('legal')} | "
                           f"{p:.3f} | {'是' if same else '否'} |")
        first_seen = sum(1 for r in sel if (r["root"] or {}).get("salem_rank") is not None)
        lines = Counter(" ; ".join(describe_line(state, [from_dict(a) for a in r["actions"]])) for r in sel)
        out.append("\n各规格打出的线（次数）：")
        for line, n in lines.most_common():
            out.append(f"- {n} × {line}")
        verdicts[k] = {"installed prefers Salem": ps > pb, "p_salem": ps, "p_bot": pb, "runs reaching Salem's end": reach,
                       "runs whose root holds Salem's first action": first_seen, "runs": len(sel)}
        out.append("")
    out.append("**小结**：" + json.dumps(verdicts, ensure_ascii=False))
    print("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step0", nargs="?")
    ap.add_argument("ana", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--read")
    ap.add_argument("--ks", type=int, nargs="+", default=list(KS), help="step-0 starts (k) to take apart")
    args = ap.parse_args()
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    _paths(args.ana)
    read(args) if args.read else run(args)


if __name__ == "__main__":
    main()
