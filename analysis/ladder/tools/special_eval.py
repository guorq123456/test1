"""The special period's evaluation (Salem's S27 and S28, 11-24): every member a player entered in the special period
against the same-class baseline member, on the pool frozen at the period's end.

    python analysis/ladder/tools/special_eval.py --period 3 [--host C:\\claude\\ladder-host]
        [--players C:\\claude\\ladder-players] [--workers 23] [--mask 0x...] [--only MID ...]
        [--games 1200 --tail 600 --repeats 5]

1. frozen: HOST/special/P<P>/frozen.json, ladder.evaluator.freeze of HOST/pool (CR fixed at the mean of the last 1000
   decided games, the evaluator's own rule), taken once and kept; the pool must be past period P (its close done).
2. candidates: each player's new decks of period P that were accepted and entered the pool (the submissions ledger:
   receipts of kind deck, period P, verdict 收下, and their admit lines), and the seven baseline members (owner
   baseline, the default strategy). A member no longer in the frozen pool (removed) is evaluated from the pool's own
   record of it (deck and strategy), under its id.
3. each candidate: ladder.evaluator.Evaluation (locked, unchanged) with the frozen pool, 5 repeats of 1200 decided games,
   the last 600 counted (the evaluator's acceptance setting, S28). The candidate is taken out of the field. Seeds: the
   candidates in a fixed order (the baselines by id, then the players' members by id), candidate k gets
   SEEDS[P][0] + SPAN * k .. + SPAN (SEEDS.md). A candidate with a result.json is read, not run again; one cut off
   resumes where it stopped (the evaluator's own resume).
4. verdicts, for each player's member against the baseline member of its class: difference = its relative CR minus
   the baseline's; 95% interval from the two sets of repeats (Welch); 过关 = the interval's lower end above 0; 良好 =
   the difference 200 or more (S27). A repeat that stopped out of reach (S3: the value is a bound) is flagged.
   HOST/special/P<P>/result.json and result.md (with the players' names: host and Salem only); each player's own rows
   in PLAYERS/<folder>/receipts/特殊期评测-P<P>.md (never another player's).

Each candidate is played under the arena's lock as the host (D2: one run at a time; between candidates Salem's lab,
S30, may take a turn). Ctrl+C stops; running it again continues. The players' strategies are imported from HOST/subs/code (the workers get it
through LADDER_EXTRA_PATH, as in the gate).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

SEEDS = {3: (94610000, 94910000)}       # SEEDS.md; registered in the project's seed bank
SPAN = 7000                             # seeds per candidate: 6000 decided games and room for draws and voids
DEFAULT = "bot:mcts:100+plan"
CRAFT_ZH = {1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}


class EvalError(Exception):
    pass


def candidates(host: Path, period: int) -> tuple[list, list]:
    """(baselines, players' members): [{"mid", "craft", "owner", "member", "team", "receipt"}]."""
    from ladder.pool import Pool
    from ladder.submit import ledger
    pool = Pool(host / "pool")
    if pool.period <= period:
        raise EvalError(f"池子还在第 {pool.period} 期：第 {period} 期收尾以后才能评")
    lines = ledger(host / "subs")
    admitted = {l["receipt"]: l["mid"] for l in lines if l.get("ev") == "admit"}
    mine = []
    for l in lines:
        if (l.get("ev") == "receipt" and l.get("kind") == "deck" and l.get("verdict") == "收下"
                and l.get("period") == period and l["id"] in admitted):
            m = pool.members[admitted[l["id"]]]
            mine.append({"mid": m.mid, "craft": m.craft, "owner": l["player"], "member": l.get("member"),
                         "team": l.get("team"), "receipt": l["id"]})
    base = [{"mid": m.mid, "craft": m.craft, "owner": "baseline", "member": None, "team": None, "receipt": None}
            for m in pool.members.values() if m.owner == "baseline" and m.strategy == DEFAULT]
    crafts = sorted(b["craft"] for b in base)
    if crafts != list(range(1, 8)):
        raise EvalError(f"基线成员不是七个职业各一个：{crafts}")
    return sorted(base, key=lambda c: c["mid"]), sorted(mine, key=lambda c: c["mid"])


def welch(a: dict, b: dict) -> dict:
    """The difference a - b of two evaluator results, with its 95% interval (Welch)."""
    from ladder.leaderboard import t975
    d = a["rel_cr"] - b["rel_cr"]
    va, vb = a["se"] ** 2, b["se"] ** 2
    se = math.sqrt(va + vb)
    na, nb = a["repeats"] - 1, b["repeats"] - 1
    df = (va + vb) ** 2 / ((va ** 2 / na if na else math.inf) + (vb ** 2 / nb if nb else math.inf)) if se else 1
    half = t975(df) * se
    return {"diff": d, "se": se, "df": df, "lo": d - half, "hi": d + half}


def evaluate(host: Path, period: int, workers: int = 23, mask=None, only=None, games=1200, tail=600, repeats=5,
             log=print, arena: Path | None = None) -> dict:
    from ladder.evaluator import Candidate, Evaluation, freeze, load_frozen
    from ladder.pool import Pool
    out = host / "special" / f"P{period}"
    out.mkdir(parents=True, exist_ok=True)
    fz = out / "frozen.json"
    base, mine = candidates(host, period)
    if not fz.exists():
        body = freeze(host / "pool")
        fz.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"冻结池：{len(body['members'])} 个成员，哈希 {body['hash']}")
    frozen, body = load_frozen(fz)
    if body["period"] <= period:
        raise EvalError(f"{fz} 是第 {body['period']} 期的池子，不是第 {period} 期收尾以后的")
    code = str((host / "subs" / "code").resolve())
    if code not in sys.path:
        sys.path.insert(0, code)
    os.environ["LADDER_EXTRA_PATH"] = os.pathsep.join(x for x in (code, os.environ.get("LADDER_EXTRA_PATH", "")) if x)
    pool = Pool(host / "pool")
    order = base + mine
    lo0 = SEEDS[period][0]
    if lo0 + SPAN * len(order) > SEEDS[period][1]:
        raise EvalError(f"{len(order)} 个候选要 {SPAN * len(order)} 个种子，登记的段不够")
    want = set(only or [])
    if want:
        need = {c["craft"] for c in order if c["mid"] in want}
        want |= {b["mid"] for b in base if b["craft"] in need}       # a member's verdict needs its class's baseline
    results = {}
    for k, c in enumerate(order):
        if want and c["mid"] not in want:
            continue
        d = out / c["mid"]
        done = d / "result.json"
        if done.exists():
            results[c["mid"]] = json.loads(done.read_text(encoding="utf-8"))
            continue
        f = next((x for x in frozen if x.mid == c["mid"]), None)
        if f is not None:
            cand = Candidate(f.mid, f.craft, f.deck, f.strategy)
        else:                                                    # removed by the period's end: the pool's record
            m = pool.members[c["mid"]]
            cand = Candidate(m.mid, m.craft, list(m.deck), m.strategy)
        seeds = (lo0 + SPAN * k, lo0 + SPAN * (k + 1))
        log(f"[{k + 1}/{len(order)}] {c['mid']}（{CRAFT_ZH[c['craft']]}，{c['owner']}）种子 {seeds[0]}～{seeds[1] - 1}")
        ev = Evaluation(fz, d, cand, seeds, games, tail, repeats)
        lock = None
        if arena is not None:                # one run at a time (D2): the arena's lock as the host, candidate by
            from ladder.arena import _lock, _unlock     # candidate, so Salem's lab (S30) gets turns in between
            lock = _lock(arena, "host")
        try:
            results[c["mid"]] = ev.run(workers=workers, mask=mask, quiet=True)
        finally:
            if lock is not None:
                _unlock(lock)
        r = results[c["mid"]]
        log(f"    相对 CR {r['rel_cr']:+.0f}（{r['lo']:+.0f}～{r['hi']:+.0f}）" + ("，有重复够不着对手（界限）" if r["stuck"] else ""))
    return report(out, period, base, mine, results, host)


