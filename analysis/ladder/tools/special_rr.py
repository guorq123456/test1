"""Period 4's evaluation (Salem 11-27): the special period's players against each other only. Each player has at most
three new decks this period, one per blueprint (快攻妖精 Forest, 跳费龙 Dragon, 兔子教 Haven; ladder.special), kept
out of the pool (「池子先看结果，再评估是否放进去」); the default strategy and the baselines are not played
(「默认打法的参考价值太低了，只评估选手自己和其他选手的差距」).

    python analysis/ladder/tools/special_rr.py [--period 4] [--host C:\\claude\\ladder-host]
        [--players C:\\claude\\ladder-players] [--arena C:\\claude\\ladder-arena] [--workers 23] [--mask 0x...]
        [--dry] [--trial N] [--no-deliver] [--no-void-stop]
    python analysis/ladder/tools/special_rr.py --report      # the formal report again from its logs, no game
    python analysis/ladder/tools/special_rr.py --deliver     # the players' receipts from the formal result, no game

1. members: each player's accepted new decks of the period (the submissions ledger: receipts of kind deck, period P,
   verdict 收下; never admitted, so nothing comes from the pool), by class: one of the three blueprints' classes, at
   most one each (two is an error: the slot rule allows one). The deck from HOST/subs/<receipt>/submission.json, the
   strategy the receipt's spec (HOST/subs/code, given to the workers through LADDER_EXTRA_PATH, as in the gate). An
   accepted deck of another class is not evaluated (listed in the notes). The players are ladder.arena.PLAYERS, all
   five whether they handed in anything or not. The changes from the blueprint are counted again here
   (special.compare): a receipt with no blueprint record, another count than its record's, or more changes than the
   cap is a doubt, and a formal run stops on any doubt (the ledger is sorted out first).
2. pairs: 15 slots, (player, class) in PLAYERS order and then ARCH order; every two slots of different players, (s, t)
   with s < t in lexicographic order, is pair k = 0..89 (a player's own three never meet). The layout is fixed by the
   player list alone: a slot nobody filled keeps its pairs' places and seeds.
3. seeds: pair k gets SEEDS[P][0] + PER_PAIR * k .. + PER_PAIR - 1 (period 4: 96310000 + 500k; 90 pairs use
   96310000-96354999 of the registered 96310000-96409999). Each seed is played twice, the pair's lower slot in seat 0
   and then in seat 1 (the same keyed deal, so the same first seat: each member is first once per seed), 1000 games a
   pair. The deal key is required for a formal run: ladder/deal.py's FORMAL list does not hold this range (it doesn't
   hold period 3's either), so the runner would deal it without a key; this tool refuses instead, and every game is
   sealed with the host's key (its id in the plan and the result).
   --trial N: N seeds a pair from TRIAL_SEEDS (92648000-92648999, the host's dry-run range; pair k gets
   92648000 + N * k ..), into HOST/special/P<P>/trial-N/, with the host's key if there is one; the period need not be
   closed, nothing is delivered. --dry: the plan only (members, missing ones, pairs, seeds, key, environment); nothing
   is played or written.
4. games: ladder.runner.run, one run per two players (the 9 pairs between them, a log HOST/special/P<P>/games/
   <a>--<b>.jsonl), under the arena's lock as the host (D2: one run at a time; between two runs Salem's lab, S30, may
   take a turn). Ctrl+C stops; running it again plays only the games not in the logs. HOST/special/P<P>/rr-plan.json
   is written before the first game: a later run with other members, seeds or another key stops (never mixed).
5. counting: a win 1, a draw 0.5, a loss 0 (a crash, an illegal move or a timeout loses for its side, as on the
   ladder); a void game is written down with its reason (the first line of its error) and not counted, for both of its
   members (whose doing it was is a rule for the host and Salem to set, not this tool); a pair, or a member, with more
   than VOID_FLAG of its games void is flagged and the result is held: not delivered until the host has read it and
   runs --deliver. A run stops once one member has VOID_STOP (ladder.arena's) void games in it and they are more than
   half of its games there (the arena's rule, 11-23 review: a strategy whose every game is void would hold the
   machine for its whole block); --no-void-stop plays on.
   A slot with no deck (缺交) loses every game it was due: 2 * PER_PAIR a pair, the other side winning them (both
   losing when both are missing). Rates are weighted by games. The 95% interval treats the two games of one seed as one
   unit, strata = the pairs of members (each a fixed part of the design), the rate a ratio (score / games) by the delta
   method: var = sum over strata of m/(m-1) * sum (e_i - mean e)^2, e_i = score_i - rate * games_i, over the stratum's
   m units with a game counted, divided by all games squared; rate +- 1.96 standard errors, clipped to 0..1. The games a
   missing slot was due are a fixed amount, not in the variance.
6. results: each player's rate against the other four (the 36 pairs a player is in) and their rank; the 5 x 5 table of
   player against player (the 9 pairs between two players); one 5 x 5 table per blueprint (the same class on both
   sides: 妖对妖, 龙对龙, 兔对兔); each member against each other player, against each class, and in all.
   HOST/special/P<P>/rr-result.json and rr-result.md (with the players' names: host and Salem only); each player's own
   numbers in PLAYERS/<folder>/receipts/特殊期评测-P<P>.md (their rate and interval, their three members' rates
   against the others, their rank of five; never another player's name, list or code), unless the result is held.
   --report: rr-result.json and .md again from the logs (no game; the environment and the key are the plan's, not
   checked again, so it works after the simulator moved on); --deliver: the receipts from the rr-result.json there.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

SEEDS = {4: (96310000, 96410000)}     # SEEDS.md (the host registers it): formal runs only
PER_PAIR = 500                        # seeds a pair of members; each seed played twice, the seats swapped
TRIAL_SEEDS = (92648000, 92649000)    # --trial (and the unit tests): the host's dry-run range, never a formal one
ARCH = ((1, "快攻妖精", "妖"), (4, "跳费龙", "龙"), (6, "兔子教", "兔"))   # Salem 11-27; this order is the layout's
VOID_FLAG = 0.02                      # a pair or a member with more of its games void: flagged, the result held
WHY_LEN = 80                          # a void game's reason as the report gives it: its error's first line, cut
Z95 = 1.959963984540054
DECIDED = ("normal", "crash", "illegal", "timeout")
ERRORS = ("crash", "illegal", "timeout")
NAME = "rr-result"
RECEIPT = "特殊期评测-P{period}.md"


class EvalError(Exception):
    pass


def _players():
    from ladder.arena import PLAYERS
    return tuple(PLAYERS)


def arch_name(craft: int) -> str:
    return next(n for c, n, _ in ARCH if c == craft)


def slot_name(slot) -> str:
    return f"{slot[0]}/{arch_name(slot[1])}"


# --- the layout ---------------------------------------------------------------------------------------------------

def slots(players) -> list:
    """(player, class) in player order, then ARCH order."""
    return [(p, c) for p in players for c, _, _ in ARCH]


def pairs(players) -> list[dict]:
    """Every two slots of different players: [{"k", "a", "b"}], a the lower slot, in lexicographic order."""
    s = slots(players)
    out = []
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            if s[i][0] != s[j][0]:
                out.append({"k": len(out), "a": s[i], "b": s[j]})
    return out


def layout(players, period: int = 4, trial: int | None = None) -> dict:
    """The seeds: pair k plays seeds lo + span * k .. lo + span * k + n - 1 (formal: n = span = PER_PAIR on SEEDS[P];
    trial: n = span = N on TRIAL_SEEDS)."""
    if trial is None:
        if period not in SEEDS:
            raise EvalError(f"第 {period} 期没有选手互打评测的种子（SEEDS）")
        (lo, hi), n = SEEDS[period], PER_PAIR
    else:
        (lo, hi), n = TRIAL_SEEDS, int(trial)
        if n < 2:
            raise EvalError("--trial 至少 2 个种子一对（区间要两个以上的种子才算得出来）")
    ps = pairs(players)
    if n < 1 or lo + n * len(ps) > hi:
        raise EvalError(f"{len(ps)} 对 × {n} 个种子要 {n * len(ps)} 个，{lo}～{hi - 1} 不够")
    return {"lo": lo, "hi": hi, "span": n, "n": n, "pairs": ps, "trial": trial,
            "used": [lo, lo + n * len(ps) - 1] if ps else None}


def pair_seeds(lay: dict, k: int) -> list[int]:
    lo = lay["lo"] + lay["span"] * k
    return list(range(lo, lo + lay["n"]))


def job_id(period: int, k: int, i: int, x: int) -> str:
    return f"R{period}-{k:02d}-{i:03d}{'ab'[x]}"


# --- the members --------------------------------------------------------------------------------------------------

def candidates(host: Path, period: int, players=None) -> tuple[dict, list, list]:
    """({(player, class): member}, notes, doubts): the accepted new decks of the period, from the ledger and the
    receipts' folders. A member: {"player", "craft", "arch", "member", "receipt", "spec", "deck" (sorted card ids),
    "code" (the deck code handed in), "list" (sha1 of the list, 10), "changes" (counted here)}. doubts: receipts whose
    blueprint record is missing or says another count than the deck has, and decks over the cap (a formal run stops)."""
    from ladder import base, special
    from ladder.pool import CRAFT_ZH, list_key
    from ladder.runner import load_deck
    from ladder.submit import ledger
    players = tuple(players or _players())
    subs = Path(host) / "subs"
    crafts = {c for c, _, _ in ARCH}
    got, notes, doubts = {}, [], []
    for l in ledger(subs):
        if not (l.get("ev") == "receipt" and l.get("kind") == "deck" and l.get("verdict") == "收下"
                and l.get("period") == period):
            continue
        rid, player = l["id"], l.get("player")
        if player not in players:
            raise EvalError(f"{rid} 是 {player!r} 的，不在选手名单里（{'、'.join(players)}）")
        sub = subs / rid / "submission.json"
        try:
            meta = json.loads(sub.read_text(encoding="utf-8"))
            ids = sorted(c.card_id for c in load_deck(meta["deck"]))
        except (OSError, ValueError, KeyError) as e:
            raise EvalError(f"{rid}（{player}）的卡组读不出来（{sub}：{type(e).__name__}: {e}）") from None
        craft = l.get("craft") or (l.get("blueprint") or {}).get("craft") or int(base.craft_of(load_deck(ids)))
        if craft not in crafts:
            notes.append(f"{rid}（{player}，{CRAFT_ZH.get(craft, craft)}）不是三副蓝本的职业，不评")
            continue
        if (player, craft) in got:
            raise EvalError(f"{player} 的{arch_name(craft)}收下了两副（{got[(player, craft)]['receipt']}、{rid}）："
                            "每人每个原型最多一副，先查清台账")
        spec = l.get("spec")
        if not spec:
            raise EvalError(f"{rid}（{player}）的回执里没有打法（spec）")
        if spec.startswith("py:") and not (subs / "code" / f"{spec.split(':')[1]}.py").is_file():
            raise EvalError(f"{rid}（{player}）的打法 {spec} 在 {subs / 'code'} 里没有")
        b = special.blueprint_for(period, craft) if special.style(period) == "blueprints" else None
        n = None if b is None else special.compare(ids, b["ids"])["changes"]
        said = (l.get("blueprint") or {}).get("changes")
        if b is not None:                    # the receipt's word is checked, never taken (11-27 review)
            if not l.get("blueprint"):
                doubts.append(f"{rid}（{player}）的回执里没有蓝本那一项（不是第 {period} 期的收卷代码收的？）")
            elif said != n:
                doubts.append(f"{rid}（{player}）的回执记着改了 {said} 张，卡组现在数是 {n} 张")
            if n > b["max_changes"]:
                doubts.append(f"{rid}（{player}）和蓝本{b['name']}比改了 {n} 张，超过上限 {b['max_changes']} 张")
        got[(player, craft)] = {"player": player, "craft": craft, "arch": arch_name(craft), "member": l.get("member"),
                                "receipt": rid, "spec": spec, "deck": ids, "code": meta["deck"],
                                "list": hashlib.sha1(list_key(ids).encode()).hexdigest()[:10], "changes": n}
    return got, notes, doubts


# --- one pair's games ---------------------------------------------------------------------------------------------

def jobs_of(pair: dict, cands: dict, seeds: list, period: int) -> list[dict]:
    """Both games of every seed: the lower slot ("a") in seat 0, then in seat 1."""
    a, b = cands[pair["a"]], cands[pair["b"]]
    out = []
    for i, seed in enumerate(seeds):
        for x, (s0, s1) in enumerate(((a, b), (b, a))):
            out.append({"id": job_id(period, pair["k"], i, x), "seed": seed, "first": None,
                        "decks": [s0["deck"], s1["deck"]], "strategies": [s0["spec"], s1["spec"]],
                        "strategy_seeds": None,
                        "labels": {"rr": period, "pair": pair["k"], "i": i, "a_seat": x,
                                   "members": [slot_name((s0["player"], s0["craft"])),
                                               slot_name((s1["player"], s1["craft"]))],
                                   "receipts": [s0["receipt"], s1["receipt"]]}})
    return out


def outcomes(path: Path) -> dict:
    """{job id: {"result", "winner", "why"}} of a log (a torn line skipped; the first line of an id kept); why: a
    void game's reason, else None."""
    got = {}
    if not Path(path).exists():
        return got
    with Path(path).open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip(" \t\r\n\x00")
            if not line:
                continue
            try:
                g = json.loads(line)
            except ValueError:
                continue
            if isinstance(g, dict) and "id" in g and g["id"] not in got:
                o = {"result": g.get("result"), "winner": g.get("winner")}
                o["why"] = why_void(g) if score(o, 0) is None else None
                got[g["id"]] = o
    return got


