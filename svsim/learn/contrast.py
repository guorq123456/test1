"""Turn-level step 1: fit the turn-end evaluation E on contrasts between plans from the same turn start.

The architecture thread 2026-10-09 07:35Z (turn-level policy iteration): for two plans a, b of one turn start, a
teacher measures how much better a turns out than b (dT, a paired play-out difference in win probability); E
should agree: sigma(E(end of a)) - sigma(E(end of b)) ~ dT. The hand-value student's 11,035 teacher labels are such
pairs already (keep:c against the bot's line, the same start), once both turns are replayed to their ends.

Two parts:
- the trainer (`fit_contrast`): a linear E over the phased features (learn.features, version and named sets as
  learn.phased), loss = sum w (sigma(E(a)) - sigma(E(b)) - dT)^2 / sum w + mu x the log loss of game results on
  self-play turn ends (keeps E calibrated as a win probability) + l2 on the standardized coefficients; full-batch
  Adam, sign constraints as learn.fit. The intercept: given explicitly (learn.fit's bias column); with mu = 0 the
  contrasts barely see it (it moves both ends alike), so it is held at `fix_bias` (default 0, or the base model's).
  A network can stand in for the linear model later through the same loss (ContrastLinear's forward / backward);
  not written yet.
- the teacher's pairs, from the analysis line's re-run (`teacher_end_pairs`, the fit command's --teacher-ends:
  their teacher_ends.py's `pairs`, one machine and one run for labels and turn ends, per determinization or
  averaged over them); the features are the mover's and read nothing of the opponent's sampled hand (tested).
- the replay (`teacher_lines`, `replay_turn`, the `pairs` command; for the candidate generator's plans, and as a
  fallback): the teacher's lines for a turn start rebuilt as
  the teacher built them (analysis/card-value/teacher_eval.measure: CrossTurnAgent over mcts-raw:100+learned+phased,
  8 determinizations, each restriction re-searched with 100 iterations, the own next turn by a 30-iteration search,
  the row's seed), then each line played on the real position by its action keys up to the end of the turn; where a
  key no longer matches (a draw changed the hand), the bot finishes the turn under the restriction (its veto, which
  LethalAgent obeys since 842654e). Each pair keeps both turns' actions, so the turn ends replay from the record.

Condition: the opponent's deck list is known (order and hand not).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

TEACHER_SPEC = "mcts-raw:100+learned+phased"


# --- features -----------------------------------------------------------------------------------------------
def feature_names(version: int = 2, extras=()) -> list:
    from svsim.learn.features import extra_names, names
    return names(False, version) + extra_names(extras)


def features_of(state, player: int, version: int = 2, extras=(), hv=None) -> list:
    from svsim.learn.features import extra_features, features
    x = list(features(state, player, False, version))
    if extras:
        x += extra_features(state, player, extras, hv)
    return x


# --- the model ----------------------------------------------------------------------------------------------
def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


class ContrastLinear:
    """E(x) = w . (x - mean) / std, the bias column a constant 1 (index `bias`)."""

    def __init__(self, n: int, bias: int, mean, std):
        self.w = np.zeros(n)
        self.bias, self.mean, self.std = bias, np.asarray(mean, float), np.asarray(std, float)

    def standardize(self, X):
        return (np.asarray(X, float) - self.mean) / self.std

    def forward(self, Xs):
        return Xs @ self.w

    def backward(self, Xs, dz):
        return Xs.T @ dz


def contrast_loss(model: ContrastLinear, A, B, dT, w, C=None, y=None, mu: float = 0.0, l2: float = 0.0,
                  fixed=None):
    """(loss, gradient) of the weighted squared contrast error, plus mu x calibration log loss, plus l2 (not on
    the bias); `fixed`: coefficient indices held where they are (zero gradient)."""
    za, zb = model.forward(A), model.forward(B)
    pa, pb = _sigmoid(za), _sigmoid(zb)
    d = pa - pb - dT
    W = float(np.sum(w))
    loss = float(np.sum(w * d * d)) / W
    g = model.backward(A, 2 * w * d * pa * (1 - pa) / W) - model.backward(B, 2 * w * d * pb * (1 - pb) / W)
    if C is not None and mu > 0 and len(C):
        zc = model.forward(C)
        loss += mu * float(np.mean(np.logaddexp(0, zc) - y * zc))
        g = g + mu * model.backward(C, (_sigmoid(zc) - y) / len(C))
    mask = np.ones_like(model.w)
    mask[model.bias] = 0.0
    loss += l2 * float(np.sum((model.w * mask) ** 2))
    g = g + 2 * l2 * model.w * mask
    if fixed is not None:
        g[list(fixed)] = 0.0
    return loss, g


def start_from(model, coef, mean, std, bias: int) -> np.ndarray:
    """Another linear model's coefficients (coef over (x - mean) / std, its bias at the same index) in `model`'s
    standardization: the same E(x), so a fit can start where that model is."""
    coef, mean, std = (np.asarray(v, float) for v in (coef, mean, std))
    w = coef * model.std / std
    others = np.arange(len(coef)) != bias
    w[bias] = coef[bias] + float(np.sum((coef * (model.mean - mean) / std)[others]))
    return w


def fit_contrast(XA, XB, dT, w=None, XC=None, yc=None, mu: float = 0.1, l2: float = 1e-3, iters: int = 3000,
                 lr: float = 0.05, signs=None, bias: int = -1, fix_bias: float | None = None, keep=None,
                 init=None):
    """(ContrastLinear, report). XA / XB: the two turn ends' features per pair; dT: the teacher's difference (a
    minus b); w: pair weights (default 1); XC / yc: calibration turn ends and their game results (mu > 0).
    The intercept is fitted only with calibration data; with mu = 0 (or none) it is held at `fix_bias` (default 0).
    `keep`: a 0/1 mask of features to use (learn.phased.STOCK zeroed). `init`: (coef, mean, std) of a model to
    start from (start_from; e.g. the installed turn-end model), else zeros."""
    from svsim.learn.fit import project, standardize
    XA, XB = np.asarray(XA, float), np.asarray(XB, float)
    n = XA.shape[1]
    bias = bias % n
    keep = np.ones(n) if keep is None else np.asarray(keep, float)
    pool = np.vstack([XA, XB] + ([np.asarray(XC, float)] if XC is not None and len(XC) else []))
    mean, std = standardize(pool * keep, bias)
    model = ContrastLinear(n, bias, mean, std)
    A, B = model.standardize(XA * keep), model.standardize(XB * keep)
    C = model.standardize(np.asarray(XC, float) * keep) if XC is not None and len(XC) else None
    y = np.asarray(yc, float) if yc is not None else None
    dT = np.asarray(dT, float)
    w = np.ones(len(dT)) if w is None else np.asarray(w, float)
    calibrated = C is not None and mu > 0
    fixed = [i for i in range(n) if keep[i] == 0 and i != bias]
    if init is not None:
        model.w = start_from(model, *init, bias) * np.where(np.arange(n) == bias, 1.0, keep)
    if not calibrated:
        model.w[bias] = 0.0 if fix_bias is None else fix_bias
        fixed.append(bias)
    m, v = np.zeros(n), np.zeros(n)
    for t in range(1, iters + 1):
        loss, g = contrast_loss(model, A, B, dT, w, C, y, mu, l2, fixed)
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * g * g
        model.w -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
        if signs is not None:
            held = model.w[bias]
            model.w = project(model.w, signs)
            model.w[bias] = held
    loss, _ = contrast_loss(model, A, B, dT, w, C, y, mu, l2)
    pa, pb = _sigmoid(model.forward(A)), _sigmoid(model.forward(B))
    report = {"loss": loss, "pairs": len(dT), "calibration_rows": 0 if C is None else len(C),
              "contrast_mse": float(np.sum(w * (pa - pb - dT) ** 2) / np.sum(w)),
              "sign_agreement": float(np.mean(np.sign(pa - pb) == np.sign(dT))), "intercept_fitted": calibrated}
    return model, report


def to_linear_value(model: ContrastLinear, version: int, extras, info: dict):
    """The fitted E as a learn.model.LinearValue (a turn-end model learn.phased.load reads)."""
    from svsim.learn.model import LinearValue
    return LinearValue([float(x) for x in model.w], [float(x) for x in model.mean], [float(x) for x in model.std],
                       False, info, version=version, extras=tuple(extras))


# --- replaying turns ----------------------------------------------------------------------------------------
def replay_turn(state, keys: list, fallback=None) -> tuple:
    """Play the turn of the player to act on a copy, following `keys` (search.mcts.action_key, as principal_line
    gives them) while one matches a legal action, ending the turn at ("T",); then fallback(state, legal) (default:
    end the turn). (actions, turn end: search.evaluate.after_end_of_turn)."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.search.evaluate import after_end_of_turn
    from svsim.search.mcts import _locator, action_key
    s = state.clone()
    me, actions, pending, following = s.active, [], list(keys), True
    while not s.over and s.active == me and s.phase == Phase.MAIN:
        legal = legal_actions(s)
        a = None
        if following and pending:
            want = pending.pop(0)
            if tuple(want) == ("T",):
                a = EndTurn()
            else:
                where = _locator(s, me)
                a = next((x for x in legal if action_key(s, x, where) == tuple(want)), None)
                if a is None:
                    following = False
        if a is None:
            a = fallback(s, legal) if fallback is not None else EndTurn()
        actions.append(a)
        if isinstance(a, EndTurn):
            return actions, after_end_of_turn(s)
        apply(s, a)
    return actions, s


