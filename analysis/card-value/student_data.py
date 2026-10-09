"""The student's data pipeline, first pairing the original Ramp mirror (student-plan.md; the architecture thread
2026-10-09 02:10: route A, the teacher's T as the training label, 400 G_end items as the validation set).

    python -m svsim.learn.netdata --games 1000 --deck ramp --opponent ramp --agent level-strong --explore 0 \\
        --seed 65800000 --workers 16 --out selfplay_raw.jsonl                               (1. self-play)
    python3 <this> sort selfplay_raw.jsonl --out selfplay.jsonl      (netdata writes games as they finish: sorted by
                                                                      g, a game's line in the file is its g)
    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> positions selfplay.jsonl --out positions.jsonl
    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> teacher selfplay.jsonl positions.jsonl \\
        --out teacher.jsonl [--workers 16]
    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> valitems selfplay.jsonl positions.jsonl \\
        teacher.jsonl --out val_items.jsonl
    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> gend selfplay.jsonl val_items.jsonl \\
        --out val_gend.jsonl [--k 16] [--workers 16]
    cd <svsim checkout> && PYTHONPATH=.:<this folder> python3 <this> labels selfplay.jsonl positions.jsonl \\
        teacher.jsonl --out labels.jsonl        (the student's labels, learn.handvalue.examples_from's format)

The labels (the build line's learn.handvalue.examples_from, 5a250ce): one JSON line per keep:<card> of a position's
principal line whose card is in the mover's hand at the turn start: {"g": the game's line in selfplay.jsonl (= its
g), "i": the action index, "player", "uid": the card (its first copy in hand order), "t": the mean of the two seeds'
T, "seeds": [each seed's T], "se": [each seed's standard error], "split"}. The hold-out split is the same as
examples_from(every=11): a game's line % 11 == 0.

Seeds, all in the data bank 65800000-65899999:
  self-play         netdata --seed 65800000 (its games and agents derive their seeds from it);
  pacing check      student_checks.py pacing: 65890000 + g;
  positions         every own-turn start (first decision of an own turn) of every game, shuffled by
                    Random(65810000), the first 10,000; a position is held out (split "val") when its game's
                    index g % 11 == 0, else "train";
  teacher           position n, seed s (0, 1): 65820000 + 2 n + s (65820000-65839999), teacher_eval.measure (the n30 teacher:
                    mcts-raw:100 base, each restriction re-searched 100 times, the own next turn by a 30-iteration
                    search, 8 determinizations), every restriction of the principal line (keep:<card>, save, noevo);
  validation items  the held-out positions with at least one keep:<card> restriction on a card in hand at the
                    turn start (the teacher's line can also play a card drawn or made during the turn), shuffled by
                    Random(65880000), the first 400, one card each (drawn by the same generator from its keep cards);
  G_end             item n, determinization j (0..2k-1): 65840000 + 100 n + j (65840000-65879999); two arms from the same
                    determinization and agent seeds: keep (c may not leave the hand this turn: played or discarded,
                    the exact check in the search's own veto, salem_discrim.root_keep) and line (the bot's own turn,
                    free), then the bot against itself to the end; G_end = mean(keep - line), the contrast the
                    teacher's keep:<card> measures. Bot mcts:100+plan+learned+phased.

Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import json
import os
import random
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

BANK = 65800000
N_POSITIONS = 10000
N_VAL = 400
HOLD_OUT = 11
GAMES = {}


def _init_games(games):
    GAMES.update(games)


def _lines(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def _state_at(rec, at):
    st = records.start(rec)
    for a in rec["actions"][:at]:
        apply(st, from_dict(a))
    return st


def own_turn_starts(rec):
    """(action index, seat) of the first decision of every turn in the main phase."""
    from svsim.core.enums import Phase
    st = records.start(rec)
    out, last = [], None
    for i, a in enumerate(rec["actions"]):
        if st.over:
            break
        if st.phase == Phase.MAIN and (st.turn, st.active) != last:
            out.append((i, st.active))
            last = (st.turn, st.active)
        apply(st, from_dict(a))
    return out


def positions(args):
    games = _lines(args.selfplay)
    allp = []
    for rec in games:
        for at, seat in own_turn_starts(rec):
            allp.append((rec["g"], at, seat))
    allp.sort()
    random.Random(BANK + 10000).shuffle(allp)
    pick = allp[:N_POSITIONS]
    by_g = {rec["g"]: rec for rec in games}
    with open(args.out, "w", encoding="utf-8") as fh:
        for n, (g, at, seat) in enumerate(pick):
            st = _state_at(by_g[g], at)
            fh.write(json.dumps({"n": n, "g": g, "at": at, "seat": seat, "own_turn": st.players[seat].turns_taken,
                                 "split": "val" if g % HOLD_OUT == 0 else "train"}) + "\n")
    print(f"{len(games)} 局，{len(allp)} 个自己回合的开头，取 {len(pick)} 个"
          f"（留出 {sum(1 for g, _, _ in pick if g % HOLD_OUT == 0)}）")


def _teacher_job(job):
    import teacher_eval as TE
    n, s, g = job
    pos = POS[n]
    gid, at, seed, res = TE.measure((str(g), pos["at"], BANK + 20000 + 2 * n + s, 8, 100, 30, 0))
    return {"n": n, "s": s, "g": g, "at": pos["at"], "seed": seed, "res": res}


POS = {}


def _init_teacher(games, pos):
    import teacher_eval as TE
    GAMES.update(games)
    TE.GAMES.update(games)
    POS.update(pos)


def teacher(args):
    games = {str(r["g"]): r for r in _lines(args.selfplay)}
    pos = {p["n"]: p for p in _lines(args.positions)}
    done = set()
    if os.path.exists(args.out):
        done = {(r["n"], r["s"]) for r in _lines(args.out)}
    jobs = [(n, s, p["g"]) for n, p in sorted(pos.items()) for s in (0, 1) if (n, s) not in done]
    if args.first is not None:                      # smoke tests only
        jobs = [j for j in jobs if j[0] < args.first]
    print(f"{len(pos)} 个局面 × 2 个种子，要量 {len(jobs)}（已完成 {len(done)}）", flush=True)
    with Pool(args.workers, initializer=_init_teacher, initargs=(games, pos)) as pool, \
            open(args.out, "a", encoding="utf-8") as fh:
        for i, row in enumerate(pool.imap_unordered(_teacher_job, jobs, chunksize=4), 1):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            if i % 500 == 0:
                print(f"  {i} / {len(jobs)}", flush=True)


def valitems(args):
    games = {str(r["g"]): r for r in _lines(args.selfplay)}
    pos = {p["n"]: p for p in _lines(args.positions)}
    keeps = {}
    for r in _lines(args.teacher):
        for key in r["res"]:
            if key.startswith("keep:"):
                keeps.setdefault(r["n"], set()).add(int(key.split(":")[1]))
    for n in list(keeps):                 # only cards in hand at the turn start (the student values that hand;
        if pos[n]["split"] != "val":      # a card drawn or made during the turn can't be kept from its start)
            continue
        st = _state_at(games[str(pos[n]["g"])], pos[n]["at"])
        held = {c.defn.card_id for c in st.players[st.active].hand}
        keeps[n] &= held
    cands = sorted(n for n, p in pos.items() if p["split"] == "val" and keeps.get(n))
    rng = random.Random(BANK + 80000)
    rng.shuffle(cands)
    with open(args.out, "w", encoding="utf-8") as fh:
        for i, n in enumerate(cands[:N_VAL]):
            c = rng.choice(sorted(keeps[n]))
            fh.write(json.dumps({"i": i, "n": n, "g": pos[n]["g"], "at": pos[n]["at"], "seat": pos[n]["seat"],
                                 "card": c}) + "\n")
    print(f"留出局面里主线上有牌的 {len(cands)} 个，取 {min(N_VAL, len(cands))} 项")


def _gend_job(job):
    from svsim.core.view import determinize
    import salem_discrim as D
    it, k = job
    st = _state_at(GAMES[str(it["g"])], it["at"])
    me = st.active
    diffs, leak = [], 0
    for j in range(2 * k):
        s = BANK + 40000 + 100 * it["i"] + j
        base = determinize(st, me, random.Random(s))
        keep, lk = D.play_out_fixed(base, me, "keep", 10 * s, it["card"])
        line, _ = D.play_out(base, me, None, 10 * s, it["card"])
        diffs.append(keep - line)
        leak += lk
    return {**it, "k": k, "G_end": sum(diffs) / len(diffs), "G_end1": sum(diffs[:k]) / k,
            "G_end2": sum(diffs[k:]) / k, "samples": diffs, "keep_arm_left": leak}


def gend(args):
    games = {str(r["g"]): r for r in _lines(args.selfplay)}
    items = _lines(args.items)
    done = set()
    if os.path.exists(args.out):
        done = {r["i"] for r in _lines(args.out)}
    jobs = [(it, args.k) for it in items if it["i"] not in done]
    if args.first is not None:                      # smoke tests only
        jobs = [j for j in jobs if j[0]["i"] < args.first]
    print(f"{len(items)} 项，要量 {len(jobs)}（已完成 {len(done)}），每项 2 × {args.k} 个确定化 × 2 支", flush=True)
    with Pool(args.workers, initializer=_init_games, initargs=(games,)) as pool, \
            open(args.out, "a", encoding="utf-8") as fh:
        for i, row in enumerate(pool.imap_unordered(_gend_job, jobs, chunksize=1), 1):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            if i % 20 == 0:
                print(f"  {i} / {len(jobs)}", flush=True)


def sort(args):
    games = sorted(_lines(args.raw), key=lambda r: r["g"])
    gs = [r["g"] for r in games]
    assert gs == list(range(len(gs))), f"games missing or repeated: {len(gs)} lines, g from {gs[0]} to {gs[-1]}"
    with open(args.out, "w", encoding="utf-8") as fh:
        for r in games:
            fh.write(json.dumps(r) + "\n")
    print(f"{len(games)} 局，按 g 排好：第 n 行就是 g = n")


def labels(args):
    games = _lines(args.selfplay)
    assert all(r["g"] == n for n, r in enumerate(games)), "selfplay.jsonl must be sorted by g (the sort step)"
    pos = {p["n"]: p for p in _lines(args.positions)}
    per = {}
    for r in _lines(args.teacher):
        for key, v in r["res"].items():
            if key.startswith("keep:"):
                per.setdefault((r["n"], int(key.split(":")[1])), {})[r["s"]] = v
    out = absent = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for (n, cid), by_seed in sorted(per.items()):
            p = pos[n]
            st = _state_at(games[p["g"]], p["at"])
            me = st.active
            copy = next((c for c in st.players[me].hand if c.defn.card_id == cid), None)
            if copy is None:              # drawn or made during the turn: not a card of the turn-start hand
                absent += 1
                continue
            seeds = [by_seed[s]["teacher"] for s in sorted(by_seed)]
            fh.write(json.dumps({"g": p["g"], "i": p["at"], "player": me, "uid": copy.uid, "card": cid,
                                 "t": sum(seeds) / len(seeds), "seeds": seeds,
                                 "se": [by_seed[s]["se"] for s in sorted(by_seed)], "split": p["split"]}) + "\n")
            out += 1
    print(f"{out} 个标签（回合开头不在手里的牌 {absent} 个，去掉了）")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("positions")
    a.add_argument("selfplay")
    a.add_argument("--out", required=True)
    b = sub.add_parser("teacher")
    b.add_argument("selfplay")
    b.add_argument("positions")
    b.add_argument("--out", required=True)
    b.add_argument("--workers", type=int, default=16)
    b.add_argument("--first", type=int, default=None)
    c = sub.add_parser("valitems")
    c.add_argument("selfplay")
    c.add_argument("positions")
    c.add_argument("teacher")
    c.add_argument("--out", required=True)
    d = sub.add_parser("gend")
    d.add_argument("selfplay")
    d.add_argument("items")
    d.add_argument("--out", required=True)
    d.add_argument("--k", type=int, default=16)
    d.add_argument("--workers", type=int, default=16)
    d.add_argument("--first", type=int, default=None)
    e = sub.add_parser("sort")
    e.add_argument("raw")
    e.add_argument("--out", required=True)
    f = sub.add_parser("labels")
    f.add_argument("selfplay")
    f.add_argument("positions")
    f.add_argument("teacher")
    f.add_argument("--out", required=True)
    args = ap.parse_args()
    {"positions": positions, "teacher": teacher, "valitems": valitems, "gend": gend, "sort": sort,
     "labels": labels}[args.cmd](args)


if __name__ == "__main__":
    main()
