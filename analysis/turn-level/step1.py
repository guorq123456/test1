"""Turn-level step 1: the data for the contrast-trained turn-end evaluation (README.md here, section "第 1 步";
written before any of its games). Condition: the opponent's deck list is known (order and hand not).

    cd <svsim checkout, build line 842654e or later> && set PYTHONPATH=.;<analysis>/turn-level;<analysis>/card-value
    python -m svsim.tools.host svsim.learn.netdata --games 1000 --deck ramp --opponent ramp --agent level-strong \\
        --explore 0 --seed 66100000 --workers 12 --out selfplay.jsonl
    python -m svsim.tools.host step1 starts selfplay.jsonl --out starts.jsonl
    python -m svsim.tools.host step1 plans selfplay.jsonl starts.jsonl --out plans.jsonl --workers 12
    python -m svsim.tools.host step1 teacher selfplay.jsonl starts.jsonl plans.jsonl --out teacher.jsonl \\
        --ends teacher_ends.jsonl.gz --workers 12
    python -m svsim.tools.host step1 gend selfplay.jsonl starts.jsonl plans.jsonl --out gend.jsonl \\
        --ends gend_ends.jsonl.gz --workers 12

Seeds (bank 66100000-66199999): self-play netdata --seed 66100000; the starts Random(66110000); the plans
66120000 + k; T 66130000 + 2k + s (a failed replay's policy 10 x that + the determinization); G_end determinization
j of start k 66140000 + 20k + j (its failed replay's policy 10 x that, then the G_end bot 10 x that + 3 for the
mover, + 1 for the opponent).

Starts: every own-turn start of the 1000 games, sorted (g, action index, seat), shuffled by Random(66110000), the
first 2000; held out ("val") when g % 11 == 0. G_end K = 4 (2 groups of 2) on training starts, 16 (2 of 8) on
held-out ones. Plans, the replay rule and T as step 0 (turn_level.py), the plans by the build line's generator.

Turn ends: one gzip line per (start, seed, determinization, plan) for T and per (start, determinization, plan) for
G_end, in analysis/card-value/teacher_ends.py's row format ({"n": k, "g", "at", "seat", "s", "j", "det_seed", "r":
the plan's kind, "actions", "value": T's play-out value or G_end's result, "summary"}), so its `turn_end` rebuilds
them (the start from selfplay.jsonl, determinized with det_seed, the actions applied, the summary checked).
"""
import argparse
import gzip
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "card-value"))
sys.path.insert(0, HERE)

import student_data as SD        # noqa: E402
import teacher_ends as TEN       # noqa: E402  (summary, the row format, turn_end)
import turn_level as TL          # noqa: E402  (the plans, the replay rule, the teacher as step 0)

BANK = 66100000
N_STARTS = 2000
HOLD_OUT = 11
K_TRAIN, K_VAL = 2, 8            # determinizations per group (2 groups)
END_SHARE = 0.10                 # the "end" pairs' share of the step-1 pairs' total weight
TAU2_FLOOR = 1e-4


def starts(args):
    games = SD._lines(args.selfplay)
    allp = sorted((rec["g"], at, seat) for rec in games for at, seat in SD.own_turn_starts(rec))
    random.Random(BANK + 10000).shuffle(allp)
    by_g = {rec["g"]: rec for rec in games}
    with open(args.out, "w", encoding="utf-8") as fh:
        for k, (g, at, seat) in enumerate(allp[:N_STARTS]):
            st = SD._state_at(by_g[g], at)
            val = g % HOLD_OUT == 0
            fh.write(json.dumps({"k": k, "src": "selfplay", "game": g, "at": at, "seat": seat,
                                 "own_turn": st.players[seat].turns_taken, "split": "val" if val else "train",
                                 "K": 2 * (K_VAL if val else K_TRAIN)}) + "\n")
    n_val = sum(1 for g, _, _ in allp[:N_STARTS] if g % HOLD_OUT == 0)
    print(f"自对弈 {len(games)} 局，{len(allp)} 个自己回合的开头，取 {min(N_STARTS, len(allp))} 个（留出 {n_val}）")


