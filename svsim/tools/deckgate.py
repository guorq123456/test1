"""The gate on any decks: is agent X stronger than agent Y when both play decks given by deck code?

    python -m svsim.tools.deckgate --x "mcts:100+plan+setnet=NET+netmid+netany" --y mcts:100+plan \
        --field analysis/deckbuild/fields/B-r1.txt --seed 85800000 --pairs 300 --out runs/t1-x.jsonl
    python -m svsim.tools.deckgate ... --time 12 --seed 85890000      # the time match first (see below)

Why (the architecture thread 2026-10-29 02:30Z): the deck search needs a score of positions shared by every deck,
and the first question is whether a value net trained on one or two decks still helps on decks it never saw.
tools.gate takes ui.session.DECKS names only; this one takes any deck codes (a field file, deckbuild.read_seeds
format: lines "label|deck code").

A pair is one deal (a seed) of one ordered matchup (deck a against deck b, every ordered pair of different decks
of the field in turn, a mirror never): X plays a against Y playing b from both seats, then Y plays a against X
playing b from both seats (4 games, the same seed). So both agents play both decks of the matchup from both seats on
the same deal, and neither deck's strength nor the seat leans the pair; X's pair score is the mean of its 4 games
(win 1, draw 0.5). Agent seeds as tools.gate (X 2 x seed + seat, Y 2 x seed + 1 - seat + 7919).

Reported: X's score with a 95% interval over pairs (each pair once), the sequential test's verdict as tools.gate
(H0 0.5, H1 --h1, normal approximation; the run plays all --pairs: a fixed count), X's score by the deck X played
(the mean of X's 2 games with that deck in each pair where it played it, the interval over those pairs), and both
sides' time per searched decision: CPU seconds (time.process_time, one process per game: this game's own) and wall.

The time match (the gate's rule, the architecture thread): --time K plays K pairs and prints X's and Y's CPU per
searched decision and their ratio; within 0.97-1.03 X's N stays, else N = round(N / ratio), once. Its seeds are
its own (--seed), not the bank's.

Results go to --out one pair per line, and a rerun with the same arguments resumes from it.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from multiprocessing import Pool
from pathlib import Path

CONDITION = "对手卡表已知（牌序、手牌未知）"


def read_field(path: str) -> list:
    """(label, card ids) for each line "label|deck code" (or a bare code) of the field file; '#' starts a comment."""
    from svsim.cards import deckcode
    out = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines()):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        label, _, code = line.rpartition("|")
        _, _, ids = deckcode.decode_deck(code.strip())
        out.append((label.strip() or f"deck{n}", list(ids)))
    return out


def matchups(n: int) -> list:
    """Every ordered pair (i, j) of different decks of a field of n, by offset: (0, 1), (1, 2), ..., (n-1, 0), then
    offset 2, and so on; each block of n plays every deck once as a and once as b, so a count of pairs that isn't a
    multiple of n (n - 1) still plays the decks about equally often."""
    return [(i, (i + d) % n) for d in range(1, n) for i in range(n)]


def _searched(agent):
    from svsim.tools.gate import _search
    return _search(agent)


def play_game(cards, seat: int, x_spec: str, y_spec: str, seed: int) -> dict:
    """One game: X plays cards[seat] in `seat`, Y the other; X's points and both sides' time per searched move."""
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    agents = [None, None]
    agents[seat] = make_agent(x_spec, 2 * seed + seat)
    agents[1 - seat] = make_agent(y_spec, 2 * seed + 1 - seat + 7919)
    searches = [_searched(a) for a in agents]
    state = new_game(cards[0], cards[1], seed=seed)
    cpu, wall = ([], []), ([], [])
    while not state.over:
        side = state.active
        search = searches[side]
        if search is not None:
            search.last_iterations = None
        c0, w0 = time.process_time(), time.perf_counter()
        action = agents[side].act(state, legal_actions(state))
        c1, w1 = time.process_time(), time.perf_counter()
        if search is not None and search.last_iterations is not None:
            cpu[side].append(c1 - c0)
            wall[side].append(w1 - w0)
        apply(state, action)
    points = 1.0 if state.winner == seat else 0.5 if state.winner not in (0, 1) else 0.0
    return {"points": points, "first": state.first,
            "x_cpu": sum(cpu[seat]), "x_wall": sum(wall[seat]), "x_moves": len(cpu[seat]),
            "y_cpu": sum(cpu[1 - seat]), "y_wall": sum(wall[1 - seat]), "y_moves": len(cpu[1 - seat])}


def play_pair(job) -> dict:
    """Pair k: X with deck a, then with deck b, each from both seats, on `seed` (4 games)."""
    from svsim.cards.pool import POOL
    k, seed, a, b, deck_a, deck_b, x_spec, y_spec = job
    da, db = [POOL[i] for i in deck_a], [POOL[i] for i in deck_b]
    games = []
    for x_deck, mine, theirs in ((a, da, db), (b, db, da)):
        for seat in (0, 1):
            cards = [None, None]
            cards[seat], cards[1 - seat] = mine, theirs
            g = play_game(cards, seat, x_spec, y_spec, seed)
            games.append({"x_deck": x_deck, "seat": seat, **g})
    return {"k": k, "seed": seed, "a": a, "b": b, "games": games}


def pair_score(d: dict) -> float:
    return sum(g["points"] for g in d["games"]) / len(d["games"])


def summary(values: list) -> tuple:
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / max(n - 1, 1)
    return mean, 1.96 * math.sqrt(var / n)


def by_deck(done: list) -> dict:
    """X's score by the deck it played: per pair, the mean of X's games with that deck."""
    out: dict = {}
    for d in done:
        per: dict = {}
        for g in d["games"]:
            per.setdefault(g["x_deck"], []).append(g["points"])
        for deck, pts in per.items():
            out.setdefault(deck, []).append(sum(pts) / len(pts))
    return out


def times(done: list) -> dict:
    """Both sides' mean CPU and wall seconds per searched decision, over every game."""
    t = {k: sum(g[k] for d in done for g in d["games"]) for k in
         ("x_cpu", "x_wall", "x_moves", "y_cpu", "y_wall", "y_moves")}
    return {"x_cpu": t["x_cpu"] / max(t["x_moves"], 1), "y_cpu": t["y_cpu"] / max(t["y_moves"], 1),
            "x_wall": t["x_wall"] / max(t["x_moves"], 1), "y_wall": t["y_wall"] / max(t["y_moves"], 1),
            "x_moves": t["x_moves"], "y_moves": t["y_moves"]}


