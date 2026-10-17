"""The move prior's offline report (the architecture thread 2026-10-17 11:37Z, step 1; learn.setpolicy).

On a held-out self-play shard, at every searched decision with two distinct moves or more (learn.setpolicy.decisions:
moves that are the same to the search are one move, the target is the root's visit distribution over them), each
method gives an order of the distinct moves and, where it has one, a distribution:
- uniform: every move the same (its figures are the expected ones of a random order);
- order: the search's own expansion order now (search.mcts.ISMCTS._options without a prior, the recorded
  player's settings), an order only;
- old: the earlier policy head (learn.policy.PolicyNet, svsim/learn/policies/ramp-ramp.npz: the old Ramp mirror,
  linear evaluator, card one-hot), its legal moves' probabilities added per distinct move as the search's root does;
- each learned prior given (learn.setpolicy.SetPolicy.priors, added per distinct move the same way).

Figures, over all decisions and split into the turn's first decision / the rest:
- top1: the method's first move is a most-visited move;
- top2: the visit share of the method's first two moves;
- ce, kl: cross entropy -sum pi log q and KL(pi || q) (methods with a distribution);
- end: over decisions where ending the turn is a move, how often the method's first move is "end" exactly when the
  search's most-visited move is (and how often the search's is).

With --dump, a jsonl.gz row per decision: seed, g, i (the action's index), start, visits (per legal move, as
recorded), priors (each method's probability per legal move, legal_actions order) and order (the expansion order
as legal-move indices, one per action key: the first legal move with that key).

    python analysis/scaling/policy_offline.py --records REC --spec SPEC --prior NAME=PATH ... [--old PATH] --out OUT
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from svsim.learn import setpolicy as SP  # noqa: E402


class _Acc:
    def __init__(self):
        self.n = 0
        self.top1 = self.top2 = self.ce = self.kl = 0.0
        self.end_n = self.end_agree = self.end_search = 0.0

    def add(self, pi, order, q, end, hit=None, cover=None, end_hit=None):
        self.n += 1
        self.top1 += pi[order[0]] >= pi.max() - 1e-12 if hit is None else hit
        self.top2 += pi[order[:2]].sum() if cover is None else cover
        if q is not None:
            ce = -float(np.sum(pi * np.log(np.maximum(q, 1e-12))))
            h = -float(np.sum(pi[pi > 0] * np.log(pi[pi > 0])))
            self.ce += ce
            self.kl += ce - h
        if end is not None:
            search_end = pi[end] >= pi.max() - 1e-12
            self.end_n += 1
            self.end_search += search_end
            self.end_agree += ((order[0] == end) == search_end) if end_hit is None else end_hit(search_end)

    def out(self, dist: bool) -> dict:
        r = {"decisions": self.n, "top1": round(self.top1 / self.n, 4), "top2": round(self.top2 / self.n, 4)}
        if dist:
            r.update(ce=round(self.ce / self.n, 4), kl=round(self.kl / self.n, 4))
        if self.end_n:
            r.update(end_decisions=int(self.end_n), end_agree=round(self.end_agree / self.end_n, 4),
                     search_ends=round(self.end_search / self.end_n, 4))
        return r


def _per_move(probs, group, n):
    q = np.zeros(n)
    np.add.at(q, group, probs)
    return q


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True, help="a held-out rec-<seed>.jsonl.gz")
    ap.add_argument("--spec", required=True, help="the recorded player (for the search's expansion order)")
    ap.add_argument("--prior", action="append", default=[], metavar="NAME=PATH")
    ap.add_argument("--old", default=None, help="learn.policy PolicyNet file (the old head)")
    ap.add_argument("--games", type=int, default=0, help="only the first N games (0: all)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dump", default=None, help="a jsonl.gz with one row per decision (the analysis line's recheck)")
    args = ap.parse_args()
    from svsim.core.actions import EndTurn
    from svsim.learn.netdata import _search
    from svsim.learn.policy import PolicyNet
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    search = _search(make_agent(args.spec, 0))
    priors = {name: SP.SetPolicy.load(path) for name, path in (p.split("=", 1) for p in args.prior)}
    old = PolicyNet.load(Path(args.old)) if args.old else None
    methods = ["uniform", "order"] + (["old"] if old else []) + list(priors)
    acc = {m: {part: _Acc() for part in ("all", "first", "rest")} for m in methods}
    games = 0
    dump = gzip.open(args.dump, "wt") if args.dump else None
    with gzip.open(args.records, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            games += 1
            for i, state, legal, reps, group, pi, start in SP.decisions(rec):
                me, n = state.active, len(reps)
                where = _locator(state, me)
                keys = [action_key(state, a, where) for a in reps]
                end = next((j for j, a in enumerate(reps) if isinstance(a, EndTurn)), None)
                parts = ("all", "first" if start else "rest")
                expected_max = float(np.sum(pi >= pi.max() - 1e-12))
                for part in parts:
                    acc["uniform"][part].add(pi, np.arange(n), np.full(n, 1.0 / n), end, hit=expected_max / n,
                                             cover=min(2, n) / n,
                                             end_hit=lambda s, n=n: (1.0 / n) if s else (1 - 1.0 / n))
                tried = list(search._options(state, me, None))
                order = [keys.index(k) for k in tried if k in keys]
                order += [j for j in range(n) if j not in order]
                for part in parts:
                    acc["order"][part].add(pi, np.asarray(order), None, end)
                dists, raw = {}, {}
                if old is not None:
                    raw["old"] = old.priors(state, legal)
                for name, pol in priors.items():
                    raw[name] = pol.priors(state, legal)
                for name, pr in raw.items():
                    dists[name] = _per_move(pr, group, n)
                if dump is not None:                  # per legal move, as recorded; order: legal indices, one a key
                    first = [group.index(j) for j in range(n)]
                    dump.write(json.dumps({"seed": int(rec["seed"]) // 100003, "g": rec["g"], "i": i,
                                           "start": bool(start), "visits": rec["search"][i]["visits"],
                                           "priors": {k: [float(x) for x in v] for k, v in raw.items()},
                                           "order": [first[j] for j in order]}) + "\n")
                for name, q in dists.items():
                    o = np.argsort(-q, kind="stable")
                    for part in parts:
                        acc[name][part].add(pi, o, q, end)
            if args.games and games >= args.games:
                break
    if dump is not None:
        dump.close()
    report = {"records": Path(args.records).name, "games": games, "spec": args.spec,
              "priors": {name: str(path) for name, path in (p.split("=", 1) for p in args.prior)},
              "old": args.old,
              "methods": {m: {part: acc[m][part].out(m not in ("order",)) for part in acc[m]} for m in methods}}
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