def _plans_job(st_row):
    import time
    from svsim.core.actions import EndTurn, to_dict
    from svsim.core.engine import apply
    from svsim.search.candidates import generate
    state, _ = TL._start_state(st_row)
    t = time.process_time()
    cands = generate(state, spec=TL.BOT, seed=BANK + 20000 + st_row["k"])
    cpu = time.process_time() - t
    plans = []
    for c in cands:
        s, keys = state.clone(), []
        for a in c.actions:
            keys.append(TL._key(s, a))
            if isinstance(a, EndTurn) or s.over:
                break
            apply(s, a)
        plans.append({"kind": c.kind, "merged": c.merged, "times": c.times, "keys": keys,
                      "actions": [to_dict(a) for a in c.actions]})
    return {"k": st_row["k"], "src": st_row["src"], "cpu": cpu, "plans": plans}


def _set_bank(bank):
    global BANK
    BANK = bank


def _init(recs, plans_rows, bank):
    """Pool initializer: the records and plans in this worker, and the bank (under spawn, as on Windows, a module
    global set in the parent doesn't reach the workers)."""
    TL.REC.update(recs)
    if plans_rows:
        TL.PLANS.update(plans_rows)
    _set_bank(bank)


def _pool(args, plans_rows=None):
    from multiprocessing import Pool
    return Pool(args.workers, initializer=_init, initargs=(TL._records(args.selfplay), plans_rows, BANK))


def plans(args):
    rows = SD._lines(args.starts)
    with _pool(args) as pool, \
            open(args.out, "w", encoding="utf-8") as fh:
        for n, out in enumerate(pool.imap_unordered(_plans_job, rows), 1):
            fh.write(json.dumps(out) + "\n")
            fh.flush()
            if n % 100 == 0:
                print(f"{n}/{len(rows)}", flush=True)
    print(f"{len(rows)} 个开头的候选写进了 {args.out}")


def _end_row(st_row, me, s, j, det_seed, kind, taken, value, state):
    return {"n": st_row["k"], "g": st_row["game"], "at": st_row["at"], "seat": me, "s": s, "j": j,
            "det_seed": det_seed, "r": kind, "actions": taken, "value": value, "summary": TEN.summary(state, me)}


def _teacher_job(job):
    """T as turn_level._teacher_job (step 0), with step 1's seed and every turn end kept."""
    import time
    from svsim.agents.crossturn_agent import CrossTurnAgent
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    st_row, s_idx = job
    k = st_row["k"]
    state, _ = TL._start_state(st_row)
    me = state.active
    seed = BANK + 30000 + 2 * k + s_idx
    t = time.process_time()
    agent = CrossTurnAgent(make_agent(TL.TEACHER, seed), samples=8, seed=seed, next_turn=True, next_search=30)
    plans_k = TL.PLANS[k]["plans"]
    seeds = [agent.rng.getrandbits(64) for _ in range(agent.samples)]
    values = {p["kind"]: [] for p in plans_k}
    failed = {p["kind"]: [] for p in plans_k}
    ends = []
    for j, sd in enumerate(seeds):
        base = determinize(state, me, random.Random(sd))
        for p in plans_k:
            s = base.clone()
            taken = []
            keys = [TL._norm(x) for x in p["keys"]]
            failed[p["kind"]].append(TL.replay(s, me, keys, TL._veto(p["kind"]),
                                               TL.finisher(p["kind"], me, 10 * seed + j, taken), taken))
            end_summary_state = s.clone()
            agent._their_turn(s, me)
            v = agent._value(s, me)
            values[p["kind"]].append(v)
            ends.append(_end_row(st_row, me, s_idx, j, sd, p["kind"], taken, v, end_summary_state))
    return ({"k": k, "s": s_idx, "seed": seed, "cpu": time.process_time() - t, "values": values,
             "failed": failed, "n_keys": {p["kind"]: len(p["keys"]) for p in plans_k}}, ends)