def budget(spec: str) -> int | None:
    """The N of a spec "name:N+options" (mcts:N), or None."""
    _, _, n = spec.split("+", 1)[0].partition(":")
    return int(n) if n.isdigit() else None


def time_match(n: int, ratio: float) -> int:
    """The gate's rule: N unchanged when X / Y time is within 0.97-1.03, else round(N / ratio), once."""
    return n if 0.97 <= ratio <= 1.03 else max(1, round(n / ratio))


def report(done: list, labels: list, h1: float) -> list:
    from svsim.tools.gate import bounds, cr_text, llr
    lines = []
    scores = [pair_score(d) for d in done]
    mean, margin = summary(scores)
    lo, hi = bounds(0.05, 0.05)
    value = llr(scores, 0.5, h1)
    verdict = "H1（X 更强）" if value >= hi else "H0（没有变强）" if value <= lo else "未判定"
    lines.append(f"{len(scores)} 对（{4 * len(scores)} 局）：X 得分 {mean:.1%} ± {margin:.1%}（95% 区间 "
                 f"{mean - margin:.1%}～{mean + margin:.1%}），{cr_text(mean, margin)}，LLR {value:+.2f}"
                 f"（判定线 {lo:.2f} / {hi:.2f}，H1 = {h1:.0%}）→ {verdict}")
    for deck, vals in sorted(by_deck(done).items()):
        m, e = summary(vals)
        lines.append(f"  X 用 {labels[deck]}：{len(vals)} 对 {m:.1%} ± {e:.1%}")
    t = times(done)
    if t["x_moves"] and t["y_moves"]:
            lines.append(f"每步（搜索过的决定）CPU：X {1000 * t['x_cpu']:.0f} ms，Y {1000 * t['y_cpu']:.0f} ms，"
                     f"比 {t['x_cpu'] / t['y_cpu']:.3f}（墙钟 X {1000 * t['x_wall']:.0f} ms，Y {1000 * t['y_wall']:.0f} ms；"
                     f"{t['x_moves']} / {t['y_moves']} 步）")
    first = [g["points"] for d in done for g in d["games"] if g["first"] == g["seat"]]
    second = [g["points"] for d in done for g in d["games"] if g["first"] != g["seat"]]
    if first and second:
        lines.append(f"X 按真实先后手：先手 {len(first)} 局 {sum(first) / len(first):.1%}，"
                     f"后手 {len(second)} 局 {sum(second) / len(second):.1%}")
    return lines


