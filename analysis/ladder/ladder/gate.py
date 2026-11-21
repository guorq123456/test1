"""The gate (phase 1, item 1.7; plan 检验口径): does a member's new strategy version replace the old one?

    python -m ladder.gate run FROZEN.json --member MID --new SPEC --old SPEC --kind better|noninf|same|fixed
                          --change "what changed" --prediction "expected gap and why" --seeds LO HI --out DIR
                          [--delta 2] [--share 0.4] [--pairs N] [--workers 11 --mask 0x3FC3FC]
                          [--resubmit-of G-xxxx --what-changed-since "..."]
    python -m ladder.gate selfcheck [--sims 2000]

How a pair is played: the new and the old version each play one game against the same frozen opponent, with the
same seed, in the same seat (so the same deal and the same first player), with the same strategy seeds on both
sides. Seats alternate pair by pair (half each). The opponent is drawn from the frozen pool (the member itself left
out) with the matching the member meets on the ladder (pool.pick_opponent from the member's CR). A pair with the
same result twice is concordant and skipped; a discordant pair counts, "won" when the new version won it. A crash,
illegal move or timeout loses for the side that made it; a void game (no one to blame) voids its pair, and if more
than 2% of the pairs are void the whole gate is invalid (A24).

Kinds:
- better (an update meant to improve): SPRT on the discordant pairs, H0 gap 0, H1 gap +delta pp (default 2; 3-5
  early, 1.5 late: fixed before the run), alpha = beta = 0.05. The gap is turned into the share of discordant pairs
  the new version wins: 0.5 + gap / (2 * discordant share). The discordant share is the member's last measured one,
  or (first gate) measured on a separate 200 pairs first and then fixed (A23: those 200 don't count in the test).
  The expected number of pairs under H1 is worked out before the run; at 3 times that with no decision: undecided,
  which counts as not passed. Two versions that play alike (no discordant pair in the first 200) stop there with
  "no difference" instead of running to the cap.
- noninf (refactor, speed-up, simplification whose decisions changed): the same test with H0 gap -2, H1 gap 0.
- same (a change that should not change any decision): every decision of both versions over `--pairs` pairs
  (default 100) must match exactly. Passing needs no statistics. If one differs, it is a noninf case.
- fixed (cumulative confirmation, spot re-tests): `--pairs` pairs (2000 for a confirmation), no stopping; the gap
  with a 95% interval, overall and by the opponent's class.

Every gate needs a prediction line before it runs (what changed, expected gap, why); a change is gated once: the same
member and new version a second time is refused unless `--resubmit-of` names the earlier gate and says what changed
in substance. Seeds are drawn at random from the gate range given, never one any earlier gate in this ledger used.
The per-step compute of the member's side, new over old, is reported; above 1.08 the gate is invalid (unequal
compute), unless compute is what the gate compares (`--compute-is-the-point`).

The ledger: DIR/../gates.jsonl (one line per gate, append-only, passed or not) and a row in GATES.md.

Built here and not in svsim/tools/gate.py, which the plan names as the starting point: that tool runs agents on the
full real state (it peeks under this task's information condition) and its test counts concordant pairs; changing
it would change the simulator package. Its idea (paired seeds, seat swap, SPRT, resumable files) is kept (D4).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for p in (str(ROOT), str(HERE.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from ladder.evaluator import Candidate, load_frozen, opponents_for  # noqa: E402
from ladder.leaderboard import t975  # noqa: E402
from ladder.pool import CRAFT_ZH, PoolError, pick_opponent  # noqa: E402

ALPHA = BETA = 0.05
COMPUTE_RATIO = 1.08
VOID_LIMIT = 0.02
CAP_FACTOR = 3
PRE_PAIRS = 200
SAME_AFTER = 200                              # this many pairs with no discordant one: the versions play alike
LEDGER_DIR = HERE.parent                      # gates.jsonl and GATES.md live in analysis/ladder/


# --- the test itself (pure; the self-check runs it on made-up sequences) -----------------------------------

def p_of_gap(gap_pp: float, share: float) -> float:
    """The share of discordant pairs the new version wins, for a win-rate gap (pp) and a discordant share."""
    p = 0.5 + (gap_pp / 100) / (2 * share)
    if not 0 < p < 1:
        raise ValueError(f"a gap of {gap_pp} pp can't happen with a discordant share of {share}")
    return p


def kl(p1: float, p0: float) -> float:
    return p1 * math.log(p1 / p0) + (1 - p1) * math.log((1 - p1) / (1 - p0))


def expected_pairs(p0: float, p1: float, share: float, alpha=ALPHA, beta=BETA) -> float:
    """Wald's approximation of the mean number of pairs (all pairs, not only discordant) when H1 holds."""
    a, b = math.log((1 - beta) / alpha), math.log(beta / (1 - alpha))
    return ((1 - beta) * a + beta * b) / kl(p1, p0) / share