def _freeze(keys):
    """Keys (nested tuples) as JSON-friendly lists, and back with _thaw."""
    return json.loads(json.dumps(keys))


def _thaw(k):
    return tuple(_thaw(x) for x in k) if isinstance(k, list) else k


def teacher_lines(state, seed: int, samples: int = 8, research: int = 100, next_search: int = 30,
                  opp_search: int = 0, spec: str = TEACHER_SPEC) -> dict:
    """{restriction: keys} as the teacher built them for this turn start and seed (teacher_eval.measure)."""
    from svsim.agents.crossturn_agent import CrossTurnAgent, principal_line, restrictions
    from svsim.tools.arena import make_agent
    extra = {"research": research} if research else {}
    if next_search or opp_search:
        extra.update(next_search=next_search, opp_search=opp_search)
    agent = CrossTurnAgent(make_agent(spec, seed), samples=samples, seed=seed, next_turn=True, **extra)
    agent.search.choose(state)
    line = principal_line(agent.search.last_root)
    cands = restrictions(line)
    return agent.lines_for(state, line, cands) if research else {r: line for r in cands}


def bot_fallback(spec: str, seed: int, restriction: str):
    """The bot finishing a turn under a restriction (its veto on the inner search)."""
    from svsim.agents.crossturn_agent import forbids
    from svsim.search.candidates import _agent_decider
    return _agent_decider(spec, seed, forbids(restriction) if restriction != "line" else None)