def why_void(g: dict) -> str:
    """A void game's reason: the first line of its error as the runner wrote it, cut at WHY_LEN characters."""
    first = next((x.strip() for x in str(g.get("error") or "").splitlines() if x.strip()), "")
    return first[:WHY_LEN] or "（日志里没写原因）"


def score(o: dict, seat: int) -> float | None:
    """The score of the side in `seat`: 1 won, 0.5 drawn, 0 lost; None: void (not counted)."""
    if o["result"] == "draw":
        return 0.5
    if o["result"] in DECIDED and o["winner"] in (0, 1):
        return 1.0 if o["winner"] == seat else 0.0
    return None


def tally(pair: dict, lay: dict, cands: dict, got: dict, period: int) -> tuple[dict, list | None]:
    """(the pair's row from a's side, its units [(a's score, games counted)] by seed; None for a missing slot)."""
    a_in, b_in = pair["a"] in cands, pair["b"] in cands
    seeds = pair_seeds(lay, pair["k"])
    row = {"k": pair["k"], "a": slot_name(pair["a"]), "b": slot_name(pair["b"]), "seeds": [seeds[0], seeds[-1]]}
    if not (a_in and b_in):
        g = 2 * lay["n"]
        row.update(status="missing", missing=[s for s, here in (("a", a_in), ("b", b_in)) if not here], games=g,
                   score_a=float(g if a_in else 0), score_b=float(g if b_in else 0), voids=0, void_share=0.0,
                   void_why={}, wins_a=g if a_in else 0, wins_b=g if b_in else 0, draws=0, errors={})
        return row, None
    units, voids, why, wins, draws, errors, absent = [], 0, {}, [0, 0], 0, {}, 0
    for i in range(lay["n"]):
        s = n = 0
        for x in (0, 1):                     # x: a's seat in that game
            o = got.get(job_id(period, pair["k"], i, x))
            if o is None:
                absent += 1
                continue
            v = score(o, x)
            if v is None:
                voids += 1
                w = o.get("why") or "（日志里没写原因）"
                why[w] = why.get(w, 0) + 1
                continue
            s, n = s + v, n + 1
            if v == 0.5:
                draws += 1
            else:
                wins[0 if v == 1 else 1] += 1
            if o["result"] in ERRORS:        # who lost it by their own doing
                side = "a" if o["winner"] != x else "b"
                key = f"{side}:{o['result']}"
                errors[key] = errors.get(key, 0) + 1
        units.append((s, n))
    if absent:
        raise EvalError(f"第 {pair['k']} 对（{row['a']} 对 {row['b']}）还有 {absent} 局没有记录：先把它打完")
    games = sum(n for _, n in units)
    sa = sum(s for s, _ in units)
    row.update(status="played", games=games, score_a=sa, score_b=games - sa, voids=voids,
               void_share=voids / (2 * lay["n"]), void_why=why, wins_a=wins[0], wins_b=wins[1], draws=draws,
               errors=errors)
    return row, units


