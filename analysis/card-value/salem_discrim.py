"""The discrimination experiment, every playable card (docs/hand-value-design.md section 6; the architecture
thread 18:44, pre-registered in README.md before any of its games): on Salem's own turns, does keeping a card,
played to the end by the bot, agree with what Salem kept?

    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> items SALEM_GAMES TEACHER_ROWS
    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> run SALEM_GAMES TEACHER_ROWS --out rows.jsonl
                                                                         [--k 16] [--workers 16] [--first N]
    python3 <this> report rows.jsonl --t T_ROWS.json --q Q_ROWS.json [--boot 2000]

Items: Salem's 80 turns (the turn starts of TEACHER_ROWS, Salem's first 10 games, his winning turns left out)
and two of the bot's turns from the top 10 (#3, #4, labelled by Salem's stated line); on each, every card id
in the mover's hand that a PlayCard can play at the turn start, or only after pressing the unused bonus play
point. Label: "used" if the mover played or discarded a copy this turn, else "kept" (copies count as one).
For each item, 2 x k determinizations from the mover's seat (own hand known; own deck order, the opponent's
hand and deck from their known 40 cards, the random numbers drawn anew), the same determinization and agent
seeds for both arms (common random numbers):
  keep  the bot plays the rest of the turn never playing c;
  use   the bot plays the rest of the turn having to use c: ending the turn is vetoed while no copy of c has
        left the hand and c is affordable (its cost <= play points + the unused bonus point), and so is playing
        another card that would leave too few points for c; once a copy is used, nothing is vetoed;
then the bot against itself, free, to the end. G_end = mean of (keep result - use result), a win-rate
difference (positive: keeping c did better). Agent mcts:100+plan+learned+phased (the G_end of
realized_end.py, whose true-score correlation with G_next passed at 0.82).
Seeds (bank 65500000): item n, determinization j: determinize with 65500000 + 100 n + j; agent seeds
10 x that (+1, +3 as in realized_end.play_out).

Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import json
import os
import random
from collections import defaultdict
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import EndTurn, PlayCard, UseBonusPP, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

import realized as R

BANK = 65500000
V2 = "mcts:100+plan+learned+phased"
EXTRA = {("1791317238047", 53): ("#3", {"Fate of the World"}),
         ("1791304981889", 35): ("#4", {"Spilling Red", "Lyria, Skydestined", "Sagatsumatsu, Fair Beheader"})}
EXTRA_FROM = 400                        # item numbers of #3 / #4 start here
# batch 2 (the architecture thread 20:45, pre-registered before its games): Salem's other 17 games, all the
# original Ramp mirror; the same items, arms, k, bot and exclusion; bank 65600000
BANK2 = 65600000
BATCH2 = ["1791315717152", "1791316090276", "1791316350693", "1791316411815", "1791316540438", "1791316841837",
          "1791316974098", "1791317238047", "1791317476826", "1791317687161", "1791384258804", "1791385092476",
          "1791385225044", "1791385824342", "1791387075633", "1791387160337", "1791387437959"]
GAMES = {}


def _init_games(games):
    """Pool initializer: fill this module's GAMES in each worker (under spawn, as on Windows, a bound
    GAMES.update would only update a pickled copy)."""
    GAMES.update(games)


def state_at(rec, at):
    st = records.start(rec)
    for a in rec["actions"][:at]:
        apply(st, from_dict(a))
    return st


def used_this_turn(rec, at):
    """The card ids the mover played or discarded this turn, and whether the turn won the game."""
    st = state_at(rec, at)
    me, used = st.active, set()
    for a in rec["actions"][at:]:
        if st.over or st.active != me:
            break
        act = from_dict(a)
        before = {c.uid: c.defn.card_id for c in st.players[me].hand}
        apply(st, act)
        still = {c.uid for c in st.players[me].hand}
        used |= {cid for uid, cid in before.items() if uid not in still}
    return used, st.over and st.winner == me


def turn_complete(rec, at):
    """Whether the record goes on past the end of this turn (a game left unfinished can stop inside a turn,
    and then the turn's labels are not Salem's whole choice)."""
    st = state_at(rec, at)
    me = st.active
    for a in rec["actions"][at:]:
        if st.over or st.active != me:
            return True
        apply(st, from_dict(a))
    return st.over or st.active != me


def salem_turn_starts(rec):
    """The action index of the first decision of each of Salem's (seat 0) turns, as teacher_eval.salem_turns."""
    st = records.start(rec)
    acts = [from_dict(a) for a in rec["actions"]]
    i, out = 0, []
    while i < len(acts) and not st.over:
        if st.active != 0 or type(acts[i]).__name__ == "Mulligan":
            apply(st, acts[i])
            i += 1
            continue
        out.append(i)
        while i < len(acts) and st.active == 0 and not st.over:
            apply(st, acts[i])
            i += 1
    return out