class SPRT:
    def __init__(self, p0: float, p1: float, alpha=ALPHA, beta=BETA):
        self.p0, self.p1 = p0, p1
        self.upper, self.lower = math.log((1 - beta) / alpha), math.log(beta / (1 - alpha))
        self.win_step, self.loss_step = math.log(p1 / p0), math.log((1 - p1) / (1 - p0))
        self.llr, self.wins, self.losses = 0.0, 0, 0

    def add(self, new_won: bool) -> str | None:
        if new_won:
            self.wins += 1
            self.llr += self.win_step
        else:
            self.losses += 1
            self.llr += self.loss_step
        if self.llr >= self.upper:
            return "H1"
        if self.llr <= self.lower:
            return "H0"
        return None


def simulate(gap_pp: float, h0: float, h1: float, share: float, sims: int, seed: int) -> dict:
    """Made-up pairs with a true gap: how often the test accepts H1, and the mean pairs to a decision."""
    rng = random.Random(seed)
    p0, p1 = p_of_gap(h0, share), p_of_gap(h1, share)
    true_p = p_of_gap(gap_pp, share)
    cap = CAP_FACTOR * expected_pairs(p0, p1, share)
    accept, undecided, pairs = 0, 0, []
    for _ in range(sims):
        t, n, verdict = SPRT(p0, p1), 0, None
        while verdict is None and n < cap:
            n += 1
            if rng.random() < share:
                verdict = t.add(rng.random() < true_p)
        accept += verdict == "H1"
        undecided += verdict is None
        pairs.append(n)
    return {"true_gap": gap_pp, "accept_h1": accept / sims, "undecided": undecided / sims,
            "mean_pairs": sum(pairs) / sims, "expected_pairs_h1": expected_pairs(p0, p1, share)}


# --- the ledger ----------------------------------------------------------------------------------------------

def ledger_path(root: Path = LEDGER_DIR) -> Path:
    return root / "gates.jsonl"


def read_ledger(root: Path = LEDGER_DIR) -> list[dict]:
    p = ledger_path(root)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def append_ledger(rec: dict, root: Path = LEDGER_DIR):
    with ledger_path(root).open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    md = root / "GATES.md"
    if not md.exists():
        md.write_text(GATES_HEADER, encoding="utf-8")
    row = (f"| {rec['gate']} | {rec['date']} | {rec.get('anon', rec['member'])} | {rec['kind']} | {rec['change']} | "
           f"{rec['prediction']} | {rec.get('hypotheses', '')} | {rec['seed_note']} | {rec['opponents_note']} | "
           f"{rec.get('compute_ratio', '')} | {rec['verdict']} | {rec.get('estimate_note', '')} | "
           f"{rec.get('resubmit_of') or ''} |\n")
    with md.open("a", encoding="utf-8") as f:
        f.write(row)


GATES_HEADER = """# 检验台账

每次检验一行，由检验工具（ladder/gate.py）自动写入，机器可读的全文在 gates.jsonl。只增不改，没通过的也记。同一个改动没有实质修改，不重新检验。

| 编号 | 日期 | 成员（匿名编号） | 类型 | 改了什么 | 事先的预测 | 假设 | 种子 | 对手构成 | 每步 CPU 之比（新 / 旧） | 结果 | 估计 | 指回 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
"""