def member_voids(rows: list) -> dict:
    """{member: {"voids", "games" (its games played, the void ones in), "share", "why": {reason: n}}} over the pairs
    played: a void game counts for both of its members (whose doing it was is not told here)."""
    out: dict = {}
    for r in rows:
        if r["status"] != "played":
            continue
        for side in ("a", "b"):
            m = out.setdefault(r[side], {"voids": 0, "games": 0, "why": {}})
            m["voids"] += r["voids"]
            m["games"] += r["games"] + r["voids"]
            for w, n in r["void_why"].items():
                m["why"][w] = m["why"].get(w, 0) + n
    for m in out.values():
        m["share"] = m["voids"] / m["games"] if m["games"] else 0.0
    return out


def holds(rows: list, voids: dict) -> list[str]:
    """Why the result is not delivered by itself: pairs or members with more than VOID_FLAG of their games void."""
    flagged = [r for r in rows if r["void_share"] > VOID_FLAG]
    out = [f"{len(flagged)} 对作废超过 {100 * VOID_FLAG:.0f}%"] if flagged else []
    out += [f"{name} 的局作废 {m['voids']}/{m['games']}（{100 * m['share']:.1f}%）"
            for name, m in sorted(voids.items(), key=lambda x: -x[1]["share"]) if m["share"] > VOID_FLAG]
    return out


# --- rates and intervals --------------------------------------------------------------------------------------------