def playable(st):
    """Card ids a PlayCard can play now, and those only after pressing the unused bonus point."""
    me = st.active
    now = {st.in_hand(me, a.uid).defn.card_id for a in legal_actions(st) if isinstance(a, PlayCard)}
    later = set()
    if any(isinstance(a, UseBonusPP) for a in legal_actions(st)):
        s2 = st.clone()
        apply(s2, UseBonusPP())
        later = {s2.in_hand(me, a.uid).defn.card_id for a in legal_actions(s2) if isinstance(a, PlayCard)} - now
    return now, later


def items(games, teacher_rows):
    line = {(r["game"], r["at"], int(r["restriction"].split(":")[1])) for r in teacher_rows
            if r["restriction"].startswith("keep:")}
    turns = sorted({(r["game"], r["at"]) for r in teacher_rows})
    out = []
    for g, at in turns:
        used, won = used_this_turn(games[g], at)
        if won:
            continue
        st = state_at(games[g], at)
        now, later = playable(st)
        names = {c.defn.card_id: c.defn.name for c in st.players[st.active].hand}
        for cid in sorted(now | later):
            out.append({"set": "salem80", "game": g, "at": at, "card": cid, "name": names[cid],
                        "label": "used" if cid in used else "kept", "bonus_only": cid in later,
                        "line": (g, at, cid) in line, "own_turn": st.players[st.active].turns_taken})
    for n, it in enumerate(out):
        it["n"] = n
    n = EXTRA_FROM
    for (g, at), (tag, salem_used) in sorted(EXTRA.items(), key=lambda kv: kv[1][0]):
        st = state_at(games[g], at)
        now, later = playable(st)
        names = {c.defn.card_id: c.defn.name for c in st.players[st.active].hand}
        for cid in sorted(now | later):
            out.append({"set": tag, "game": g, "at": at, "card": cid, "name": names[cid], "n": n,
                        "label": "used" if names[cid] in salem_used else "kept", "bonus_only": cid in later,
                        "line": False, "own_turn": st.players[st.active].turns_taken})
            n += 1
    return out


def items2(games):
    """Batch 2: every turn start of Salem's in the 17 games (his winning turns, and a turn the record stops
    inside, left out), the same items as items(); numbered from 0 in their own bank."""
    out = []
    for g in BATCH2:
        for at in salem_turn_starts(games[g]):
            used, won = used_this_turn(games[g], at)
            if won or not turn_complete(games[g], at):
                continue
            st = state_at(games[g], at)
            now, later = playable(st)
            names = {c.defn.card_id: c.defn.name for c in st.players[st.active].hand}
            for cid in sorted(now | later):
                out.append({"set": "salem17", "game": g, "at": at, "card": cid, "name": names[cid],
                            "label": "used" if cid in used else "kept", "bonus_only": cid in later,
                            "line": None, "own_turn": st.players[st.active].turns_taken})
    for n, it in enumerate(out):
        it["n"] = n
    return out


def uses_card(cid, me):
    """The use arm's veto (module docstring): c must leave the hand this turn while it is affordable."""
    def veto(s, a):
        if s.active != me:
            return False
        hand = {c.uid for c in s.players[me].hand}
        if not veto.uids <= hand:
            return False                                  # a copy held at the turn start has left the hand: free
        mine = [c for c in s.players[me].hand if c.uid in veto.uids]
        p = s.players[me]
        spare = p.pp + (1 if p.bonus_ready and not p.bonus_active else 0)
        need = min(c.cost for c in mine)
        if isinstance(a, EndTurn):
            return need <= spare
        if isinstance(a, PlayCard):
            card = s.in_hand(me, a.uid)
            if card is not None and card.defn.card_id != cid:
                return need <= spare and spare - card.cost < need
        return False
    veto.uids = set()
    return veto


