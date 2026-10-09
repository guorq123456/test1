"""The n30 teacher re-run with every own turn's end kept: contrast pairs for turn-level step 1 (the architecture
thread 2026-10-09 07:42Z: option (b), one machine, one run, so labels and turn ends match bit for bit).

Same positions and seeds as the student data (b355c44): position n, seed s -> teacher seed 65820000 + 2n + s, the
teacher exactly as teacher_eval.measure (CrossTurnAgent(mcts-raw:100+learned+phased, next_turn, research 100,
next_search 30, samples 8)). Nothing of the teacher is copied: a subclass only records, while the teacher plays
each candidate's own turn, the actions it applies (crossturn_agent's `apply`, wrapped for that stretch), and the
8 determinization seeds (the agent's random state just before `outcomes`, which draws them first).

    cd <svsim checkout at b355c44> && PYTHONPATH=.:<this folder> python3 <this> run selfplay.jsonl positions.jsonl \\
        --out teacher_ends.jsonl.gz [--workers 4]
    ... <this> check selfplay.jsonl positions.jsonl teacher_ends.jsonl.gz --teacher teacher.jsonl [--sample 2000]

One JSON line per (position, seed, determinization, candidate), gzip:
    {"n", "g", "at", "seat", "s", "seed": the teacher's seed, "j": the determinization (0-7), "det_seed",
     "r": "line" (the teacher's principal line) or the restriction (keep:<card id>, save, noevo),
     "actions": the own turn's actions (svsim.core.actions.to_dict, in order; the end of turn not included),
     "value": this determinization's play-out value (the opponent's turn, the own next turn, the ENDED model),
     "summary": {"hp": [mover, opponent], "hand": [sizes], "field": [[card ids in order], [..]], "pp": mover's pp}
     at the own turn's end}
Positions whose principal line has no restriction (nothing to contrast) are left out.

T of a restriction on seed s = the mean over j of value(r) - value(line); se as teacher_eval.measure.

Reading (`turn_end`, `pairs`): a row gives back its turn-end State - the start position from the record,
determinized with det_seed, the actions applied - and the summary is checked (a mismatch raises). `pairs` gives the
step-1 trainer one item per (position, seed, determinization, restriction): (start id, turn end a = the restricted
line's, turn end b = the principal line's, dT = value(a) - value(b), weight 1), leaving out determinizations where
both lines took the same actions (the same turn end: nothing to contrast).
"""
import argparse
import gzip
import json
import math
import os
import random
from multiprocessing import Pool

import student_data as SD

BANK = SD.BANK                                    # 65800000: the student data's bank
TEACHER = "mcts-raw:100+learned+phased"
SAMPLES, RESEARCH, NEXT_SEARCH = 8, 100, 30


def summary(state, me: int) -> dict:
    p, o = state.players[me], state.players[1 - me]
    return {"hp": [p.leader_hp, o.leader_hp], "hand": [len(p.hand), len(o.hand)],
            "field": [[c.defn.card_id for c in p.field], [c.defn.card_id for c in o.field]], "pp": p.pp}


def _agent(seed):
    """The teacher of teacher_eval.measure, recording its own turns."""
    import svsim.agents.crossturn_agent as CT
    from svsim.core.actions import to_dict
    from svsim.tools.arena import make_agent

    class Recording(CT.CrossTurnAgent):
        def _own_turn(self, s, me, line, veto):
            taken, plain = [], CT.apply

            def apply(state, action):
                taken.append(to_dict(action))
                return plain(state, action)
            CT.apply = apply
            try:
                super()._own_turn(s, me, line, veto)
            finally:
                CT.apply = plain
            self.turns.append((taken, summary(s, me)))

    agent = Recording(make_agent(TEACHER, seed), samples=SAMPLES, seed=seed, next_turn=True, research=RESEARCH,
                      next_search=NEXT_SEARCH, opp_search=0)
    agent.turns = []
    return agent


def measure(state, seed):
    """(candidates, determinization seeds, {r: [value per determinization]}, [(actions, summary)] in outcomes'
    order: determinization by determinization, candidates in order), as teacher_eval.measure computes it."""
    from svsim.agents.crossturn_agent import principal_line, restrictions
    agent = _agent(seed)
    agent.search.choose(state)
    line = principal_line(agent.search.last_root)
    cands = restrictions(line)
    lines = agent.lines_for(state, line, cands)
    r = random.Random()
    r.setstate(agent.rng.getstate())              # outcomes draws the determinization seeds first
    det_seeds = [r.getrandbits(64) for _ in range(agent.samples)]
    out = agent.outcomes(state, lines, cands)
    return cands, det_seeds, out, agent.turns


