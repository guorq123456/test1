"""The hero gate: does a pilot X play one deck (the hero) better than the baseline pilot, against a field?

    python -m svsim.tools.herogate --hero bot/T3-RUNE-1 --field analysis/pilot/fields/bot-frozen7.txt \
        --x "mcts:N+plan+setnet=NET+netmid+netany" --base "mcts:100+plan" --opp "mcts:100+plan" \
        --seed 85992000 --pairs 300 --out runs/pilot/gate-g1.jsonl
    python -m svsim.tools.herogate ... --time 24 --seed 85992900          # the time match first

Why (the architecture thread 2026-10-31 23:35Z): a pilot trained for one deck (the elf-t recipe) is measured on that
deck only. Pair k: the hero against the field's k-th other deck in turn (the non-hero decks of the field, k mod their
number), on the deal `seed` + k, from both seats; X pilots the hero in two games, the baseline in two more on the same
deals and seats, against the same opponent agent with the same agent seeds (tools.deckgate.play_game: the hero's
side 2 x seed + seat, the opponent's 2 x seed + 1 - seat + 7919). The pair's difference is the mean of X's two games
minus the mean of the baseline's two (win 1, draw 0.5); the report gives X's score, the baseline's, and the paired
difference with a 95% interval over pairs, by opponent too.

The time match (the gate's rule): --time K plays K pairs and compares X's CPU per searched decision with the
baseline's (both piloting the hero, the same deals); within 0.97-1.03 X's N stays, else N = round(N / ratio), once.
Time it with BLAS on one thread (tools.deckgate).

Results go to --out one pair per line; a rerun with the same arguments resumes from it.

Condition: 对手卡表已知（牌序、手牌未知）.
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


def opponents(field: list, hero: str) -> list:
    """The field's decks other than the hero, in file order."""
    if sum(1 for label, _ in field if label == hero) != 1:
        raise SystemExit(f"--hero {hero}: not exactly one deck of the field has that label")
    return [i for i, (label, _) in enumerate(field) if label != hero]


def play_pair(job) -> dict:
    """Pair k: the hero against deck `opp` on `seed`, X then the baseline piloting it, from both seats."""
    from svsim.cards.pool import POOL
    from svsim.tools.deckgate import play_game
    k, seed, opp, hero_ids, opp_ids, x_spec, base_spec, opp_spec = job
    hero, other = [POOL[i] for i in hero_ids], [POOL[i] for i in opp_ids]
    games = []
    for arm, spec in (("x", x_spec), ("base", base_spec)):
        for seat in (0, 1):
            cards = [None, None]
            cards[seat], cards[1 - seat] = hero, other
            g = play_game(cards, seat, spec, opp_spec, seed)
            games.append({"arm": arm, "seat": seat, "points": g["points"], "first": g["first"],
                          "hero_cpu": g["x_cpu"], "hero_moves": g["x_moves"], "hero_wall": g["x_wall"],
                          "opp_cpu": g["y_cpu"], "opp_moves": g["y_moves"]})
    return {"k": k, "seed": seed, "opp": opp, "games": games}


def scores(d: dict) -> tuple:
    """(X's mean, the baseline's mean) over the pair's games."""
    x = [g["points"] for g in d["games"] if g["arm"] == "x"]
    b = [g["points"] for g in d["games"] if g["arm"] == "base"]
    return sum(x) / len(x), sum(b) / len(b)


def summary(values: list) -> tuple:
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / max(n - 1, 1)
    return mean, 1.96 * math.sqrt(var / n)


def cpu(done: list, arm: str) -> float:
    """The hero's CPU seconds per searched decision under `arm`."""
    t = sum(g["hero_cpu"] for d in done for g in d["games"] if g["arm"] == arm)
    n = sum(g["hero_moves"] for d in done for g in d["games"] if g["arm"] == arm)
    return t / max(n, 1)