def teacher(args):
    plans_rows = {r["k"]: r for r in SD._lines(args.plans)}
    rows = [r for r in SD._lines(args.starts) if r["k"] in plans_rows]
    jobs = [(r, s) for r in rows for s in (0, 1)]
    with _pool(args, plans_rows) as pool, \
            open(args.out, "w", encoding="utf-8") as fh, gzip.open(args.ends, "wt", encoding="utf-8") as fe:
        for n, (out, ends) in enumerate(pool.imap_unordered(_teacher_job, jobs), 1):
            fh.write(json.dumps(out) + "\n")
            for e in ends:
                fe.write(json.dumps(e, separators=(",", ":")) + "\n")
            if n % 200 == 0:
                print(f"{n}/{len(jobs)}", flush=True)
    print(f"{len(jobs)} 个（开头 × 种子）的老师 T 写进了 {args.out}，回合末写进了 {args.ends}")


def _gend_job(st_row):
    import time
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    k = st_row["k"]
    state, _ = TL._start_state(st_row)
    me = state.active
    plans_k = TL.PLANS[k]["plans"]
    out = {p["kind"]: [] for p in plans_k}
    failed = {p["kind"]: [] for p in plans_k}
    ends = []
    t = time.process_time()
    for j in range(st_row["K"]):
        sd = BANK + 40000 + 20 * k + j
        base = determinize(state, me, random.Random(sd))
        for p in plans_k:
            s = base.clone()
            taken = []
            keys = [TL._norm(x) for x in p["keys"]]
            failed[p["kind"]].append(TL.replay(s, me, keys, TL._veto(p["kind"]),
                                               TL.finisher(p["kind"], me, 10 * sd, taken), taken))
            end_summary_state = s.clone()
            if not s.over and s.active == me:
                apply(s, EndTurn())
            agents = {me: make_agent(TL.GEND_BOT, 10 * sd + 3), 1 - me: make_agent(TL.GEND_BOT, 10 * sd + 1)}
            while not s.over:
                apply(s, agents[s.active].act(s, legal_actions(s)))
            res = 1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5
            out[p["kind"]].append(res)
            ends.append(_end_row(st_row, me, None, j, sd, p["kind"], taken, res, end_summary_state))
    return ({"k": k, "K": st_row["K"], "split": st_row["split"], "cpu": time.process_time() - t,
             "results": out, "failed": failed}, ends)


def gend(args):
    plans_rows = {r["k"]: r for r in SD._lines(args.plans)}
    rows = [r for r in SD._lines(args.starts) if r["k"] in plans_rows]
    with _pool(args, plans_rows) as pool, \
            open(args.out, "w", encoding="utf-8") as fh, gzip.open(args.ends, "wt", encoding="utf-8") as fe:
        for n, (out, ends) in enumerate(pool.imap_unordered(_gend_job, rows), 1):
            fh.write(json.dumps(out) + "\n")
            for e in ends:
                fe.write(json.dumps(e, separators=(",", ":")) + "\n")
            if n % 50 == 0:
                print(f"{n}/{len(rows)}", flush=True)
    print(f"{len(rows)} 个开头的 G_end 写进了 {args.out}，回合末写进了 {args.ends}")


# --- labels (README "第 1 步", 标签; fixed before any step-1 data) -------------------------------------------

def _var(x):
    m = sum(x) / len(x)
    return sum((v - m) ** 2 for v in x) / max(len(x) - 1, 1)


NO_CONTRAST = {"step1": 0, "teacher_ends": 0}