GAMES, POS = {}, {}


def _init(games, pos):
    GAMES.update(games)
    POS.update(pos)


def _job(job):
    from svsim.agents.crossturn_agent import NONE
    n, s = job
    p = POS[n]
    st = SD._state_at(GAMES[p["g"]], p["at"])
    me = st.active
    seed = BANK + 20000 + 2 * n + s
    cands, det_seeds, out, turns = measure(st, seed)
    if len(cands) < 2:                            # the line alone: nothing to contrast
        return []
    rows, i = [], 0
    for j, sd in enumerate(det_seeds):
        for r in cands:
            actions, summ = turns[i]
            i += 1
            rows.append({"n": n, "g": p["g"], "at": p["at"], "seat": me, "s": s, "seed": seed, "j": j,
                         "det_seed": sd, "r": "line" if r == NONE else r, "actions": actions,
                         "value": out[r][j], "summary": summ})
    return rows


def run(args):
    games = {r["g"]: r for r in SD._lines(args.selfplay)}
    pos = {p["n"]: p for p in SD._lines(args.positions)}
    jobs = [(n, s) for n in sorted(pos) for s in (0, 1)]
    if args.first is not None:                    # smoke tests only
        jobs = [j for j in jobs if j[0] < args.first]
    rows = 0
    with Pool(args.workers, initializer=_init, initargs=(games, pos)) as pool, \
            gzip.open(args.out, "wt", encoding="utf-8") as fh:
        for k, out in enumerate(pool.imap_unordered(_job, jobs, chunksize=4), 1):
            for row in out:
                fh.write(json.dumps(row, separators=(",", ":")) + "\n")
            rows += len(out)
            if k % 500 == 0:
                print(f"  {k} / {len(jobs)}，{rows} 行", flush=True)
    print(f"{len(jobs)} 个（局面 × 种子），{rows} 行写进了 {args.out}")


# --- reading ------------------------------------------------------------------------------------

def rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


class Starts:
    """Start positions by n, from the self-play records (cached)."""

    def __init__(self, selfplay, positions=None):
        self.games = {r["g"]: r for r in SD._lines(selfplay)}
        self.cache = {}

    def get(self, n, g, at):
        if n not in self.cache:
            self.cache[n] = SD._state_at(self.games[g], at)
        return self.cache[n]


def turn_end(row, starts: Starts, end_of_turn: bool = False):
    """The row's own-turn end, rebuilt: the start position determinized with det_seed, the actions applied; the
    summary checked (ValueError if it doesn't match). end_of_turn: also resolve the end-of-turn abilities, as the
    ENDED model sees it (search.evaluate.after_end_of_turn), without starting the opponent's turn."""
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    from svsim.core.view import determinize
    st = starts.get(row["n"], row["g"], row["at"])
    me = row["seat"]
    s = determinize(st, me, random.Random(row["det_seed"]))
    for a in row["actions"]:
        apply(s, from_dict(a))
    got = summary(s, me)
    if got != row["summary"]:
        raise ValueError(f"turn end of n={row['n']} s={row['s']} j={row['j']} r={row['r']} rebuilt as {got}, "
                         f"recorded {row['summary']}")
    if end_of_turn:
        from svsim.search.evaluate import after_end_of_turn
        s = after_end_of_turn(s)
    return s


def groups(path):
    """((n, s), {r: [row per determinization]}) one (position, seed) at a time: `run` writes each one's rows
    together, so the file streams (no need to hold 400,000 rows)."""
    key, d = None, {}
    for row in rows(path):
        k = (row["n"], row["s"])
        if k != key and d:
            yield key, d
            d = {}
        key = k
        d.setdefault(row["r"], [None] * SAMPLES)[row["j"]] = row
    if d:
        yield key, d


def teacher_values(d) -> dict:
    """{r: (T, se)} for one (position, seed), as teacher_eval.measure: the mean of value(r) - value(line)."""
    out = {}
    base = [x["value"] for x in d["line"]]
    for r, rs in d.items():
        if r == "line":
            continue
        diffs = [x["value"] - b for x, b in zip(rs, base)]
        m = sum(diffs) / len(diffs)
        se = math.sqrt(sum((x - m) ** 2 for x in diffs) / max(len(diffs) - 1, 1) / len(diffs))
        out[r] = (m, se)
    return out