def view(row: dict, units, side: str) -> tuple:
    """One pair seen from `side` ("a" or "b"): (units or None, fixed score, fixed games, wins, draws, losses, voids)."""
    if units is None:
        s = row["score_a"] if side == "a" else row["score_b"]
        w = row["wins_a"] if side == "a" else row["wins_b"]
        return None, s, row["games"], w, 0, row["games"] - w, 0
    if side == "b":
        units = [(n - s, n) for s, n in units]
    w, l = (row["wins_a"], row["wins_b"]) if side == "a" else (row["wins_b"], row["wins_a"])
    return units, 0.0, 0, w, row["draws"], l, row["voids"]


def rate(parts: list) -> dict:
    """The score rate of a set of pairs from one side (each a `view`), weighted by games, with its 95% interval
    (see the module's step 5)."""
    S = G = 0.0
    w = d = l = v = 0
    missing = 0
    for units, fs, fg, pw, pd, pl, pv in parts:
        w, d, l, v = w + pw, d + pd, l + pl, v + pv
        if units is None:
            S, G, missing = S + fs, G + fg, missing + fg
        else:
            S, G = S + sum(s for s, _ in units), G + sum(n for _, n in units)
    out = {"games": int(G), "score": S, "wins": w, "draws": d, "losses": l, "voids": v, "missing_games": missing}
    if not G:
        return {**out, "rate": None, "lo": None, "hi": None, "se": None}
    p = S / G
    var = 0.0
    for units, *_ in parts:
        if units is None:
            continue
        es = [s - p * n for s, n in units if n]
        m = len(es)
        if m > 1:
            mean = sum(es) / m
            var += m / (m - 1) * sum((e - mean) ** 2 for e in es)
    se = math.sqrt(var) / G
    return {**out, "rate": p, "lo": max(0.0, p - Z95 * se), "hi": min(1.0, p + Z95 * se), "se": se}


def summarize(players, rows: list, units: dict) -> dict:
    """Totals, ranks, the player table, the same-class tables and the members' rows from the pairs."""
    by = {}                                   # (side slot, other slot) -> view
    for r in rows:
        a, b = _slot_of(r["a"]), _slot_of(r["b"])
        by[(a, b)] = view(r, units.get(r["k"]), "a")
        by[(b, a)] = view(r, units.get(r["k"]), "b")

    def of(pred):
        return rate([v for (x, y), v in by.items() if pred(x, y)])
    totals = {p: of(lambda x, y, p=p: x[0] == p) for p in players}
    order = sorted(players, key=lambda p: -(totals[p]["rate"] or 0.0))
    ranks = {p: 1 + sum(1 for q in players if (totals[q]["rate"] or 0.0) > (totals[p]["rate"] or 0.0))
             for p in players}
    matrix = {p: {q: of(lambda x, y, p=p, q=q: x[0] == p and y[0] == q) for q in players if q != p} for p in players}
    same = {arch_name(c): {p: {q: rate([by[((p, c), (q, c))]]) for q in players if q != p} for p in players}
            for c, _, _ in ARCH}
    members = {}
    for p in players:
        for c, _, _ in ARCH:
            me = (p, c)
            members[slot_name(me)] = {
                "player": p, "craft": c, "arch": arch_name(c),
                "total": of(lambda x, y, me=me: x == me),
                "vs_player": {q: of(lambda x, y, me=me, q=q: x == me and y[0] == q) for q in players if q != p},
                "vs_arch": {arch_name(c2): of(lambda x, y, me=me, c2=c2: x == me and y[1] == c2) for c2, _, _ in ARCH}}
    return {"totals": totals, "order": order, "ranks": ranks, "matrix": matrix, "same_arch": same, "members": members}


def _slot_of(name: str) -> tuple:
    p, a = name.rsplit("/", 1)
    return p, next(c for c, n, _ in ARCH if n == a)


# --- running ------------------------------------------------------------------------------------------------------

def _out_dir(host: Path, period: int, trial: int | None) -> Path:
    out = Path(host) / "special" / f"P{period}"
    return out if trial is None else out / f"trial-{trial}"


def _checks(host: Path, period: int, formal: bool, key) -> dict:
    """The period closed, the simulator the period's, the deal key: required for a formal run, reported otherwise."""
    from ladder import deal
    got, warn = {}, []
    try:
        from ladder.pool import Pool
        got["pool_period"] = Pool(Path(host) / "pool").period
    except Exception as e:                    # noqa: BLE001 - written into the warnings
        got["pool_period"] = None
        warn.append(f"读不了池子（{type(e).__name__}: {e}）")
    if got["pool_period"] is not None and got["pool_period"] <= period:
        warn.append(f"池子还在第 {got['pool_period']} 期：第 {period} 期收尾以后才评（收下的卡组可能还会变）")
    try:
        import environments
        got["env"] = environments.check(period)["name"]
    except SystemExit as e:                  # environments.check stops with its own message
        got["env"] = None
        warn.append(str(e))
    try:
        k = deal.resolve(key)
    except deal.DealError as e:
        raise EvalError(f"发牌密钥读不了：{e}") from None
    got["key_bytes"], got["key"] = k, (deal.key_id(k) if k else None)
    if k is None:
        warn.append(f"没有发牌密钥（{deal.DEFAULT_KEY} 或 {deal.KEY_ENV}）：这一段种子 deal.py 不当正式段、runner 不拦，"
                    "正式评测由这个工具自己要求有密钥（试跑不要求）")
    got["warnings"] = warn
    if formal and warn:
        raise EvalError("；".join(warn))
    return got


def plan_record(period: int, players, lay: dict, cands: dict, key_id: str | None, env: str | None) -> dict:
    return {"period": period, "trial": lay["trial"], "players": list(players), "arch": [n for _, n, _ in ARCH],
            "seeds": {"lo": lay["lo"], "span": lay["span"], "n": lay["n"], "pairs": len(lay["pairs"]),
                      "used": lay["used"]},
            "key": key_id, "env": env,
            "members": {slot_name(s): ({k: cands[s][k] for k in ("receipt", "spec", "list")} if s in cands else None)
                        for s in slots(players)}}


def _same_plan(path: Path, plan: dict):
    """The plan of the games already in this folder must be this one (never mixed); written if there is none."""
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        diff = [k for k in plan if old.get(k) != plan[k]]
        if diff:
            raise EvalError(f"{path.parent} 里是另一次评测的对局（{'、'.join(diff)} 不一样）：不混着用，"
                            "先挪走那个目录")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")