def step1_pairs(starts_path, plans_path, teacher_path, gend_path):
    """Every kept plan other than the bot's against the bot's, at every start: {"k", "kind", "split", "dT": mean of
    the 16 determinizations' value(plan) - value(bot), "vT": their variance / 16, "dG": mean of the K paired
    result differences, "dG_dets": the K differences, "K"}."""
    st = {r["k"]: r for r in SD._lines(starts_path)}
    T, G = {}, {}
    for r in SD._lines(teacher_path):
        d = T.setdefault(r["k"], {})
        for kind, v in r["values"].items():
            d.setdefault(kind, {})[r["s"]] = v
    for r in SD._lines(gend_path):
        G[r["k"]] = r["results"]
    out = []
    for k in sorted(T):
        if k not in G or "bot" not in T[k]:
            continue
        for kind in T[k]:
            if kind == "bot" or kind not in G[k]:
                continue
            dt = [a - b for s in (0, 1) for a, b in zip(T[k][kind][s], T[k]["bot"][s])]
            dg = [a - b for a, b in zip(G[k][kind], G[k]["bot"])]
            if all(x == 0 for x in dt):           # the plan played as the bot's on every T determinization:
                NO_CONTRAST["step1"] += 1         # no contrast (as the teacher labels' rule, 02:38Z)
                continue
            out.append({"k": k, "kind": kind.split(":")[0], "plan": kind, "split": st[k]["split"],
                        "dT": sum(dt) / len(dt), "vT": _var(dt) / len(dt), "dG": sum(dg) / len(dg),
                        "dG_dets": dg, "K": len(dg)})
    return out


def calibrate(pairs):
    """On the training pairs without "end": b (dG = b x dT through the origin), the pooled per-determinization
    variance of the G_end differences s2G, and tau2, the variance of the true dG that b x dT misses (moments:
    mean (dG - b dT)^2 - mean s2G / K - b^2 mean vT; floored at TAU2_FLOOR)."""
    tr = [p for p in pairs if p["split"] == "train" and p["kind"] != "end"]
    b = sum(p["dT"] * p["dG"] for p in tr) / sum(p["dT"] ** 2 for p in tr)
    s2g = sum(_var(p["dG_dets"]) for p in tr) / len(tr)
    resid = sum((p["dG"] - b * p["dT"]) ** 2 for p in tr) / len(tr)
    noise = sum(s2g / p["K"] + b * b * p["vT"] for p in tr) / len(tr)
    tau2 = resid - noise
    return {"b": b, "s2G": s2g, "tau2": max(tau2, TAU2_FLOOR), "tau2_raw": tau2, "n": len(tr)}


def label_of(p, cal):
    """The pair's label on the win-probability scale and its weight: L = b dT + w (dG - b dT), w = tau2 / (tau2 +
    s2G / K); V = (1 - w)^2 (tau2 + b^2 vT) + w^2 s2G / K; weight 1 / V. A T-only pair (dG None): L = b dT,
    V = tau2 + b^2 vT."""
    b, tau2 = cal["b"], cal["tau2"]
    prior = b * p["dT"]
    vprior = tau2 + b * b * p["vT"]
    if p.get("dG") is None:
        return prior, 1.0 / vprior, 0.0
    vg = cal["s2G"] / p["K"]
    w = tau2 / (tau2 + vg)
    L = prior + w * (p["dG"] - prior)
    V = (1 - w) ** 2 * vprior + w * w * vg
    return L, 1.0 / V, w


def teacher_end_pairs(ends_path, positions_path):
    """The card-value teacher re-run (student_read/teacher_ends.jsonl.gz) as T-only pairs: per (position,
    restriction) over both seeds' determinizations, dT = mean of value(r) - value(line), vT = their variance /
    count; split by the student positions' (g % 11)."""
    split = {p["n"]: p["split"] for p in SD._lines(positions_path)}
    acc = {}
    for (n, s), d in TEN.groups(ends_path):
        line = d["line"]
        for r, rs in d.items():
            if r == "line":
                continue
            acc.setdefault((n, r), []).extend(x["value"] - b["value"] for x, b in zip(rs, line))
    out = []
    for (n, r), v in sorted(acc.items()):
        if all(x == 0 for x in v):                # the restriction changed nothing (02:38Z)
            NO_CONTRAST["teacher_ends"] += 1
            continue
        out.append({"k": n, "kind": r.split(":")[0], "plan": r, "split": split[n], "dT": sum(v) / len(v),
                    "vT": _var(v) / len(v), "dG": None, "K": 0})
    return out