def pairs(path, starts: Starts, end_of_turn: bool = False, keep_same: bool = False):
    """The step-1 trainer's items, streamed: {"start": n, "s", "j", "r", "a": the restricted line's turn end
    (State), "b": the principal line's (State), "dT": value(a) - value(b), "weight": 1.0}. Determinizations where
    both lines took the same actions (the same turn end) are left out unless keep_same."""
    for (n, s), d in groups(path):
        line = d["line"]
        for r, rs in sorted(d.items()):
            if r == "line":
                continue
            for x, b in zip(rs, line):
                if x["actions"] == b["actions"] and not keep_same:
                    continue
                yield {"start": n, "s": s, "j": x["j"], "r": r, "a": turn_end(x, starts, end_of_turn),
                       "b": turn_end(b, starts, end_of_turn), "dT": x["value"] - b["value"], "weight": 1.0}


def check(args):
    """The file read back: every (position, seed) complete, a sample of turn ends rebuilt (summaries checked),
    T recomputed from the rows and set beside b355c44's teacher.jsonl."""
    import numpy as np
    starts = Starts(args.selfplay)
    rng = random.Random(0)
    n_groups = n_rows = n_pairs = same = 0
    complete = True
    sample, seen = [], 0
    T = {}
    for (n, s), d in groups(args.ends):
        n_groups += 1
        for r, rs in d.items():
            complete &= all(x is not None for x in rs) and "line" in d
            for x in rs:
                n_rows += 1
                seen += 1
                if len(sample) < args.sample:          # reservoir sample, seed 0
                    sample.append(x)
                elif rng.random() < args.sample / seen:
                    sample[rng.randrange(args.sample)] = x
            if r != "line":
                n_pairs += len(rs)
                same += sum(x["actions"] == b["actions"] for x, b in zip(rs, d["line"]))
        for r, v in teacher_values(d).items():
            T[(n, s, r)] = v
    print("条件：对手卡表已知（牌序、手牌未知）。老师连同回合末重跑的核对\n")
    print(f"- {n_groups} 个（局面 × 种子），{n_rows} 行；每个候选 8 个确定化都齐、都有主线：{complete}")
    bad = 0
    for x in sample:
        try:
            turn_end(x, starts)
        except ValueError as e:
            bad += 1
            if bad <= 5:
                print("  ", e)
    print(f"- 抽 {len(sample)} 行重建回合末（蓄水池抽样，种子 0），摘要对不上的 {bad} 行")
    print(f"- 对比对（限制 × 确定化）{n_pairs} 个，其中两条线动作完全相同、没有可比的 {same} 个"
          f"（{same / max(n_pairs, 1):.1%}），`pairs` 默认去掉")
    if args.teacher:
        ref = {}
        for row in SD._lines(args.teacher):
            for k, v in row["res"].items():
                ref[(row["n"], row["s"], k)] = v["teacher"]
        both = [(T[k][0], ref[k]) for k in T if k in ref]
        same_t = sum(abs(a - b) < 1e-12 for a, b in both)
        d = np.array([abs(a - b) for a, b in both])
        print(f"- 和 b355c44 的 T 比：共有 {len(both)} 个（局面 × 种子 × 限制），逐位相同 {same_t}（{same_t / max(len(both), 1):.1%}）；"
              f"|ΔT| 中位 {np.median(d):.4f}、95% 分位 {np.percentile(d, 95):.4f}、最大 {d.max():.4f}；"
              f"只在这次有的 {len(set(T) - set(ref))}，只在 b355c44 有的 {len(set(ref) - set(T))}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run")
    a.add_argument("selfplay")
    a.add_argument("positions")
    a.add_argument("--out", required=True)
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--first", type=int, default=None)
    b = sub.add_parser("check")
    b.add_argument("selfplay")
    b.add_argument("positions")
    b.add_argument("ends")
    b.add_argument("--teacher", default=None)
    b.add_argument("--sample", type=int, default=2000)
    args = ap.parse_args()
    {"run": run, "check": check}[args.cmd](args)


if __name__ == "__main__":
    main()