def blocks(lay: dict, players) -> list[tuple]:
    """[(player a, player b, [pairs])]: the pairs between two players, in pair order."""
    out: dict = {}
    for p in lay["pairs"]:
        out.setdefault((p["a"][0], p["b"][0]), []).append(p)
    return [(a, b, ps) for (a, b), ps in out.items()]


def evaluate(host: Path, period: int = 4, workers: int = 23, mask=None, trial: int | None = None, key="auto",
             arena: Path | None = None, players=None, log=print, void_stop=True) -> dict:
    """Play what is not played yet and write the report. void_stop: True stops a run at ladder.arena's VOID_STOP (see
    _void_watch), an int at that many, False never."""
    players = tuple(players or _players())
    if not 1 <= workers <= 23:
        raise EvalError("--workers 要 1～23")
    lay = layout(players, period, trial)
    cands, notes, doubts = candidates(host, period, players)
    chk = _checks(host, period, trial is None, key)
    if doubts and trial is None:
        raise EvalError("台账和卡组对不上，先查清：" + "；".join(doubts))
    for w in chk["warnings"] + doubts:
        log(f"注意：{w}")
    if arena is not None:
        w = _window_open(arena, period)
        if w:
            log(f"注意：{w}")
    out = _out_dir(host, period, trial)
    plan = plan_record(period, players, lay, cands, chk["key"], chk["env"])
    _same_plan(out / "rr-plan.json", plan)
    code = str((Path(host) / "subs" / "code").resolve())
    if code not in sys.path:
        sys.path.insert(0, code)
    os.environ["LADDER_EXTRA_PATH"] = os.pathsep.join(x for x in (code, os.environ.get("LADDER_EXTRA_PATH", "")) if x)
    games_dir = out / "games"
    games_dir.mkdir(parents=True, exist_ok=True)
    if void_stop is True:
        from ladder.arena import VOID_STOP
        void_stop = VOID_STOP
    bl = blocks(lay, players)
    for b, (pa, pb, ps) in enumerate(bl):
        path = games_dir / f"{pa}--{pb}.jsonl"
        jobs = [j for p in ps if p["a"] in cands and p["b"] in cands
                for j in jobs_of(p, cands, pair_seeds(lay, p["k"]), period)]
        if not jobs:
            log(f"[{b + 1}/{len(bl)}] {pa} 对 {pb}：没有能打的对（缺交）")
            continue
        done = set(outcomes(path))
        left = [j for j in jobs if j["id"] not in done]
        if not left:
            log(f"[{b + 1}/{len(bl)}] {pa} 对 {pb}：已经打完（{len(jobs)} 局）")
            continue
        log(f"[{b + 1}/{len(bl)}] {pa} 对 {pb}：{sum(1 for p in ps if p['a'] in cands and p['b'] in cands)} 对，"
            f"{len(left)} 局要打（已打 {len(jobs) - len(left)}）")
        _run_block(left, path, workers, mask, chk["key_bytes"], arena, log, void_stop or None)
    return report(out, period, players, lay, cands, notes, chk, trial, doubts)


def _window_open(arena: Path, period: int) -> str | None:
    """A later period's practice window still open: every block takes the arena's lock as the host (who goes first),
    so the players' runs wait behind it (the run should come between the close and the next opening)."""
    from datetime import datetime, timezone
    try:
        win = json.loads((Path(arena) / "public" / "window.json").read_text(encoding="utf-8"))
        deadline = datetime.fromisoformat(str(win["deadline"]).replace("Z", "+00:00"))
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if int(win.get("period") or 0) > period and datetime.now(timezone.utc) < deadline:
        return (f"第 {win['period']} 期的练习场窗口开着（截止 {win['deadline']}）：评测每一块都以主持方身份先拿锁，"
                f"选手的练习要排在后面等；照常应该在第 {period} 期收尾以后、下一期开期以前跑")
    return None


def _void_watch(stop: int | None, path: Path):
    """runner.run's on_result: stop the run once one member has `stop` void games in it and they are more than half of
    its games there (ladder.arena's VOID_STOP rule, 11-23 review: a strategy whose every game is void would hold the
    machine for the whole block). The games already written stay; running again goes on from them."""
    seen: dict = {}

    def on_result(log):
        labels = log.get("labels") or {}
        void = score({"result": log.get("result"), "winner": log.get("winner")}, 0) is None
        for m in labels.get("members") or ():
            c = seen.setdefault(m, [0, 0])
            c[0], c[1] = c[0] + void, c[1] + 1
            if stop and void and c[0] >= stop and c[0] * 2 > c[1]:
                raise EvalError(f"{m} 这一次作废了 {c[0]} 局（一共 {c[1]} 局），比一半还多，先停下：多半是它的打法在评测的"
                                f"进程里载入不了，或者在对局里碰了绊线（最近一局：{why_void(log)}）。看 {path} 里作废的局"
                                "写着的原因；查清以后再跑同一条命令接着打（打完的局不重打），要照样打完加 --no-void-stop")
    return on_result


def _run_block(jobs: list, path: Path, workers: int, mask, key, arena: Path | None, log, void_stop: int | None = None):
    from ladder import runner
    lock = unlock = let_others_in = None
    if arena is not None:                    # one run at a time (D2): the arena's lock as the host, block by block,
        # so Salem's lab (S30) gets turns in between; both imported before the lock is taken
        from special_eval import let_others_in

        from ladder.arena import _lock, _unlock
        lock, unlock = _lock(arena, "host"), _unlock
    try:
        r = runner.run(jobs, str(path), workers=workers, mask=mask, quiet=True, key=key,
                       on_result=_void_watch(void_stop, path))
    finally:
        if lock is not None:
            unlock(lock)
            let_others_in(arena)
    log(f"    {r.get('played', 0)} 局，{r.get('seconds', 0):.0f} 秒，{r.get('results', {})}")