# --- one gate on real games --------------------------------------------------------------------------------

class Gate:
    def __init__(self, frozen_path, member: str, new: str, old: str, kind: str, change: str, prediction: str,
                 seeds, out_dir, delta: float = 2.0, share: float | None = None, pairs: int | None = None,
                 resubmit_of: str | None = None, since: str = "", compute_is_the_point: bool = False,
                 ledger_root: Path = LEDGER_DIR, rng_seed: int | None = None):
        if kind not in ("better", "noninf", "same", "fixed"):
            raise PoolError(f"unknown kind {kind}")
        if not change.strip() or not prediction.strip():
            raise PoolError("a gate needs the change and the prediction written before it runs")
        self.ledger_root = Path(ledger_root)
        ledger = read_ledger(self.ledger_root)
        earlier = [r for r in ledger if r["member"] == member and r["new"] == new and r["kind"] == kind]
        if earlier and not (resubmit_of and since.strip()):
            raise PoolError(f"this change was gated already ({earlier[-1]['gate']}); a resubmission names it and "
                            "says what changed in substance")
        self.frozen, self.body = load_frozen(frozen_path)
        me = next((f for f in self.frozen if f.mid == member), None)
        if me is None:
            raise PoolError(f"{member} is not in the frozen pool")
        self.me = me
        self.others, self.mu = opponents_for(self.frozen, member)
        self.cand = Candidate(member, me.craft, me.deck, new, cr=me.cr)
        self.kind, self.new, self.old, self.delta = kind, new, old, delta
        self.change, self.prediction, self.resubmit_of, self.since = change, prediction, resubmit_of, since
        self.compute_is_the_point = compute_is_the_point
        self.lo, self.hi = seeds
        self.used = {s for r in ledger for s in r.get("seeds_used", [])}
        self.gid = f"G-{len(ledger) + 1:04d}"
        self.dir = Path(out_dir) / self.gid
        self.dir.mkdir(parents=True, exist_ok=True)
        self.rng_seed = rng_seed if rng_seed is not None else time.time_ns() % 2 ** 48
        self.rng = random.Random(self.rng_seed)
        self.pairs_target = pairs or {"same": 100, "fixed": 2000}.get(kind)
        last_share = next((r["discordant_share"] for r in reversed(ledger)
                           if r["member"] == member and r.get("discordant_share")), None)
        self.share = share or last_share
        self.results: dict[str, dict] = {}
        self.pairs: list[dict] = []
        self.seeds_used: list[int] = []

    # one pair = two jobs
    def _pair(self, i: int, tag: str) -> list[dict]:
        opp, how = pick_opponent(self.cand, self.others, self.mu, self.rng, cr=self.me.cr)
        while True:
            seed = self.rng.randrange(self.lo, self.hi)
            if seed not in self.used:
                break
        self.used.add(seed)
        self.seeds_used.append(seed)
        seat = i % 2
        sseeds = [self.rng.randrange(1, 2 ** 31), self.rng.randrange(1, 2 ** 31)]
        pair = {"i": i, "tag": tag, "seed": seed, "seat": seat, "opp": opp.mid, "opp_craft": opp.craft,
                "ids": {}}
        jobs = []
        for side, spec in (("new", self.new), ("old", self.old)):
            sides = [(self.me.deck, spec), (opp.deck, opp.strategy)]
            if seat == 1:
                sides.reverse()
            jid = f"{self.gid}-{tag}{i:05d}-{side}"
            pair["ids"][side] = jid
            jobs.append({"id": jid, "seed": seed, "first": None, "decks": [d for d, _ in sides],
                         "strategies": [s for _, s in sides], "strategy_seeds": sseeds,
                         "labels": {"gate": self.gid, "pair": i, "side": side, "member_seat": seat,
                                    "opponent": opp.mid}})
        self.pairs.append(pair)
        return jobs

    def _outcome(self, pair) -> str | None:
        """'new' / 'old' (the discordant winner), 'same', 'void', or None while a game is still out."""
        a, b = (self.results.get(pair["ids"][s]) for s in ("new", "old"))
        if a is None or b is None:
            return None
        if a["result"] == "void" or b["result"] == "void":
            return "void"
        won = [(r["winner"] == pair["seat"]) if r["winner"] in (0, 1) else None for r in (a, b)]
        if won[0] == won[1]:
            return "same"                          # both won, both lost, or both drawn
        if None in won:                            # a draw against a decided game: the decided side's result
            return "new" if won[0] or won[1] is False else "old"
        return "new" if won[0] else "old"

    def _run(self, make_jobs, stop, workers, step_limit, mask):
        from ladder import runner
        def on_result(log):
            self.results[log["id"]] = log
        runner.run(make_jobs(), str(self.dir / "games.jsonl"), workers=workers, step_limit=step_limit,
                   mask=mask, quiet=True, on_result=on_result)

    def run(self, workers=4, step_limit=30.0, mask=None) -> dict:
        t0 = time.time()
        rec = {"gate": self.gid, "date": time.strftime("%m-%d"), "member": self.me.mid, "anon": self.me.anon,
               "craft": self.me.craft,
               "kind": self.kind, "new": self.new, "old": self.old, "change": self.change,
               "prediction": self.prediction, "resubmit_of": self.resubmit_of, "since": self.since,
               "frozen": self.body["hash"], "seed_range": [self.lo, self.hi], "rng_seed": self.rng_seed}
        if self.kind in ("better", "noninf"):
            self._sequential(rec, workers, step_limit, mask)
        else:
            self._fixed(rec, workers, step_limit, mask)
        self._compute(rec)
        rec["pairs"] = len(self.pairs)                     # every pair played, the share pre-run included
        rec["pre_pairs"] = sum(1 for p in self.pairs if p["tag"] == "pre")
        rec["void_pairs"] = sum(1 for p in self.pairs if p.get("outcome") == "void")
        if rec["pairs"] and rec["void_pairs"] / rec["pairs"] > VOID_LIMIT:
            rec["verdict"] = "invalid: too many void pairs"
        if rec.get("compute_ratio") and rec["compute_ratio"] > COMPUTE_RATIO and not self.compute_is_the_point:
            rec["verdict"] = f"invalid: compute ratio {rec['compute_ratio']} > {COMPUTE_RATIO}"
        # opponents of the pairs the test used (not the share pre-run, not pairs finishing after the stop), and of
        # the ones among them whose results differed (the only ones the sequential test counts)
        used = [p for p in self.pairs if p["tag"] != "pre" and not p.get("after_stop")
                and p.get("outcome") not in (None, "void")]
        opp, opp_d = {}, {}
        for p in used:
            k = CRAFT_ZH[p["opp_craft"]]
            opp[k] = opp.get(k, 0) + 1
            if p["outcome"] in ("new", "old"):
                opp_d[k] = opp_d.get(k, 0) + 1
        rec["opponents"], rec["opponents_discordant"] = opp, opp_d

        def note(d):
            return "、".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda x: -x[1])) or "—"
        rec["opponents_note"] = note(opp) + ("" if self.kind == "same" else f"（结果不同的：{note(opp_d)}）")
        rec["seeds_used"] = sorted(self.seeds_used)
        rec["seed_note"] = f"{len(self.seeds_used)} 个，取自 {self.lo}～{self.hi - 1}"
        rec["seconds"] = round(time.time() - t0, 1)
        (self.dir / "pairs.json").write_text(json.dumps(self.pairs, ensure_ascii=False), encoding="utf-8")
        append_ledger(rec, self.ledger_root)
        return rec

    def _sequential(self, rec, workers, step_limit, mask):
        if self.share is None:                     # first gate of this member: measure the share first (A23)
            jobs = [j for i in range(PRE_PAIRS) for j in self._pair(i, "pre")]
            self._run(lambda: iter(jobs), None, workers, step_limit, mask)
            pre = [self._outcome(p) for p in self.pairs if p["tag"] == "pre"]
            for p, o in zip([p for p in self.pairs if p["tag"] == "pre"], pre):
                p["outcome"] = o
            valid = [o for o in pre if o not in (None, "void")]
            self.share = max(0.05, sum(o in ("new", "old") for o in valid) / max(1, len(valid)))
            rec["share_measured_on"] = len(valid)
        h0, h1 = (0.0, self.delta) if self.kind == "better" else (-2.0, 0.0)
        p0, p1 = p_of_gap(h0, self.share), p_of_gap(h1, self.share)
        exp = expected_pairs(p0, p1, self.share)
        cap = math.ceil(CAP_FACTOR * exp)
        rec.update(hypotheses=f"H0 {h0:+g} pp / H1 {h1:+g} pp，不同局占比 {self.share:.3f}",
                   discordant_share=round(self.share, 4), expected_pairs=round(exp), cap_pairs=cap)
        test = SPRT(p0, p1)
        state = {"verdict": None, "issued": 0}
        pending: list[dict] = []

        def jobs():
            while state["verdict"] is None and state["issued"] < cap:
                for j in self._pair(state["issued"], "p"):
                    yield j
                pending.append(self.pairs[-1])
                state["issued"] += 1
                drain()
                if state["verdict"] is not None:
                    return

        def drain():                                # count finished pairs in the order they were issued
            while pending and state["verdict"] is None:
                o = self._outcome(pending[0])
                if o is None:
                    return
                p = pending.pop(0)
                p["outcome"] = o
                if o in ("new", "old"):
                    p["counted"] = True
                    state["verdict"] = test.add(o == "new")
                state["done"] = state.get("done", 0) + 1
                if state["verdict"] is None and state["done"] >= SAME_AFTER and test.wins + test.losses == 0:
                    state["verdict"] = "SAME"           # identical results so far: report no difference, stop

        from ladder import runner

        def on_result(log):
            self.results[log["id"]] = log
            drain()
        runner.run(jobs(), str(self.dir / "games.jsonl"), workers=workers, step_limit=step_limit, mask=mask,
                   quiet=True, on_result=on_result)
        drain()
        for p in pending:                           # finished after the test had stopped: logged, not counted
            p["outcome"] = self._outcome(p)
            p["after_stop"] = True
        v = state["verdict"]
        if v == "SAME":
            rec["verdict"] = (f"no difference: the first {SAME_AFTER} pairs all had the same result "
                              f"({'passed' if self.kind == 'noninf' else 'not passed'})")
        else:
            rec["verdict"] = ("passed" if v == "H1" else "not passed") if v else "undecided (counts as not passed)"
        rec["llr"] = round(test.llr, 3)
        rec["discordant"] = {"new": test.wins, "old": test.losses}
        n = state["issued"]
        d = test.wins - test.losses
        rec["estimate_note"] = (f"停在第 {n} 对；不同局 {test.wins + test.losses}（新赢 {test.wins}）；"
                                f"停止时的胜率差 {100 * d / max(1, n):+.1f} pp（偏高，不当效果量）")

    def _fixed(self, rec, workers, step_limit, mask):
        jobs = [j for i in range(self.pairs_target) for j in self._pair(i, "f")]
        self._run(lambda: iter(jobs), None, workers, step_limit, mask)
        for p in self.pairs:
            p["outcome"] = self._outcome(p)
        valid = [p for p in self.pairs if p["outcome"] not in (None, "void")]
        if self.kind == "same":
            diff = []
            for p in self.pairs:
                a, b = self.results[p["ids"]["new"]], self.results[p["ids"]["old"]]
                if a.get("actions") != b.get("actions"):
                    diff.append(p["i"])
            rec["verdict"] = "passed: every decision the same" if not diff else \
                f"not passed: decisions differ in {len(diff)} of {len(self.pairs)} pairs (gate it as noninf)"
            rec["estimate_note"] = f"{len(self.pairs)} 对逐步比对"
            return
        for p in valid:
            p["counted"] = True
        xs = [1 if p["outcome"] == "new" else -1 if p["outcome"] == "old" else 0 for p in valid]
        n = len(xs)
        mean = sum(xs) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1)) if n > 1 else float("nan")
        half = t975(n - 1) * sd / math.sqrt(n)
        by = {}
        for p, x in zip(valid, xs):
            by.setdefault(CRAFT_ZH[p["opp_craft"]], []).append(x)
        rec["gap_pp"] = round(100 * mean, 2)
        rec["ci_pp"] = [round(100 * (mean - half), 2), round(100 * (mean + half), 2)]
        rec["by_class"] = {k: {"pairs": len(v), "gap_pp": round(100 * sum(v) / len(v), 1)} for k, v in by.items()}
        rec["discordant_share"] = round(sum(1 for x in xs if x) / n, 4)
        rec["verdict"] = ("no gap shown (interval contains 0)" if mean - half <= 0 <= mean + half else
                          "stronger" if mean > 0 else "weaker")
        rec["estimate_note"] = f"{n} 对：胜率差 {rec['gap_pp']:+.1f} pp，95% 区间 {rec['ci_pp'][0]:+.1f}～{rec['ci_pp'][1]:+.1f}"

    def _compute(self, rec):
        """Mean per-step compute of the member's side, new over old, on the counted (or all) pairs."""
        tot = {"new": [0, 0], "old": [0, 0]}
        for p in self.pairs:
            for side in ("new", "old"):
                log = self.results.get(p["ids"][side])
                if not log:
                    continue
                for seat, comp, _ in log.get("steps", []):
                    if seat == p["seat"]:
                        tot[side][0] += comp
                        tot[side][1] += 1
        if tot["new"][1] and tot["old"][1] and tot["old"][0]:
            rec["compute_ratio"] = round((tot["new"][0] / tot["new"][1]) / (tot["old"][0] / tot["old"][1]), 3)
            rec["compute_steps"] = {k: v[1] for k, v in tot.items()}