def report(done: list, labels: list) -> list:
    lines = []
    x = [scores(d)[0] for d in done]
    b = [scores(d)[1] for d in done]
    diff = [a - c for a, c in zip(x, b)]
    (mx, ex), (mb, eb), (md, ed) = summary(x), summary(b), summary(diff)
    lines.append(f"{len(done)} 对（X {2 * len(done)} 局、基线 {2 * len(done)} 局）：英雄卡组 X {mx:.1%} ± {ex:.1%}，"
                 f"基线 {mb:.1%} ± {eb:.1%}，配对差 {md:+.1%} ± {ed:.1%}（95% 区间 {md - ed:+.1%}～{md + ed:+.1%}）")
    for opp in sorted({d["opp"] for d in done}):
        sub = [d for d in done if d["opp"] == opp]
        sx = summary([scores(d)[0] for d in sub])[0]
        sb = summary([scores(d)[1] for d in sub])[0]
        sd, se = summary([scores(d)[0] - scores(d)[1] for d in sub])
        lines.append(f"  对 {labels[opp]}：{len(sub)} 对 X {sx:.1%}，基线 {sb:.1%}，差 {sd:+.1%} ± {se:.1%}")
    cx, cb = cpu(done, "x"), cpu(done, "base")
    if cb > 0:
        lines.append(f"英雄每步（搜索过的决定）CPU：X {1000 * cx:.0f} ms，基线 {1000 * cb:.0f} ms，比 {cx / cb:.3f}")
    return lines


def budget(spec: str) -> int | None:
    _, _, n = spec.split("+", 1)[0].partition(":")
    return int(n) if n.isdigit() else None


def time_match(n: int, ratio: float) -> int:
    return n if 0.97 <= ratio <= 1.03 else max(1, round(n / ratio))


def acceptance_line(x_spec: str, hero: str):
    """The acceptance library's pass rates for the hero deck under X's net and prior (analysis/acceptance, process
    item 5), or None when the hero has no positions or X names neither; never stops a gate."""
    import re
    net = re.search(r"(?:^|\+)setnet=([^+]+)", x_spec)
    prior = re.search(r"(?:^|\+)puct=([^+:]+)", x_spec)
    if not (net or prior):
        return None
    try:
        import sys
        folder = Path(__file__).resolve().parents[2] / "analysis" / "acceptance"
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))
        from run import summary_line
        return summary_line(net.group(1) if net else None, prior.group(1) if prior else None, deck=hero)
    except Exception as e:                       # the library is a report, not a gate condition
        return f"验收库：没能运行（{e!r}）"


class _InProcess:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def imap_unordered(self, fn, items):
        return map(fn, items)


def main() -> None:
    from svsim.tools.deckgate import read_field
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hero", required=True, help="the field label of the hero's deck")
    ap.add_argument("--field", required=True, help="the decks (lines label|deck code)")
    ap.add_argument("--x", required=True, help="the pilot under test (arena spec), on the hero's side")
    ap.add_argument("--base", required=True, help="the baseline pilot, on the hero's side")
    ap.add_argument("--opp", required=True, help="the opponents' agent")
    ap.add_argument("--seed", type=int, required=True, help="pair k plays deal seed + k")
    ap.add_argument("--pairs", type=int, default=300)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=None)
    ap.add_argument("--time", type=int, default=0, metavar="K", help="the time match: K pairs, the CPU ratio, N")
    ap.add_argument("--allow-stale", action="store_true",
                    help="let a model trained on other rules through (learn.provenance; printed in the output)")
    args = ap.parse_args()
    field = read_field(args.field)
    labels = [label for label, _ in field]
    hero = labels.index(args.hero) if args.hero in labels else None
    opps = opponents(field, args.hero)
    count = args.time or args.pairs
    done: dict = {}
    if args.out and os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            d = json.loads(line)
            done[d["k"]] = d
    if args.out and os.path.dirname(args.out):
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
    print(f"条件：英雄 {args.hero} 对 {len(opps)} 套对手轮流（{args.field}）；每对 = 一副发牌，X 和基线各坐两边；{CONDITION}",
          flush=True)
    print(f"X = {args.x}\n基线 = {args.base}\n对手 = {args.opp}", flush=True)
    from svsim.learn.provenance import guard            # a model trained on other rules stops the gate
    guard([args.x, args.base, args.opp], args.allow_stale, out=lambda s: print(s, flush=True))
    print("BLAS 线程：" + "，".join(f"{k}={os.environ.get(k, '未设')}" for k in
                                  ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")), flush=True)
    todo = [(k, args.seed + k, opps[k % len(opps)], field[hero][1], field[opps[k % len(opps)]][1], args.x, args.base,
             args.opp) for k in range(count) if k not in done]
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
    for line in report(results, labels):
        print(line, flush=True)
    acceptance = acceptance_line(args.x, args.hero)
    if acceptance:
        print(acceptance, flush=True)
    if args.time:
        ratio = cpu(results, "x") / max(cpu(results, "base"), 1e-12)
        n = budget(args.x)
        if n is not None:
            print(f"时间匹配：X / 基线 = {ratio:.3f} → N {n} → {time_match(n, ratio)}", flush=True)


if __name__ == "__main__":
    main()