def again(host: Path, period: int = 4, players=None) -> dict:
    """--report: the formal report once more from the logs already written, no game. The members, seeds and players
    must be the plan's (rr-plan.json); its environment and key are kept, not checked again (so it works after the
    simulator moved on to the next period's)."""
    players = tuple(players or _players())
    lay = layout(players, period)
    cands, notes, doubts = candidates(host, period, players)
    if doubts:
        raise EvalError("台账和卡组对不上，先查清：" + "；".join(doubts))
    out = _out_dir(host, period, None)
    path = out / "rr-plan.json"
    if not path.exists():
        raise EvalError(f"没有 {path}：第 {period} 期还没正式跑过")
    old = json.loads(path.read_text(encoding="utf-8"))
    _same_plan(path, plan_record(period, players, lay, cands, old.get("key"), old.get("env")))
    try:
        from ladder.pool import Pool
        pool_period = Pool(Path(host) / "pool").period
    except Exception:                         # noqa: BLE001 - only written into the report
        pool_period = None
    chk = {"key": old.get("key"), "env": old.get("env"), "pool_period": pool_period, "key_bytes": None,
           "warnings": ["这一份是 --report 从日志重出的：模拟器环境和发牌密钥是 rr-plan.json 记的，这次没有再核"]}
    return report(out, period, players, lay, cands, notes, chk, None, doubts)


def saved(host: Path, period: int = 4) -> dict:
    """--deliver: the formal result already written (rr-result.json)."""
    f = _out_dir(host, period, None) / f"{NAME}.json"
    if not f.exists():
        raise EvalError(f"没有 {f}：先正式跑完（或 --report 重出）")
    body = json.loads(f.read_text(encoding="utf-8"))
    if body.get("trial") is not None or body.get("period") != period:
        raise EvalError(f"{f} 不是第 {period} 期的正式结果")
    return body


# --- the reports --------------------------------------------------------------------------------------------------