def selfcheck(sims: int = 2000, seed: int = 20261121) -> dict:
    """Plan 阶段 1 检验工具自检, first half: made-up pair sequences with a true gap of 0, of H1, and halfway."""
    out = {}
    for name, h0, h1 in (("better +2", 0.0, 2.0), ("better +5", 0.0, 5.0), ("noninf", -2.0, 0.0)):
        rows = []
        for k, gap in enumerate((h0, (h0 + h1) / 2, h1)):
            rows.append(simulate(gap, h0, h1, 0.4, sims, seed + 17 * k + len(out)))
        out[name] = rows
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("frozen"); r.add_argument("--member", required=True)
    r.add_argument("--new", required=True); r.add_argument("--old", required=True)
    r.add_argument("--kind", required=True, choices=["better", "noninf", "same", "fixed"])
    r.add_argument("--change", required=True); r.add_argument("--prediction", required=True)
    r.add_argument("--seeds", type=int, nargs=2, required=True); r.add_argument("--out", required=True)
    r.add_argument("--delta", type=float, default=2.0); r.add_argument("--share", type=float)
    r.add_argument("--pairs", type=int); r.add_argument("--workers", type=int, default=4)
    r.add_argument("--mask"); r.add_argument("--step-limit", type=float, default=30.0)
    r.add_argument("--resubmit-of"); r.add_argument("--what-changed-since", default="")
    r.add_argument("--compute-is-the-point", action="store_true")
    s = sub.add_parser("selfcheck"); s.add_argument("--sims", type=int, default=2000)
    a = ap.parse_args()
    if a.cmd == "selfcheck":
        print(json.dumps(selfcheck(a.sims), indent=1))
        return
    g = Gate(a.frozen, a.member, a.new, a.old, a.kind, a.change, a.prediction, tuple(a.seeds), a.out,
             delta=a.delta, share=a.share, pairs=a.pairs, resubmit_of=a.resubmit_of, since=a.what_changed_since,
             compute_is_the_point=a.compute_is_the_point)
    print(json.dumps(g.run(a.workers, a.step_limit, int(a.mask, 16) if a.mask else None), ensure_ascii=False,
                     indent=1))


if __name__ == "__main__":
    main()