def _c_playable(s, me, uids):
    """A copy of c held at the turn start can be played now, or after pressing the unused bonus point."""
    def now(t):
        return any(isinstance(a, PlayCard) and a.uid in uids for a in legal_actions(t))
    if now(s):
        return True
    if any(isinstance(a, UseBonusPP) for a in legal_actions(s)):
        t = s.clone()
        apply(t, UseBonusPP())
        return now(t)
    return False


def root_use(uids, me):
    """The fixed use arm's check on the actual decision (side reading): an action is vetoed if c is playable
    now and would not be after it (playing the action on a copy of the state: enhanced or alternative costs,
    targets that go away, a full board), and ending the turn is vetoed while c is playable; a copy of c
    leaving the hand any way (played or discarded) frees the turn."""
    def veto(s, a):
        hand = {c.uid for c in s.players[me].hand}
        if s.active != me or not uids <= hand:
            return False
        if isinstance(a, PlayCard) and a.uid in uids:
            return False
        if isinstance(a, EndTurn):
            return _c_playable(s, me, uids)
        t = s.clone()
        apply(t, a)
        if not uids <= {c.uid for c in t.players[me].hand}:
            return False
        return _c_playable(s, me, uids) and not _c_playable(t, me, uids)
    return veto


def root_keep(uids, me):
    """The fixed keep arm's check on the actual decision (side reading): no copy of c may leave the hand this
    turn, played or discarded by another card's effect."""
    def veto(s, a):
        if s.active != me:
            return False
        if isinstance(a, PlayCard) and a.uid in uids:
            return True
        t = s.clone()
        apply(t, a)
        return not uids <= {c.uid for c in t.players[me].hand}
    return veto


def play_out_fixed(base, me, arm, seed, cid, strict=False):
    """play_out with the fixed arms: the exact checks (root_use / root_keep) are the search's own veto, so
    they hold at every node of its tree (the search picks its move among its root's children, built through
    the veto; a filter on the legal list handed to act() does nothing, which is why the first version's
    affordability check, on the base cost, let enhanced or alternative-cost plays through)."""
    from svsim.tools.arena import make_agent
    st = base.clone()
    start = {c.uid for c in st.players[me].hand if c.defn.card_id == cid}
    root = root_keep(start, me) if arm == "keep" else root_use(start, me)
    agent = make_agent(V2, seed)
    inner = agent
    while not (hasattr(inner, "search") and hasattr(inner.search, "veto")):
        inner = inner.base
    old = inner.search.veto
    inner.search.veto = (lambda s, a: root(s, a) or old(s, a)) if old else root
    overridden = 0
    while not st.over and st.active == me:
        legal = legal_actions(st)
        allowed = [a for a in legal if not root(st, a)]
        a = agent.act(st, allowed or legal)
        if strict and allowed and a not in allowed:
            # the lethal planner (agents.lethal_agent) plays its line's step whenever it is legal, listed or not
            # (search.combo.listed), so a lethal with c went past the check: under `strict` the inner search
            # chooses instead, its root built through the veto (the student's validation set, 2026-10-09)
            a = inner.act(st, allowed)
            overridden += 1
            if a not in allowed:
                a = next((x for x in allowed if type(x).__name__ == "EndTurn"), allowed[0])
        apply(st, a)
    left = not start <= {c.uid for c in st.players[me].hand}
    agents = {me: make_agent(V2, seed + 3), 1 - me: make_agent(V2, seed + 1)}
    while not st.over:
        apply(st, agents[st.active].act(st, legal_actions(st)))
    result = 1.0 if st.winner == me else 0.0 if st.winner == 1 - me else 0.5
    return (result, left, overridden) if strict else (result, left)


def play_out(base, me, veto, seed, cid):
    """realized_end.play_out, also returning whether a copy of `cid` left the hand during this turn."""
    from svsim.tools.arena import make_agent
    st = base.clone()
    start = {c.uid for c in st.players[me].hand if c.defn.card_id == cid}
    if veto is not None and hasattr(veto, "uids"):
        veto.uids = start
    mine = R.agent_with_veto(V2, seed, veto)
    while not st.over and st.active == me:
        apply(st, mine.act(st, legal_actions(st)))
    left = not start <= {c.uid for c in st.players[me].hand}
    agents = {me: make_agent(V2, seed + 3), 1 - me: make_agent(V2, seed + 1)}
    while not st.over:
        apply(st, agents[st.active].act(st, legal_actions(st)))
    return (1.0 if st.winner == me else 0.0 if st.winner == 1 - me else 0.5), left