def report(out: Path, period: int, players, lay: dict, cands: dict, notes: list, chk: dict,
           trial: int | None, doubts: list | None = None) -> dict:
    """rr-result.json and .md from the logs in `out`. "hold": why the result is not delivered by itself (holds)."""
    got = {}
    for f in sorted((out / "games").glob("*.jsonl")):
        got.update(outcomes(f))
    rows, units = [], {}
    for p in lay["pairs"]:
        row, u = tally(p, lay, cands, got, period)
        rows.append(row)
        if u is not None:
            units[p["k"]] = u
    s = summarize(players, rows, units)
    flagged = [r["k"] for r in rows if r["void_share"] > VOID_FLAG]
    voids = member_voids(rows)
    body = {"period": period, "trial": trial, "players": list(players), "arch": [n for _, n, _ in ARCH],
            "seeds": {k: lay[k] for k in ("lo", "span", "n", "used")}, "key": chk["key"], "env": chk["env"],
            "pool_period": chk["pool_period"], "warnings": chk["warnings"], "notes": notes, "doubts": doubts or [],
            "hold": holds(rows, voids), "member_voids": voids,
            "members_in": {slot_name(k): {x: v[x] for x in ("member", "receipt", "spec", "list", "changes", "code")}
                           for k, v in cands.items()},
            "missing": [slot_name(x) for x in slots(players) if x not in cands],
            "pairs": rows, "void_flagged": flagged,
            "games": {"played": sum(r["games"] + r["voids"] for r in rows if r["status"] == "played"),
                      "counted": sum(r["games"] for r in rows if r["status"] == "played"),
                      "void": sum(r["voids"] for r in rows), "draws": sum(r["draws"] for r in rows)},
            **s, "interval": INTERVAL}
    (out / f"{NAME}.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / f"{NAME}.md").write_text(host_text(body), encoding="utf-8")
    return body


INTERVAL = ("95% 区间：同一个种子的两局（两边各坐一次）算一组，按「一副对一副」分层，每层里各组得分的波动合起来，"
            "胜率按「得分 ÷ 局数」用正态近似（点估计 ± 1.96 个标准误，截在 0～100%）。缺交该打的局是定数，不算进波动。")


PLAYER_INTERVAL = ("括号里是 95% 区间：局数有限，胜率里有运气，真实的胜率大概率在这个范围里，范围越窄越准（同一个种子换座位的"
                   "两局算一组来估）。没交的那一副算的局是定数，不算进这个范围。")


def pct(r: dict | None, ci: bool = True, note: str = "", long: bool = False) -> str:
    """「52.8%（47.3～58.2）」; long: 「52.8%（95% 区间 47.3%～58.2%）」; a note goes inside the brackets."""
    if r is None or r.get("rate") is None:
        return "—"
    s = f"{100 * r['rate']:.1f}%"
    if not ci:
        return s + (f"（{note}）" if note else "")
    lo, hi = (f"95% 区间 {100 * r['lo']:.1f}%", f"{100 * r['hi']:.1f}%") if long else \
        (f"{100 * r['lo']:.1f}", f"{100 * r['hi']:.1f}")
    return s + f"（{lo}～{hi}" + (f"，{note}" if note else "") + "）"


def _setup_lines(body: dict) -> list[str]:
    n, lay = body["seeds"]["n"], body["seeds"]
    return [(f"每个选手最多三副：{'、'.join(body['arch'])}。不同选手的成员两两一对，自己的三副之间不打；每对 {n} 个发牌种子，"
             f"每个种子两边各坐一次（同一个种子换座位，先后手各一次），一对 {2 * n} 局。默认打法、基线不参加。"
             "平局算半局，作废的局不算。缺交的那一副该打的局全算输（对面算赢）。"), "",
            INTERVAL, "",
            (f"种子：第 k 对（k 从 0 起，顺序见 rr-result.json 的 pairs）用 {lay['lo']} + {lay['span']}k 起的 {n} 个"
             f"（这一次用到 {lay['used'][0]}～{lay['used'][1]}）" if lay["used"] else "种子：没有对")
            + f"；发牌密钥 {body['key'] or '没有'}；模拟器环境 {body['env'] or '没核对上'}；池子在第 {body['pool_period']} 期。"]


def host_text(body: dict) -> str:
    players, s = body["players"], body
    t = body.get("trial")
    head = [f"# 第 {body['period']} 期特殊期评测：选手互打" + (f"（试跑，每对 {t} 个种子）" if t else ""), "",
            "带选手名，只给主持方和 Salem。", ""] + _setup_lines(body) + ["",
            (f"打了 {body['games']['played']} 局：算进来 {body['games']['counted']}（平 {body['games']['draws']}），"
             f"作废 {body['games']['void']}。缺交：{'、'.join(body['missing']) or '没有'}。"), ""]
    if body.get("hold") and t:
        head += ["**作废的局多**：" + "；".join(body["hold"]) + "。见下面「要留意的」。", ""]
    elif body.get("hold"):
        head += ["**先不发给选手**（作废的局多）：" + "；".join(body["hold"]) + "。看过下面「要留意的」、定了要发，再跑一次"
                 "加 --deliver（不打局）。", ""]
    if body["warnings"] or body.get("doubts"):
        head += ["注意：" + "；".join(body["warnings"] + body.get("doubts", [])), ""]
    out = head + ["## 总成绩（对其他所有选手）", "",
                  "| 名次 | 选手 | 胜率（95% 区间） | 局数 | 胜 | 平 | 负 | 作废 | 其中缺交算的局 |", "|" + "---|" * 9]
    for p in s["order"]:
        r = s["totals"][p]
        out.append(f"| {s['ranks'][p]} | {p} | {pct(r)} | {r['games']} | {r['wins']} | {r['draws']} | {r['losses']} | "
                   f"{r['voids']} | {r['missing_games'] or '—'} |")
    out += ["", "## 选手对选手（行对列的胜率，两人之间 9 种原型对局合在一起）", ""] + _grid(players, s["matrix"])
    for _, a, short in ARCH:
        out += ["", f"## {short}对{short}（{a}对{a}）", ""] + _grid(players, s["same_arch"][a], body, a)
    out += ["", "## 每一副", "", "| 选手 | 原型 | 成员 | 回执 | 改动 | " + " | ".join(f"对 {q}" for q in players)
            + " | " + " | ".join(f"对{a}" for a in body["arch"]) + " | 合计 |",
            "|" + "---|" * (6 + len(players) + len(body["arch"]))]
    for p in players:
        for a in body["arch"]:
            name = f"{p}/{a}"
            m, info = s["members"][name], body["members_in"].get(name)
            cells = [p, a, (info["member"] or "—") if info else "缺交", info["receipt"] if info else "—",
                     "—" if not info or info["changes"] is None else str(info["changes"])]
            cells += ["—" if q == p else pct(m["vs_player"][q], ci=False) for q in players]
            cells += [pct(m["vs_arch"][x], ci=False) for x in body["arch"]]
            cells.append(pct(m["total"]))
            out.append("| " + " | ".join(cells) + " |")
    out += ["", "## 要留意的", ""]
    flagged = [r for r in body["pairs"] if r["k"] in body["void_flagged"]]
    out.append("- 作废超过 2% 的对：" + ("、".join(f"第 {r['k']} 对 {r['a']} 对 {r['b']}（{r['voids']} 局，"
                                           f"{100 * r['void_share']:.1f}%）" for r in flagged) or "没有"))
    errs = {}
    for r in body["pairs"]:
        for k, n in r.get("errors", {}).items():
            side, what = k.split(":")
            who = r[side]
            errs.setdefault(who, {}).setdefault(what, 0)
            errs[who][what] += n
    zh = {"crash": "崩溃", "illegal": "非法走法", "timeout": "超时"}
    out.append("- 自己出错判负的局：" + ("；".join(f"{w}：" + "、".join(f"{zh[k]} {n}" for k, n in sorted(e.items()))
                                          for w, e in sorted(errs.items())) or "没有"))
    mv = sorted(((k, m) for k, m in body.get("member_voids", {}).items() if m["voids"]), key=lambda x: -x[1]["share"])
    out.append("- 作废的局（按成员，一局作废两边都记；作废率 = 作废 ÷ 它打了的局）：" + ("；".join(
        f"{k} {m['voids']}/{m['games']}（{100 * m['share']:.1f}%：" + "、".join(f"{w} {n}" for w, n in sorted(
            m["why"].items(), key=lambda x: -x[1])) + "）" for k, m in mv) or "没有"))
    if mv:
        out.append("- 作废的局不算进胜率，两边都不算输。能从原因看出是哪一边造成的（比如某一副的打法载入不了）要不要判那一边输，"
                   "是规则的事，由主持方和 Salem 定，这个工具不替他们定")
    out.append("- 台账里没算进来的：" + ("；".join(body["notes"]) or "没有"))
    return "\n".join(out) + "\n"


def _grid(players, table: dict, body: dict | None = None, arch: str | None = None) -> list[str]:
    out = ["| | " + " | ".join(players) + " |", "|" + "---|" * (len(players) + 1)]
    for p in players:
        cells = []
        for q in players:
            if q == p:
                cells.append("—")
                continue
            r = table[p][q]
            if arch is not None and body is not None:
                me, them = f"{p}/{arch}" in body["members_in"], f"{q}/{arch}" in body["members_in"]
                if not (me and them):
                    cells.append("缺交，全输" if not me else "对面缺交，全赢")
                    continue
            cells.append(pct(r, note="含缺交" if r["missing_games"] else ""))
        out.append(f"| {p} | " + " | ".join(cells) + " |")
    return out


def player_text(body: dict, player: str) -> str:
    """A player's own receipt: their numbers only, no other player's name, list or code."""
    s, n = body, body["seeds"]["n"]
    others = len(body["players"]) - 1
    tot, rank = s["totals"][player], s["ranks"][player]
    out = [f"# 第 {body['period']} 期特殊期评测（选手互打）：你的结果", "",
           (f"这一期的评测只比选手之间：你的每一副和其他 {others} 个选手交的每一副各打 {n} 个发牌种子，每个种子两边各坐一次"
            f"（同一个种子换座位，先后手各一次），一副对一副 {2 * n} 局；你自己的几副之间不打，默认打法和基线不参加。"
            "平局算半局，作废的局不算。哪一副没交，它该打的局全算输（对面算赢）。"), "",
           f"- 总胜率（你的三副对其他 {others} 个选手的所有成员）：{pct(tot, long=True)}，算进来 {tot['games']} 局"
           + (f"（另有作废 {tot['voids']} 局，不算）" if tot["voids"] else ""),
           f"- 名次：{len(body['players'])} 个选手里第 {rank}（按总胜率排，一样的算同一名）", "",
           f"## 三副各自的成绩（对其他 {others} 个选手）", "",
           "| 原型 | 你的成员 | 胜率（95% 区间） | 局数 | 胜 | 平 | 负 | " + " | ".join(f"对{a}" for a in body["arch"]) + " |",
           "|" + "---|" * (7 + len(body["arch"]))]
    for a in body["arch"]:
        name = f"{player}/{a}"
        m, info = s["members"][name], body["members_in"].get(name)
        r = m["total"]
        cells = [a, (info["member"] or "—") if info else "缺交（该打的局全算输）", pct(r), str(r["games"]), str(r["wins"]),
                 str(r["draws"]), str(r["losses"])] + [pct(m["vs_arch"][x], ci=False) for x in body["arch"]]
        out.append("| " + " | ".join(cells) + " |")
    out += ["", (f"「对{body['arch'][0]}」这几列 = 对其他 {others} 个选手同一个原型的那几副合在一起。别的选手要是少交了"
                 "哪一副，那一副该打的局算你赢，也算在这几列和上面的胜率里。"), "", PLAYER_INTERVAL]
    return "\n".join(out) + "\n"


def deliver(body: dict, players_dir: Path) -> dict:
    """Each player's own receipt into their receipts folder (a formal run only)."""
    from ladder.arena import FOLDER
    if body.get("trial"):
        raise EvalError("试跑的结果不发给选手")
    got = {}
    for p in body["players"]:               # one folder that can't be written doesn't keep the others' (submit.deliver)
        try:
            box = Path(players_dir) / FOLDER.get(p, p) / "receipts"
            box.mkdir(parents=True, exist_ok=True)
            f = box / RECEIPT.format(period=body["period"])
            f.write_text(player_text(body, p), encoding="utf-8")
            got[p] = str(f)
        except OSError as e:
            got[p] = f"写不进去：{type(e).__name__}: {e}"
    return got


def dry(host: Path, period: int = 4, trial: int | None = None, players=None, key="auto") -> dict:
    """What a run would do, nothing played or written."""
    players = tuple(players or _players())
    lay = layout(players, period, trial)
    cands, notes, doubts = candidates(host, period, players)
    chk = _checks(host, period, False, key)
    playable = [p for p in lay["pairs"] if p["a"] in cands and p["b"] in cands]
    return {"period": period, "trial": trial, "out": str(_out_dir(host, period, trial)),
            "members": {slot_name(s): ({k: cands[s][k] for k in ("member", "receipt", "spec", "changes")}
                                       if s in cands else "缺交") for s in slots(players)},
            "pairs": len(lay["pairs"]), "playable": len(playable), "games": 2 * lay["n"] * len(playable),
            "seeds": {"per_pair": lay["n"], "first": lay["lo"], "used": lay["used"]},
            "key": chk["key"], "env": chk["env"], "pool_period": chk["pool_period"], "warnings": chk["warnings"],
            "notes": notes, "doubts": doubts, "formal_ready": trial is None and not chk["warnings"] and not doubts}


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", type=int, default=4)
    ap.add_argument("--host", type=Path, default=Path(r"C:\claude\ladder-host"))
    ap.add_argument("--players", type=Path, default=Path(r"C:\claude\ladder-players"))
    ap.add_argument("--arena", type=Path, default=Path(r"C:\claude\ladder-arena"), help="whose lock it takes")
    ap.add_argument("--workers", type=int, default=23)
    ap.add_argument("--mask", type=lambda x: int(x, 0), default=None)
    ap.add_argument("--dry", action="store_true", help="the plan only: nothing played or written")
    ap.add_argument("--trial", type=int, metavar="N", help=f"N seeds a pair from {TRIAL_SEEDS[0]}-{TRIAL_SEEDS[1] - 1}")
    ap.add_argument("--no-deliver", action="store_true")
    ap.add_argument("--no-void-stop", action="store_true", help="play on when a member's games come back void")
    ap.add_argument("--report", action="store_true", help="the formal report again from its logs: no game")
    ap.add_argument("--deliver", action="store_true", help="the receipts from the formal result written: no game")
    a = ap.parse_args(argv)
    out = _out_dir(a.host, a.period, a.trial)
    try:
        if a.dry:
            print(json.dumps(dry(a.host, a.period, a.trial), ensure_ascii=False, indent=1))
            return 0
        if a.deliver:                         # the host has read rr-result.md (a held result, or --no-deliver)
            body = saved(a.host, a.period)
            if body.get("hold"):
                print("这份结果有要留意的（" + "；".join(body["hold"][:4]) + ("……" if len(body["hold"]) > 4 else "")
                      + "），照你说的发。")
            print("放进选手的 receipts：", deliver(body, a.players))
            return 0
        if a.report:
            body = again(a.host, a.period)
            print(f"重出了：{out / (NAME + '.md')}（不发给选手；要发再加 --deliver 跑一次）")
            return 0
        body = evaluate(a.host, a.period, a.workers, a.mask, a.trial, arena=a.arena, void_stop=not a.no_void_stop)
    except EvalError as e:
        print(f"停下：{e}")
        return 1
    except KeyboardInterrupt:
        print("停了（Ctrl+C）。再跑同一条命令接着打：打完的局不重打。")
        return 130
    if a.trial is None and not a.no_deliver:
        if body["hold"]:
            print("先不发给选手：" + "；".join(body["hold"][:4]) + ("……" if len(body["hold"]) > 4 else "")
                  + f"。先看 {out / (NAME + '.md')} 的「要留意的」；看过、定了要发，再跑一次加 --deliver（不打局）")
        else:
            print("放进选手的 receipts：", deliver(body, a.players))
    print(f"完成：{body['games']['played']} 局（作废 {body['games']['void']}），缺交 {len(body['missing'])} 副；"
          f"结果 {out / (NAME + '.md')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