def pairs_for_position(state, rows: list, spec_bot: str = "v2s", **teacher_kw) -> list:
    """The contrast pairs of one turn start from its teacher rows (one per seed, teacher.jsonl's "res"): for each
    keep:<card> of a card in hand at the start (and not 'changed nothing', learn.handvalue._no_change), per seed,
    {"seed", "restriction", "dT", "se", "a": the restricted turn's actions, "b": the line's}."""
    from svsim.core.actions import to_dict
    from svsim.learn.handvalue import _no_change
    me = state.active
    held = {c.defn.card_id for c in state.players[me].hand}
    out = []
    for row in rows:
        keeps = [k for k in row["res"] if k.startswith("keep:") and int(k.split(":")[1]) in held
                 and not _no_change([row], int(k.split(":")[1]))]
        if not keeps:
            continue
        lines = teacher_lines(state, row["seed"], **teacher_kw)
        line_actions, _ = replay_turn(state, lines.get("line", []), bot_fallback(spec_bot, row["seed"], "line"))
        for r in keeps:
            if r not in lines:
                continue
            acts, _ = replay_turn(state, lines[r], bot_fallback(spec_bot, row["seed"], r))
            out.append({"seed": row["seed"], "restriction": r, "dT": row["res"][r]["teacher"],
                        "se": row["res"][r].get("se"), "a": [to_dict(a) for a in acts],
                        "b": [to_dict(a) for a in line_actions]})
    return out


def turn_end_of(record, at: int, actions: list):
    """The turn end reached from a record's position before action `at` by `actions` (to_dict form)."""
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools import records as R
    s = R.start(record)
    for a in record["actions"][:at]:
        apply(s, from_dict(a))
    for d in actions:
        a = from_dict(d)
        if isinstance(a, EndTurn):
            return after_end_of_turn(s)
        apply(s, a)
    return s