class _InProcess:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def imap_unordered(self, fn, items):
        return map(fn, items)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--x", required=True, help="the agent under test (arena spec)")
    parser.add_argument("--y", required=True, help="the agent it must beat")
    parser.add_argument("--field", required=True, help="the decks (lines label|deck code)")
    parser.add_argument("--seed", type=int, required=True, help="first seed of the bank: pair k plays seed + k")
    parser.add_argument("--pairs", type=int, default=300)
    parser.add_argument("--h1", type=float, default=0.55)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", default=None, help="results (JSON lines; resumed if it exists)")
    parser.add_argument("--time", type=int, default=0, metavar="K",
                        help="the time match: play K pairs, print the CPU ratio and the matched N")
    args = parser.parse_args()
    field = read_field(args.field)
    labels = [label for label, _ in field]
    order = matchups(len(field))
    count = args.time or args.pairs
    done: dict = {}
    if args.out and os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            d = json.loads(line)
            done[d["k"]] = d
    if args.out and os.path.dirname(args.out):
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
    print(f"条件：{len(field)} 套卡组（{args.field}）的 {len(order)} 个非镜像有序对局轮流；每对 = 一副发牌，"
          f"X 打 a 对 Y 打 b、Y 打 a 对 X 打 b，各坐两边（4 局）；{CONDITION}", flush=True)
    print(f"X = {args.x}\nY = {args.y}", flush=True)
    todo = []
    for k in range(count):
        if k in done:
            continue
        a, b = order[k % len(order)]
        todo.append((k, args.seed + k, a, b, field[a][1], field[b][1], args.x, args.y))
    t0 = time.time()
    fh = open(args.out, "a", encoding="utf-8") if args.out else None
    with (Pool(args.workers) if args.workers > 1 else _InProcess()) as pool:
        for res in pool.imap_unordered(play_pair, todo):
            done[res["k"]] = res
            if fh:
                fh.write(json.dumps(res) + "\n")
                fh.flush()
            if len(done) % 25 == 0:
                print(f"  …{len(done)} 对 {time.time() - t0:.0f}s", flush=True)
    if fh:
        fh.close()
    results = [done[k] for k in sorted(done) if k < count]
    for line in report(results, labels, args.h1):
        print(line, flush=True)
    if args.time and times(results)["y_moves"] and times(results)["x_moves"]:
        t = times(results)
        ratio = t["x_cpu"] / t["y_cpu"]
        n = budget(args.x)
        if n is not None:
            print(f"时间匹配：X / Y = {ratio:.3f} → N {n} → {time_match(n, ratio)}", flush=True)


if __name__ == "__main__":
    main()
