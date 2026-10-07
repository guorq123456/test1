"""How sharp is the search's root visit distribution, and how often does search change the greedy choice?

    cd <svsim checkout> && PYTHONPATH=. python3 sharpness.py RECORDS.jsonl [--agent SPEC] [--workers 4]

Reads self-play records written by svsim.learn.netdata (record["search"][i]:
the root visits of every legal move, in legal_actions order, for decisions the
ISMCTS made; None where the lethal search or the planner chose). For each such
decision with more than one legal move it measures:
- the number of legal moves;
- the root visit distribution pi: its entropy over log(number of legal moves)
  (0 = all visits on one move, 1 = spread evenly), and whether the most-visited
  move has at least 80% of the visits;
- whether the search's choice (the most-visited move; the move actually played
  may be an exploration move) equals the greedy choice: every legal move
  applied once (EndTurn: the end-of-turn abilities resolved, as the search's
  leaves are) and the resulting position scored with the agent's own leaf
  evaluation, no search at all (ties: agreement if the search's move is among
  the best).
Grouped by the moment in the turn (the turn's first decision / a later one /
the decision that ended the turn) and by the player's own turn number.
"""
import argparse
import json
import math
import statistics
from collections import defaultdict
from multiprocessing import Pool

SPEC = "mcts:100+plan+learned+phased"


def _weights(spec):
    from svsim.tools.arena import make_agent
    inner = make_agent(spec, 0)
    while not (hasattr(inner, "search") and hasattr(inner.search, "weights")):
        inner = inner.base
    return inner.search.weights


def analyse(args):
    line, spec = args
    from svsim.cards import library, decks  # noqa: F401
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.search.evaluate import after_end_of_turn, evaluate
    from svsim.tools import records as R
    weights = _weights(spec)
    record = json.loads(line)
    thoughts = record.get("search") or []
    acts = record["actions"]
    # which decisions start / end a turn (by the actions actually played)
    out, rows = [], []
    for i, (state, action) in enumerate(R.steps(record)):
        if state.phase != Phase.MAIN:
            continue
        rows.append((i, state.turn, state.active, isinstance(action, EndTurn), state.clone()))
    first_of_turn = {}
    for i, turn, active, ends, _ in rows:
        first_of_turn.setdefault((turn, active), i)
    for i, turn, me, ends, state in rows:
        legal = legal_actions(state)
        if len(legal) < 2:
            continue
        moment = "start" if first_of_turn[(turn, me)] == i else ("end" if ends else "mid")
        own = state.players[me].turns_taken
        bucket = "1-3" if own <= 3 else "4-6" if own <= 6 else "7+"
        t = thoughts[i] if i < len(thoughts) else None
        if not t or not sum(t["visits"]):
            out.append({"moment": moment, "bucket": bucket, "searched": False, "legal": len(legal)})
            continue
        visits = t["visits"]
        total = sum(visits)
        pi = [v / total for v in visits]
        H = -sum(p * math.log(p) for p in pi if p > 0) / math.log(len(legal))
        top = max(range(len(visits)), key=lambda k: visits[k])
        scores = []
        for a in legal:
            if isinstance(a, EndTurn):
                s2 = after_end_of_turn(state)
            else:
                s2 = state.clone()
                apply(s2, a)
            scores.append(evaluate(s2, me, weights))
        best = max(scores)
        greedy_set = {k for k, s in enumerate(scores) if s >= best - 1e-9}
        out.append({"moment": moment, "bucket": bucket, "searched": True, "legal": len(legal),
                    "entropy": H, "sharp": pi[top] >= 0.8, "agree": top in greedy_set,
                    "top_share": pi[top], "tried": sum(1 for v in visits if v) / len(legal),
                    "visits": total})
    return out


def summarize(rows, key):
    groups = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    groups["all"] = rows
    lines = []
    order = {"moment": ["start", "mid", "end", "all"], "bucket": ["1-3", "4-6", "7+", "all"]}[key]
    for g in order:
        rs = groups.get(g, [])
        s = [r for r in rs if r["searched"]]
        if not s:
            continue
        legal = sorted(r["legal"] for r in s)
        lines.append({
            "group": g, "decisions": len(rs), "searched": len(s),
            "legal_median": statistics.median(legal), "legal_p90": legal[int(0.9 * (len(legal) - 1))],
            "entropy_mean": statistics.mean(r["entropy"] for r in s),
            "entropy_median": statistics.median(r["entropy"] for r in s),
            "sharp_share": sum(r["sharp"] for r in s) / len(s),
            "agree_share": sum(r["agree"] for r in s) / len(s),
            "top_mean": statistics.mean(r["top_share"] for r in s),
            "tried_mean": statistics.mean(r["tried"] for r in s),
            "visits_median": statistics.median(r["visits"] for r in s),
            "not_searched": len(rs) - len(s),
        })
    return lines


def main():
    p = argparse.ArgumentParser()
    p.add_argument("records")
    p.add_argument("--agent", default=SPEC, help="whose leaf evaluation scores the greedy choice")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--json", default=None, help="write the per-decision rows here")
    args = p.parse_args()
    lines = [line for line in open(args.records, encoding="utf-8") if line.strip()]
    with Pool(args.workers) as pool:
        rows = [r for part in pool.imap_unordered(analyse, [(line, args.agent) for line in lines]) for r in part]
    if args.json:
        json.dump(rows, open(args.json, "w"))
    print(f"{len(lines)} 局，{len(rows)} 个有 2 个以上合法动作的决策点")
    for key, title in (("moment", "按回合内的时刻"), ("bucket", "按自己的回合数")):
        print(f"\n{title}")
        print(f"{'组':<6}{'决策':>7}{'搜索':>7}{'合法动作中位/p90':>16}{'熵均值':>8}{'熵中位':>8}{'最高占比':>9}{'π最高≥0.8':>11}{'试过的动作':>10}{'同贪心首选':>11}")
        for s in summarize(rows, key):
            print(f"{s['group']:<6}{s['decisions']:>7}{s['searched']:>7}{s['legal_median']:>10.0f} / {s['legal_p90']:<4}"
                  f"{s['entropy_mean']:>8.2f}{s['entropy_median']:>8.2f}{s['top_mean']:>9.0%}{s['sharp_share']:>11.0%}"
                  f"{s['tried_mean']:>10.0%}{s['agree_share']:>11.0%}")
    s_all = summarize(rows, "moment")[-1]
    print(f"\n每个决策点根节点总访问数中位数：{s_all['visits_median']:.0f}")


if __name__ == "__main__":
    main()