def _teacher_ends_module(analysis_dir):
    """The analysis line's analysis/card-value/teacher_ends.py (and its student_data.py) from a folder."""
    import importlib
    import sys
    folder = str(Path(analysis_dir).resolve())
    if folder not in sys.path:
        sys.path.insert(0, folder)
    return importlib.import_module("teacher_ends")


def teacher_end_pairs(ends, selfplay, positions, module=None, analysis_dir=None, mode: str = "det",
                      hold_out_every: int = 11, split: str = "train", version: int = 2, extras=(), hv=None):
    """Contrast items from the analysis line's teacher re-run (teacher_ends.jsonl.gz; their `pairs` and `Starts`,
    turn ends with the end-of-turn abilities resolved, as the ENDED model sees them): (start n, g, features of the
    restricted line's end a, of the principal line's end b, dT, weight). mode "det": one item per determinization
    (their default, determinizations where both lines took the same actions left out); "mean": one per (position,
    seed, restriction), dT the mean over all 8 determinizations (identical ones included, as the teacher's T), with
    the first determinization's pair whose actions differ (none: left out). Pairs with a turn end where the game
    is over (a lethal during the turn; their turn_end returns it as it is since 9999f81) are left out: the
    evaluation gives the result there, not E. The features are the mover's
    (positions.jsonl's seat). split: "train" (games g % hold_out_every != 0), "val" (== 0) or None (both)."""
    TE = module if module is not None else _teacher_ends_module(analysis_dir)
    starts = TE.Starts(selfplay)
    pos = {}
    for line in open(positions, encoding="utf-8"):
        if line.strip():
            p = json.loads(line)
            pos[p["n"]] = (p["g"], p["seat"])

    def wanted(g):
        if split is None or not hold_out_every:
            return True
        return (g % hold_out_every == 0) == (split == "val")

    def item(n, a, b, dT, w):
        g, seat = pos[n]
        return n, g, features_of(a, seat, version, extras, hv), features_of(b, seat, version, extras, hv), dT, w

    if mode == "det":
        for it in TE.pairs(ends, starts, end_of_turn=True):
            if it["a"].over or it["b"].over:           # the game ended during the turn: E is not asked there
                continue
            if wanted(pos[it["start"]][0]):
                yield item(it["start"], it["a"], it["b"], it["dT"], it["weight"])
        return
    if mode != "mean":
        raise ValueError(f"unknown mode {mode!r}")
    key, group = None, []

    def flush(group):
        diffs = [it["dT"] for it in group]
        pick = next((it for it in group if not (it["a"].over or it["b"].over) and not _same_end(it)), None)
        if pick is not None and wanted(pos[pick["start"]][0]):
            return item(pick["start"], pick["a"], pick["b"], sum(diffs) / len(diffs), 1.0)
        return None
    for it in TE.pairs(ends, starts, end_of_turn=True, keep_same=True):
        k = (it["start"], it["s"], it["r"])
        if k != key and group:
            out = flush(group)
            if out is not None:
                yield out
            group = []
        key = k
        group.append(it)
    if group:
        out = flush(group)
        if out is not None:
            yield out


def _same_end(it) -> bool:
    from svsim.search.lethal import state_key
    return state_key(it["a"]) == state_key(it["b"])


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pairs", help="teacher labels -> contrast pairs (JSON lines), the teacher's lines replayed")
    p.add_argument("--selfplay", required=True)
    p.add_argument("--positions", required=True)
    p.add_argument("--teacher", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int, default=None, help="the first N positions only (smoke runs)")
    p.add_argument("--workers", type=int, default=1)
    f = sub.add_parser("fit", help="pairs (+ self-play calibration) -> a candidate folder's turn-end model")
    f.add_argument("--pairs", default=None, help="this module's pairs (JSON lines); or --teacher-ends")
    f.add_argument("--teacher-ends", default=None, help="the analysis line's teacher_ends.jsonl.gz")
    f.add_argument("--analysis-dir", default=None, help="the folder with their teacher_ends.py and student_data.py")
    f.add_argument("--positions", default=None, help="positions.jsonl (the movers, the games), with --teacher-ends")
    f.add_argument("--mode", default="det", choices=("det", "mean"),
                   help="with --teacher-ends: a pair per determinization (det), or dT averaged over them (mean)")
    f.add_argument("--selfplay", required=True)
    f.add_argument("--matchup", default="ramp-ramp")
    f.add_argument("--out", required=True)
    f.add_argument("--act-from", default=None, help="a models folder whose in-turn model is copied (act unchanged)")
    f.add_argument("--mu", type=float, default=0.1, help="weight of the calibration log loss")
    f.add_argument("--l2", type=float, default=1e-3)
    f.add_argument("--iters", type=int, default=3000)
    f.add_argument("--hold-out-every", type=int, default=11)
    f.add_argument("--features", default="")
    args = parser.parse_args()
    if args.cmd == "pairs":
        _pairs_command(args)
    else:
        _fit_command(args)