def labels(args):
    """labels.jsonl: a header line with the calibration, then one line per pair (step 1's and the teacher
    re-run's) with its label, weight and split; the "end" pairs' weights scaled to END_SHARE of the step-1 pairs'
    total (training split)."""
    s1 = step1_pairs(args.starts, args.plans, args.teacher, args.gend)
    cal = calibrate(s1)
    rows = []
    for p in s1:
        L, W, w = label_of(p, cal)
        rows.append({"source": "step1", **{k: p[k] for k in ("k", "kind", "plan", "split", "dT", "dG", "K")},
                     "label": L, "weight": W, "w_G": w})
    tr = [r for r in rows if r["split"] == "train"]
    end_w = sum(r["weight"] for r in tr if r["kind"] == "end")
    rest_w = sum(r["weight"] for r in tr if r["kind"] != "end")
    scale = (END_SHARE / (1 - END_SHARE)) * rest_w / end_w if end_w > 0 else 1.0
    for r in rows:
        if r["kind"] == "end":
            r["weight"] *= scale
    if args.teacher_ends:
        for p in teacher_end_pairs(args.teacher_ends, args.positions):
            L, W, _ = label_of(p, cal)
            rows.append({"source": "teacher_ends", **{k: p[k] for k in ("k", "kind", "plan", "split", "dT")},
                         "dG": None, "K": 0, "label": L, "weight": W, "w_G": 0.0})
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"calibration": cal, "end_scale": scale}) + "\n")
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"校准（训练对、不含 end，{cal['n']} 对）：b = {cal['b']:.3f}，每局方差 {cal['s2G']:.3f}，"
          f"tau² = {cal['tau2_raw']:.5f}{'（撞下限）' if cal['tau2_raw'] < TAU2_FLOOR else ''}；end 的权重乘 {scale:.3f}")
    import numpy as np
    w = np.array([r["weight"] for r in rows if r["split"] == "train"])
    print(f"标签 {len(rows)} 个：第 1 步 {len(s1)}，老师重跑 {len(rows) - len(s1)}；没有可比、不进标签的：第 1 步 "
          f"{NO_CONTRAST['step1']}，老师重跑 {NO_CONTRAST['teacher_ends']}；训练标签权重的有效样本量占 "
          f"{w.sum() ** 2 / np.sum(w * w) / len(w):.1%}（建造线的 fit 有自己的等权退路）")


# --- the held-out reading (README "第 1 步", 留出; fixed before any step-1 data) -------------------------------

def _win(state, me, weights):
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import evaluate
    if state.over:
        return 1.0 if state.winner == me else 0.0 if state.winner == 1 - me else 0.5
    z = evaluate(state, me, weights, False)
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z / SCALE))))