def measure(job):
    from svsim.core.view import determinize
    it, k, bank = job[:3]
    variant = job[3] if len(job) > 3 else "plain"
    st = state_at(GAMES[it["game"]], it["at"])
    me = st.active
    diffs, used_keep, used_use = [], 0, 0
    for j in range(2 * k):
        s = bank + 100 * it["n"] + j
        base = determinize(st, me, random.Random(s))
        if variant == "fixed":
            keep, lk = play_out_fixed(base, me, "keep", 10 * s, it["card"])
            use, lu = play_out_fixed(base, me, "use", 10 * s, it["card"])
        else:
            keep, lk = play_out(base, me, R.keeps_card(it["card"]), 10 * s, it["card"])
            use, lu = play_out(base, me, uses_card(it["card"], me), 10 * s, it["card"])
        diffs.append(keep - use)
        used_keep += lk
        used_use += lu
    return {**it, "k": k, "variant": variant, "G_end": sum(diffs) / len(diffs), "G_end1": sum(diffs[:k]) / k,
            "G_end2": sum(diffs[k:]) / k, "samples": diffs, "keep_arm_used": used_keep, "use_arm_used": used_use}


ITEM_KEYS = ("set", "game", "at", "card", "name", "label", "bonus_only", "line", "own_turn", "n")


def run(args):
    GAMES.update(json.load(open(args.games, encoding="utf-8"))["records"])
    if args.redo:                      # the fixed side reading: the flagged items of finished runs, their own seeds
        todo = []
        for path in args.redo:
            for x in open(path, encoding="utf-8"):
                if x.strip():
                    r = json.loads(x)
                    if r["use_arm_used"] < 2 * r["k"] or r["keep_arm_used"] > 0:
                        todo.append({k: v for k, v in r.items() if k in ITEM_KEYS})
    elif args.batch == 2:
        todo = items2(GAMES)
    else:
        todo = items(GAMES, json.load(open(args.teacher, encoding="utf-8")))
    if args.first is not None:
        todo = todo[:args.first]
    done = set()
    if os.path.exists(args.out):
        done = {(json.loads(x)["set"], json.loads(x)["n"]) for x in open(args.out, encoding="utf-8") if x.strip()}
    bank = lambda it: args.seed_base if args.seed_base is not None else BANK2 if it["set"] == "salem17" else BANK
    jobs = [(it, args.k, bank(it), args.variant) for it in todo if (it["set"], it["n"]) not in done]
    print(f"{len(todo)} 项，要量 {len(jobs)} 项（已完成 {len(done)}），每项 2 × {args.k} 个确定化 × 2 支", flush=True)
    with Pool(args.workers, initializer=_init_games, initargs=(GAMES,)) as pool, \
            open(args.out, "a", encoding="utf-8") as fh:
        for i, row in enumerate(pool.imap_unordered(measure, jobs, chunksize=1), 1):
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 10 == 0:
                print(f"  {i} / {len(jobs)}", flush=True)


# ------------------------------------------------------------------------------------------------ report

def _pairs(data, key, group):
    """(wins, pairs) over (kept, used) pairs within each group: per card id across turns, or within a turn."""
    by = defaultdict(lambda: ([], []))
    for d in data:
        if d.get(key) is None:
            continue
        by[group(d)][0 if d["label"] == "kept" else 1].append(d[key])
    w = n = 0
    for kept, used in by.values():
        for a in kept:
            for b in used:
                w += (a > b) + 0.5 * (a == b)
                n += 1
    return w, n


def auc(data, key, how):
    group = {"按牌": lambda d: d["card"], "同回合": lambda d: (d["game"], d["at"]), "合并": lambda d: 0}[how]
    w, n = _pairs(data, key, group)
    return w / n if n else float("nan"), n


def spearman(x, y):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for t in range(i, j + 1):
                r[order[t]] = (i + j) / 2
            i = j + 1
        return r
    a, b = ranks(x), ranks(y)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    cov = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    va, vb = sum((p - ma) ** 2 for p in a) ** 0.5, sum((q - mb) ** 2 for q in b) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