def _load_lines(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def _pairs_job(job):
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    from svsim.tools import records as R
    record, pos, rows = job
    s = R.start(record)
    for a in record["actions"][:pos["at"]]:
        apply(s, from_dict(a))
    return [dict(p, n=pos["n"], g=pos["g"], at=pos["at"], player=pos["seat"], split=pos.get("split"))
            for p in pairs_for_position(s, rows)]


def _pairs_command(args):
    from multiprocessing import Pool
    games = {r["g"]: r for r in _load_lines(args.selfplay)}
    pos = {p["n"]: p for p in _load_lines(args.positions)}
    rows: dict = {}
    for r in _load_lines(args.teacher):
        rows.setdefault(r["n"], []).append(r)
    ns = sorted(rows)[:args.limit] if args.limit else sorted(rows)
    jobs = [(games[pos[n]["g"]], pos[n], rows[n]) for n in ns]
    with open(args.out, "w", encoding="utf-8") as out, Pool(args.workers) as pool:
        for part in pool.imap(_pairs_job, jobs, chunksize=1):
            for p in part:
                out.write(json.dumps(p) + "\n")


def _fit_command(args):
    import hashlib
    import shutil
    from svsim.learn.features import signs
    from svsim.learn.netdata import ENDED, rows as replay_rows
    from svsim.learn.phased import STOCK
    extras = tuple(e for e in args.features.split(",") if e)
    names = feature_names(2, extras)
    games = {r["g"]: r for r in _load_lines(args.selfplay)}
    k = args.hold_out_every
    XA, XB, dT, w = [], [], [], []
    if args.teacher_ends:
        for _, _, xa, xb, d, wt in teacher_end_pairs(args.teacher_ends, args.selfplay, args.positions,
                                                     analysis_dir=args.analysis_dir, mode=args.mode,
                                                     hold_out_every=k, split="train", extras=extras):
            XA.append(xa)
            XB.append(xb)
            dT.append(d)
            w.append(wt)
        source = args.teacher_ends
    else:
        for p in (p for p in _load_lines(args.pairs) if not (k and p["g"] % k == 0)):
            a = turn_end_of(games[p["g"]], p["at"], p["a"])
            b = turn_end_of(games[p["g"]], p["at"], p["b"])
            XA.append(features_of(a, p["player"], 2, extras))
            XB.append(features_of(b, p["player"], 2, extras))
            dT.append(p["dT"])
            w.append(1.0)
        source = args.pairs
    XC, yc = [], []
    for g, rec in games.items():
        if k and g % k == 0:
            continue
        for phase, me, st, result in replay_rows(rec):
            if phase == ENDED and result != 0.5:
                XC.append(features_of(st, me, 2, extras))
                yc.append(result)
    keep = [0.0 if n.startswith(STOCK) else 1.0 for n in names]
    model, report = fit_contrast(XA, XB, dT, w, XC, yc, mu=args.mu, l2=args.l2, iters=args.iters,
                                 signs=list(signs(False, 2)) + [0] * (len(names) - len(signs(False, 2))),
                                 bias=names.index("bias"), keep=keep)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    info = {"moment": "ended", "contrast": True, "mu": args.mu, "l2": args.l2, "iters": args.iters,
            "hold_out_every": k, "pairs": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
            "pairs_from": "teacher_ends" if args.teacher_ends else "pairs", "mode": args.mode,
            "selfplay": hashlib.sha256(Path(args.selfplay).read_bytes()).hexdigest(), "report": report}
    to_linear_value(model, 2, extras, info).save(out / f"{args.matchup}-ended.json")
    if args.act_from:
        from svsim.learn.phased import folder_of
        shutil.copy(folder_of(args.act_from) / f"{args.matchup}-act.json", out / f"{args.matchup}-act.json")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