def holdout(args):
    """On the held-out starts: for every kept plan against the bot's, dE = the mean over its determinizations (T's
    16 and G_end's 16) of sigma(E(the plan's turn end)) - sigma(E(the bot's)), E each evaluator's turn-end model
    (after the end-of-turn abilities, the opponent to move). The share of pairs where dE has dG_end's sign (dG_end
    = 0 left out; dE = 0 counts a half), and the same against dT; new and installed side by side, the difference
    with an interval by resampling starts (2000, seed 0). Without "end" first (the step-0 reading), then with it."""
    import numpy as np
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    specs = {"new": args.new, "installed": args.installed}
    W = {name: _search(make_agent(spec, 0)).weights for name, spec in specs.items()}
    val = {r["k"] for r in SD._lines(args.starts) if r["split"] == "val"}
    pairs = [p for p in step1_pairs(args.starts, args.plans, args.teacher, args.gend) if p["k"] in val]
    starts_ = TEN.Starts(args.selfplay)
    win = {}                                       # (k, plan, det) -> {evaluator: win probability}
    for path, tag in ((args.teacher_ends_s1, "T"), (args.gend_ends, "G")):
        for row in TEN.rows(path):
            if row["n"] not in val:
                continue
            st = TEN.turn_end(row, starts_, end_of_turn=True)
            win[(row["n"], row["r"], (tag, row["s"], row["j"]))] = {e: _win(st, row["seat"], W[e]) for e in W}
    per = []
    for p in pairs:
        dets = [d for (k, plan, d) in win if k == p["k"] and plan == p["plan"]]
        dE = {e: float(np.mean([win[(p["k"], p["plan"], d)][e] - win[(p["k"], "bot", d)][e] for d in dets
                                if (p["k"], "bot", d) in win])) for e in W}
        per.append({**p, "dE": dE})

    def agree(rows, e, target):
        got = [(1.0 if np.sign(r["dE"][e]) == np.sign(r[target]) else 0.5 if r["dE"][e] == 0 else 0.0)
               for r in rows if r[target] != 0]
        return float(np.mean(got)) if got else float("nan"), len(got)
    rng = np.random.default_rng(0)
    print("条件：对手卡表已知（牌序、手牌未知）。第 1 步留出读数（只报；判定看门）\n")
    print(f"- 新：`{args.new}`；现装：`{args.installed}`；留出开头 {len(val)} 个，对子 {len(per)} 个")
    for label, rows in (("不含 end", [r for r in per if r["kind"] != "end"]), ("含 end", per)):
        ks = sorted({r["k"] for r in rows})
        for target, name in (("dG", "ΔG_end（K = 16）"), ("dT", "ΔT")):
            a_new, n = agree(rows, "new", target)
            a_old, _ = agree(rows, "installed", target)
            bs = []
            for _ in range(2000):
                pick = rng.choice(ks, len(ks))
                sel = [r for k in pick for r in rows if r["k"] == k]
                bs.append(agree(sel, "new", target)[0] - agree(sel, "installed", target)[0])
            print(f"- {label}，和 {name} 同号：新 {a_new:.3f}、现装 {a_old:.3f}（{n} 对），新 − 现装 {a_new - a_old:+.3f}"
                  f"（{np.nanpercentile(bs, 2.5):+.3f}～{np.nanpercentile(bs, 97.5):+.3f}）")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("starts")
    a.add_argument("selfplay")
    a.add_argument("--out", required=True)
    for name in ("plans", "teacher", "gend"):
        a = sub.add_parser(name)
        a.add_argument("selfplay")
        a.add_argument("starts")
        if name != "plans":
            a.add_argument("plans")
            a.add_argument("--ends", required=True)
        a.add_argument("--out", required=True)
        a.add_argument("--workers", type=int, default=12)
    a = sub.add_parser("labels")
    a.add_argument("starts")
    a.add_argument("plans")
    a.add_argument("teacher")
    a.add_argument("gend")
    a.add_argument("--teacher-ends", default=None, help="analysis/card-value/student_read/teacher_ends.jsonl.gz")
    a.add_argument("--positions", default=None, help="the student data's positions.jsonl (its split)")
    a.add_argument("--out", required=True)
    a = sub.add_parser("holdout")
    a.add_argument("selfplay")
    a.add_argument("starts")
    a.add_argument("plans")
    a.add_argument("teacher")
    a.add_argument("gend")
    a.add_argument("teacher_ends_s1", help="step 1's teacher_ends.jsonl.gz")
    a.add_argument("gend_ends")
    a.add_argument("--new", required=True, help="the candidate's agent string")
    a.add_argument("--installed", default="v2s")
    for sp in sub.choices.values():
        sp.add_argument("--bank", type=int, default=BANK, help="the seed bank (another only for smoke tests)")
    args = ap.parse_args()
    _set_bank(args.bank)
    {"starts": starts, "plans": plans, "teacher": teacher, "gend": gend, "labels": labels,
     "holdout": holdout}[args.cmd](args)


if __name__ == "__main__":
    main()