def report(out: Path, period: int, base: list, mine: list, results: dict, host: Path | None = None) -> dict:
    by_craft = {b["craft"]: b for b in base}
    rows = []
    for c in mine:
        r, b = results.get(c["mid"]), results.get(by_craft[c["craft"]]["mid"])
        if r is None or b is None:
            continue
        w = welch(r, b)
        rows.append({**c, "rel_cr": r["rel_cr"], "lo": r["lo"], "hi": r["hi"], "base_mid": by_craft[c["craft"]]["mid"],
                     "base_rel_cr": b["rel_cr"], "diff": w["diff"], "diff_lo": w["lo"], "diff_hi": w["hi"],
                     "pass": w["lo"] > 0, "good": w["diff"] >= 200, "bound": bool(r["stuck"] or b["stuck"])})
    body = {"period": period, "baselines": {b["mid"]: results.get(b["mid"]) for b in base}, "members": rows}
    (out / "result.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "result.md").write_text(table(rows, period, names=True), encoding="utf-8")
    return body


def table(rows: list, period: int, names: bool) -> str:
    head = [f"# 第 {period} 期特殊期评测", "",
            "每个成员在第 {0} 期收尾时冻结的池子上评一次（5 个重复 × 1200 局，取后 600 局），和同职业的基线成员比相对 CR。"
            "过关 = 差值的 95% 区间整个在 0 以上；良好 = 差值 200 以上。「界限」= 有重复打到够不着任何对手停下（S3），"
            "那个读数是界限。".format(period), ""]
    cols = (["选手"] if names else []) + ["队", "职业", "成员", "相对 CR", "基线", "差值（95% 区间）", "过关", "良好"]
    out = head + ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in sorted(rows, key=lambda r: (r["owner"], r["craft"])):
        cells = ([r["owner"]] if names else []) + [
            r["team"] or "—", CRAFT_ZH[r["craft"]], r["member"] or r["mid"],
            f"{r['rel_cr']:+.0f}（{r['lo']:+.0f}～{r['hi']:+.0f}）", f"{r['base_rel_cr']:+.0f}",
            f"{r['diff']:+.0f}（{r['diff_lo']:+.0f}～{r['diff_hi']:+.0f}）" + ("，界限" if r["bound"] else ""),
            "过" if r["pass"] else "没过", "是" if r["good"] else "—"]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def deliver(body: dict, players: Path) -> dict:
    """Each player's own rows into their receipts folder; never another player's."""
    from ladder.arena import FOLDER
    got = {}
    for player, folder in FOLDER.items():
        rows = [r for r in body["members"] if r["owner"] == player]
        if not rows:
            continue
        box = Path(players) / folder / "receipts"
        box.mkdir(parents=True, exist_ok=True)
        (box / f"特殊期评测-P{body['period']}.md").write_text(table(rows, body["period"], names=False), encoding="utf-8")
        got[player] = len(rows)
    return got


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", type=int, required=True)
    ap.add_argument("--host", type=Path, default=Path(r"C:\claude\ladder-host"))
    ap.add_argument("--players", type=Path, default=Path(r"C:\claude\ladder-players"))
    ap.add_argument("--arena", type=Path, default=Path(r"C:\claude\ladder-arena"), help="whose lock it takes")
    ap.add_argument("--workers", type=int, default=23)
    ap.add_argument("--mask", type=lambda x: int(x, 0), default=None)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--games", type=int, default=1200)
    ap.add_argument("--tail", type=int, default=600)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--no-deliver", action="store_true")
    a = ap.parse_args(argv)
    if a.period not in SEEDS:
        print(f"第 {a.period} 期没有登记评测种子（SEEDS）")
        return 1
    try:
        body = evaluate(a.host, a.period, a.workers, a.mask, a.only, a.games, a.tail, a.repeats, arena=a.arena)
    except EvalError as e:
        print(f"停下：{e}")
        return 1
    if not a.no_deliver and not a.only:
        print("放进选手的 receipts：", deliver(body, a.players))
    print(f"完成：{len(body['members'])} 个成员；结果 {a.host / 'special' / f'P{a.period}' / 'result.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