def report(args):
    from statistics import NormalDist
    rows = [json.loads(x) for path in args.rows for x in open(path, encoding="utf-8") if x.strip()]
    T = defaultdict(list)
    for path in args.t or []:
        for r in json.load(open(path, encoding="utf-8")):
            if r["restriction"].startswith("keep:"):
                T[(r["game"], r["at"], int(r["restriction"].split(":")[1]))].append(r["teacher"])
    Q = {}
    for path in args.q or []:
        for r in json.load(open(path, encoding="utf-8")):
            for cid, (lab, v) in r["value"].items():
                Q[(r["game"], r["at"], int(cid))] = v

    def attach(rs):
        out = []
        for r in rs:
            key = (r["game"], r["at"], r["card"])
            out.append({**r, "T": sum(T[key]) / len(T[key]) if T.get(key) else None, "Q": Q.get(key)})
        return out
    data = attach(rows)
    sets = [x for x in ("salem80", "salem17") if any(d["set"] == x for d in data)]
    names_ = {"salem80": "第一批（前 10 局，80 个回合）", "salem17": "第二批（另外 17 局）"}
    main = [d for d in data if d["set"] in sets]
    clean = [d for d in main if d["use_arm_used"] >= d["k"]]
    line = [d for d in clean if d["T"] is not None]
    print("条件：对手卡表已知（牌序、手牌未知）。" + "；".join(
        f"{names_[x]}：{sum(d['set'] == x for d in main)} 项（留 {sum(d['set'] == x and d['label'] == 'kept' for d in main)}，"
        f"用 {sum(d['set'] == x and d['label'] == 'used' for d in main)}），「用」那支有一半以上确定化没用掉 c 的 "
        f"{sum(d['set'] == x and d['use_arm_used'] < d['k'] for d in main)} 项不算" for x in sets) +
        f"；老师主线上的 {len(line)} 项有 T。区间 95%，按 Salem 的回合重抽 {args.boot} 次。\n")
    rel = spearman([d["G_end1"] for d in clean], [d["G_end2"] for d in clean])
    rel32 = 2 * rel / (1 + rel)
    print(f"G_end 两组（各 {clean[0]['k'] if clean else 0} 个确定化）的一致度（秩）：{rel:.3f}；"
          f"折成 32 个确定化的信度（Spearman–Brown）{rel32:.3f}\n")
    turns = sorted({(d["game"], d["at"]) for d in main})
    rng = random.Random(13)
    picks = [[turns[rng.randrange(len(turns))] for _ in turns] for _ in range(args.boot)]

    def boot(sub, f):
        by = defaultdict(list)
        for d in sub:
            by[(d["game"], d["at"])].append(d)
        vals = []
        for pick in picks:
            s_ = [d for t in pick for d in by.get(t, [])]
            v = f(s_)
            if v == v:
                vals.append(v)
        vals.sort()
        return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]) if vals else (float("nan"),) * 2

    def table(title, sub, keys, hows=("按牌", "同回合", "合并")):
        print(f"**{title}**：{len(sub)} 项\n")
        print("| AUC 口径 | " + " | ".join(keys) + " | " + " | ".join(f"G_end − {k}" for k in keys[1:]) + " |")
        print("|---|" + "---|" * (2 * len(keys) - 1))
        for how in hows:
            cells = []
            for k in keys:
                s_ = [d for d in sub if d[k] is not None]
                a, n = auc(s_, k, how)
                lo, hi = boot(s_, lambda x, k=k: auc(x, k, how)[0])
                cells.append(f"{a:.3f}（{lo:.3f}～{hi:.3f}；{n} 对）")
            for k in keys[1:]:
                s_ = [d for d in sub if d[k] is not None]
                a = auc(s_, "G_end", how)[0] - auc(s_, k, how)[0]
                lo, hi = boot(s_, lambda x, k=k: auc(x, "G_end", how)[0] - auc(x, k, how)[0])
                cells.append(f"{a:+.3f}（{lo:+.3f}～{hi:+.3f}）")
            print(f"| {how}{'（主）' if how == '按牌' else ''} | " + " | ".join(cells) + " |")
        print()

    both = len(sets) > 1
    tag = "两批合并" if both else names_[sets[0]]
    table(f"{tag}，全部项（主读：G_end 和 Salem 一致不一致）", clean, ("G_end", "Q"))
    table(f"{tag}，老师主线上的项（主读：G_end 和 T 比）", line, ("G_end", "T", "Q"))
    if both:
        for x in sets:
            table(f"{names_[x]}单独，全部项", [d for d in clean if d["set"] == x], ("G_end", "Q"), ("按牌",))
            table(f"{names_[x]}单独，老师主线上的项", [d for d in line if d["set"] == x], ("G_end", "T", "Q"), ("按牌",))

    # the reading, as pre-registered (README: the three outcomes of design section 6; the additions written after
    # the start and before any data, 19:47; for the merged 27 games the half-width rule, 20:45); order 1 -> 4 -> 2 -> 3
    how = "按牌"
    aG = auc(clean, "G_end", how)[0]
    loG, hiG = boot(clean, lambda x: auc(x, "G_end", how)[0])
    aQ = auc([d for d in clean if d["Q"] is not None], "Q", how)[0]
    lineG = auc(line, "G_end", how)[0]
    loGl, hiGl = boot(line, lambda x: auc(x, "G_end", how)[0])
    dGT = lineG - auc(line, "T", how)[0]
    lo_d, hi_d = boot(line, lambda x: auc(x, "G_end", how)[0] - auc(x, "T", how)[0])
    half = (hi_d - lo_d) / 2
    print(f"**判读（{tag}，主口径「按牌」）**：全部项 G_end {aG:.3f}（{loG:.3f}～{hiG:.3f}），同表 Q 的点估计 {aQ:.3f}；"
          f"主线项 G_end {lineG:.3f}（{loGl:.3f}～{hiGl:.3f}），G_end − T {dGT:+.3f}（{lo_d:+.3f}～{hi_d:+.3f}，半宽 {half:.3f}）")
    if loG <= 0.5:
        if hiG < aQ:
            print(f"→ 第 1 条：分布问题{'（方向相反：上沿 < 0.5）' if hiG < 0.5 else ''}")
        else:
            print("→ 分不开：分布问题或尺子太小（区间含 0.5，上沿 ≥ Q 的点估计），按第 3 条")
    elif hi_d < 0:
        print("→ 第 4 条：老师比终局更像 Salem，不加深老师；记「Salem 的留牌更像短视界判断，或 G_end 噪声」，按第 3 条换大尺子")
    elif lo_d > 0 and loGl > 0.5:
        print("→ 第 2 条：老师的近似有问题，加深老师")
    elif both and half <= 0.12:
        print("→ 第 3 条，并且半宽 ≤ 0.12：在 Salem 的对局能分辨的精度上，老师 ≈ 终局真值，可以当学生的目标"
              "（学生线做不做改由成本和一道门来定）")
    else:
        print("→ 第 3 条：尺子太小" + ("（半宽 > 0.12）" if both else ""))
    print()

    # side readings, not part of the reading
    if args.fixed:
        fixed = {(r["set"], r["n"]): r for r in attach([json.loads(x) for path in args.fixed
                                                         for x in open(path, encoding="utf-8") if x.strip()])}
        swapped = [fixed.get((d["set"], d["n"]), d) for d in main]
        fclean = [d for d in swapped if d["use_arm_used"] >= d["k"]]
        fline = [d for d in fclean if d["T"] is not None]
        n_sw = sum(1 for d in main if (d["set"], d["n"]) in fixed)
        print(f"**副读：修好的两支**（{n_sw} 个有标记的项换成修好的版本，同样的种子；换完以后「用」那支仍有一半以上没用掉的 "
              f"{len(swapped) - len(fclean)} 项不算；「留」那支仍有 c 离手的 {sum(1 for d in fclean if d['keep_arm_used'] > 0)} 项）\n")
        a1 = auc(fclean, "G_end", how)[0]
        l1, h1 = boot(fclean, lambda x: auc(x, "G_end", how)[0])
        a2 = auc(fline, "G_end", how)[0] - auc(fline, "T", how)[0]
        l2, h2 = boot(fline, lambda x: auc(x, "G_end", how)[0] - auc(x, "T", how)[0])
        print(f"- 全部项 G_end 按牌 AUC {a1:.3f}（{l1:.3f}～{h1:.3f}；{len(fclean)} 项）；主线项 G_end − T {a2:+.3f}（{l2:+.3f}～{h2:+.3f}；{len(fline)} 项）\n")
    nd = NormalDist()
    deatt = lambda a: nd.cdf(nd.inv_cdf(min(max(a, 1e-6), 1 - 1e-6)) / rel32 ** 0.5) if rel32 > 0 else float("nan")
    print(f"**副读：去噪后的 AUC（推算）**：按 AUC = Φ(d′/√2)、d′ 按信度 {rel32:.3f} 去衰减（AUC* = Φ(Φ⁻¹(AUC) ÷ √信度)）："
          f"全部项 G_end {aG:.3f} → {deatt(aG):.3f}，主线项 G_end {lineG:.3f} → {deatt(lineG):.3f}。"
          f"T、Q 不做这一步（它们的噪声这里量不出），所以和它们比时只作参考。\n")
    for tag_ in ("#3", "#4"):
        ex = [d for d in data if d["set"] == tag_]
        if not ex:
            continue
        print(f"**{tag_}**（bot 的局面，标签是 Salem 说的走法；不并入 AUC）\n")
        print("| 牌 | Salem | G_end（留 − 用） | 95% | 「用」那支用掉 c 的确定化 |")
        print("|---|---|---|---|---|")
        for d in ex:
            s_ = d["samples"]
            m = sum(s_) / len(s_)
            se = (sum((x - m) ** 2 for x in s_) / (len(s_) - 1) / len(s_)) ** 0.5
            print(f"| {d['name']} | {'留' if d['label'] == 'kept' else '用'} | {m:+.3f} | {m - 1.96 * se:+.3f}～{m + 1.96 * se:+.3f} | "
                  f"{d['use_arm_used']} / {len(s_)} |")
        print()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("items")
    a.add_argument("games")
    a.add_argument("teacher", nargs="?", default=None)
    a.add_argument("--batch", type=int, default=1, choices=(1, 2))
    b = sub.add_parser("run")
    b.add_argument("games")
    b.add_argument("teacher", nargs="?", default=None, help="batch 1's turns and line flags (not used by batch 2)")
    b.add_argument("--out", required=True)
    b.add_argument("--k", type=int, default=16)
    b.add_argument("--workers", type=int, default=16)
    b.add_argument("--first", type=int, default=None)
    b.add_argument("--batch", type=int, default=1, choices=(1, 2))
    b.add_argument("--variant", default="plain", choices=("plain", "fixed"))
    b.add_argument("--redo", nargs="+", default=None, help="fixed side reading: the flagged items of these rows")
    b.add_argument("--seed-base", type=int, default=None, help="smoke tests only: seeds off the banks")
    c = sub.add_parser("report")
    c.add_argument("rows", nargs="+")
    c.add_argument("--t", action="append", default=None)
    c.add_argument("--q", action="append", default=None)
    c.add_argument("--fixed", action="append", default=None, help="rows of the fixed side reading")
    c.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    if args.cmd == "items" and args.batch == 2:
        its = items2(json.load(open(args.games, encoding="utf-8"))["records"])
        print(f"第二批（另外 17 局）：{len({(i['game'], i['at']) for i in its})} 个回合，{len(its)} 项"
              f"（留 {sum(i['label'] == 'kept' for i in its)}、用 {sum(i['label'] == 'used' for i in its)}；"
              f"只有按额外 PP 才打得出 {sum(i['bonus_only'] for i in its)}）；项编号 0～{len(its) - 1}；"
              f"种子 {BANK2}～{BANK2 + 100 * len(its) - 1}")
    elif args.cmd == "items":
        games = json.load(open(args.games, encoding="utf-8"))["records"]
        its = items(games, json.load(open(args.teacher, encoding="utf-8")))
        main80 = [i for i in its if i["set"] == "salem80"]
        print(f"Salem 80 个回合：{len({(i['game'], i['at']) for i in main80})} 个回合，{len(main80)} 项"
              f"（留 {sum(i['label'] == 'kept' for i in main80)}、用 {sum(i['label'] == 'used' for i in main80)}；"
              f"只有按额外 PP 才打得出 {sum(i['bonus_only'] for i in main80)}；老师主线上的 {sum(i['line'] for i in main80)}）")
        for tag in ("#3", "#4"):
            ex = [i for i in its if i["set"] == tag]
            print(f"{tag}：" + "，".join(f"{i['name']}（{'用' if i['label'] == 'used' else '留'}"
                                        f"{'，要按额外 PP' if i['bonus_only'] else ''}）" for i in ex))
        print(f"项编号 0～{len(main80) - 1}、{EXTRA_FROM}～{EXTRA_FROM + len(its) - len(main80) - 1}；"
              f"种子 {BANK}～{BANK + 100 * (EXTRA_FROM + len(its) - len(main80)) - 1}")
    elif args.cmd == "run":
        run(args)
    else:
        report(args)


if __name__ == "__main__":
    main()
