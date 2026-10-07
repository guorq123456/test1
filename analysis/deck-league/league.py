"""Baseline league of the tournament decks: one agent on both sides, every pairing, paired seats, one seed bank.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --decks elf-t nemesis-t ramp-t pirate-t --pairs 150 \
        --agent v2s --seed 25000000 --workers 4 --out league.jsonl.gz
    python3 <this> --report league.jsonl.gz [more.jsonl.gz ...] [--boot 2000]
    (later files replace a game of the same pairing, pair and seat: e.g. the mirrors' second games, --mirror-second)

Every pairing of the decks (the mirrors too) plays --pairs pairs of games: seed s twice, the first deck in
seat 0 then in seat 1 (who goes first comes from the seed, so the first deck goes first in one game of a
pair and second in the other), both sides the same agent (arena spec or version name, seeds 2s and
2s+1), the same seeds s = --seed + k for every pairing. In a mirror the two decks are the same, so
the second game of a pair swaps the agents' seeds (2s+1 in seat 0, 2s in seat 1); otherwise it would
replay the first game move for move (it did in the first run at f631e14: --mirror-second plays those
second games again, into a separate file, and the report counts a repeated game once). Each game is kept as a full record
(svsim.tools.records format, plus the pairing and the seat of the first deck) for later use (deck
inference, teacher data). Condition: the opponent's 40-card list is known (order and hand not), as in
tools.gate.

Report: each pairing's score for its first deck (± 95%, from the pairs), split by who actually went
first; the mirrors' first-player rate; and a Bradley–Terry fit of deck strength on the non-mirror
pairings (logit P(i beats j) = θi − θj, mean θ = 0), with intervals from resampling pairs within each
pairing, as CR on Salem's scale (236 per logit; in brackets the game's steady-state formula,
0.5 + gap/800, which holds within ±175).
"""
import argparse
import gzip
import json
import math
import random
import time
from collections import defaultdict
from itertools import combinations_with_replacement
from multiprocessing import Pool

SALEM_CR_PER_LOGIT = 236.0


def play_pair(job, seats=(0, 1)):
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools import records
    from svsim.tools.arena import VERSIONS, make_agent
    from svsim.ui.session import DECKS
    a, b, k, seed, spec = job
    spec = VERSIONS.get(spec, spec)
    out = []
    for seat_a in seats:
        names = [a, b] if seat_a == 0 else [b, a]
        cards = [decks.build(DECKS[n][1]) for n in names]
        swap = a == b and seat_a == 1               # a mirror's second game: otherwise the same game again
        agents = [make_agent(spec, 2 * seed + (1 - i if swap else i)) for i in (0, 1)]
        t0 = time.perf_counter()
        state = new_game(cards[0], cards[1], seed=seed)
        rec = records.new_record(cards[0], cards[1], seed, state.first, f"{spec} / {spec}")
        rec["names"] = names
        while not state.over:
            action = agents[state.active].act(state, legal_actions(state))
            records.add(rec, action)
            apply(state, action)
        rec["winner"] = state.winner
        out.append({"pair": f"{a}/{b}", "k": k, "seed": seed, "seat_a": seat_a, "first": state.first,
                    "agent_seeds": [2 * seed + (1 - i if swap else i) for i in (0, 1)],
                    "winner": state.winner, "turns": state.turn, "seconds": time.perf_counter() - t0,
                    "record": rec})
    return out


def mirror_second(job):
    return play_pair(job, seats=(1,))


def score_a(g):
    """The first deck's result in a game: 1 / 0.5 / 0."""
    if g["winner"] is None:
        return 0.5
    return 1.0 if g["winner"] == g["seat_a"] else 0.0


def bt_fit(counts, decks_, iters=2000):
    """counts[(i, j)] = (score of i, games), i != j. Logit strengths, mean 0 (simple MM / gradient steps)."""
    theta = {d: 0.0 for d in decks_}
    for _ in range(iters):
        grad = {d: 0.0 for d in decks_}
        for (i, j), (s, n) in counts.items():
            p = 1 / (1 + math.exp(theta[j] - theta[i]))
            grad[i] += s - n * p
            grad[j] -= s - n * p
        for d in decks_:
            theta[d] += 0.5 * grad[d] / max(sum(n for (i, j), (_, n) in counts.items() if d in (i, j)), 1) * 4
        m = sum(theta.values()) / len(theta)
        theta = {d: t - m for d, t in theta.items()}
    return theta


def report(paths, boots):
    latest = {}
    for path in paths:                                       # a later file replaces the same game slot
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            latest[(g["pair"], g["k"], g["seat_a"])] = g
    games = list(latest.values())
    by_pair = defaultdict(lambda: defaultdict(list))         # pairing -> k -> games
    for g in games:
        by_pair[g["pair"]][g["k"]].append(g)
    decks_ = sorted({d for p in by_pair for d in p.split("/")})
    print("条件：对手卡表已知（牌序、手牌未知）；双方同一个 agent；每对同种子、换座位；所有组合用同一个种子库。\n")
    print(f"{'组合':<22}{'局':>6}  前一个卡组的得分（95%）      它先手 / 后手时")
    counts = {}
    pair_scores = {}
    for pair in sorted(by_pair):
        ks = by_pair[pair]
        per_pair = [sum(score_a(g) for g in gs) / len(gs) for gs in ks.values() if len(gs) == 2]
        n = 2 * len(per_pair)
        m = sum(per_pair) / len(per_pair)
        se = math.sqrt(sum((x - m) ** 2 for x in per_pair) / max(len(per_pair) - 1, 1) / len(per_pair))
        allg = [g for gs in ks.values() for g in gs if len(gs) == 2]
        first = [score_a(g) for g in allg if g["first"] == g["seat_a"]]
        second = [score_a(g) for g in allg if g["first"] != g["seat_a"]]
        a, b = pair.split("/")
        tag = "（镜像：先手胜率）" if a == b else ""
        if a == b:
            # a pair whose two games are the same game move for move (the first run's mirrors) counts once
            distinct = []
            for gs in ks.values():
                if len(gs) == 2 and gs[0]["record"]["actions"] == gs[1]["record"]["actions"]:
                    distinct.append(gs[0])
                else:
                    distinct.extend(gs)
            nd = len(distinct)
            fr = sum(1.0 if g["winner"] == g["first"] else 0.5 if g["winner"] is None else 0.0 for g in distinct) / nd
            half = 1.96 * math.sqrt(fr * (1 - fr) / nd)
            print(f"{pair:<22}{nd:>6}  先手胜率 {fr:.1%} ± {half:.1%}{tag}"
                  + (f"（{len(allg) - nd} 局是同一局的重复，只算一次）" if nd < len(allg) else ""))
            continue
        print(f"{pair:<22}{n:>6}  {m:.1%} ± {1.96 * se:.1%}          {sum(first) / len(first):.1%} / {sum(second) / len(second):.1%}")
        pair_scores[pair] = per_pair
        counts[(a, b)] = (sum(per_pair) * 2, n)
    theta = bt_fit(counts, decks_)
    rng = random.Random(17)
    samples = {d: [] for d in decks_}
    for _ in range(boots):
        c = {}
        for pair, xs in pair_scores.items():
            a, b = pair.split("/")
            pick = [xs[rng.randrange(len(xs))] for _ in xs]
            c[(a, b)] = (sum(pick) * 2, 2 * len(pick))
        th = bt_fit(c, decks_, iters=400)
        for d in decks_:
            samples[d].append(th[d])
    print("\nBradley–Terry（不含镜像），CR 按 Salem 刻度（236 / logit），平均为 0：")
    for d in sorted(decks_, key=lambda d: -theta[d]):
        s = sorted(samples[d])
        lo, hi = s[int(0.025 * len(s))], s[int(0.975 * len(s)) - 1]
        print(f"  {d:<12} θ {theta[d]:+.3f}  CR {SALEM_CR_PER_LOGIT * theta[d]:+.0f}"
              f"（{SALEM_CR_PER_LOGIT * lo:+.0f}～{SALEM_CR_PER_LOGIT * hi:+.0f}）")
    print("\n各组合的稳态式 CR 差（0.5 + 差/800，±175 以内成立）：")
    for pair, xs in pair_scores.items():
        m = sum(xs) / len(xs)
        gap = (m - 0.5) * 800
        print(f"  {pair:<22} {gap:+.0f}{'' if abs(gap) <= 175 else '（超出 ±175，公式不成立）'}")
    secs = [g["seconds"] for g in games]
    print(f"\n{len(games)} 局，平均每局 {sum(secs) / len(secs):.1f} 秒")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", nargs="+", default=None)
    ap.add_argument("--mirror-second", action="store_true",
                    help="play only the mirrors' second games (seat-swapped agent seeds), e.g. to complete the first run")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--decks", nargs="+", default=["elf-t", "nemesis-t", "ramp-t", "pirate-t"])
    ap.add_argument("--pairs", type=int, default=150)
    ap.add_argument("--agent", default="v2s")
    ap.add_argument("--seed", type=int, default=25000000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.report:
        report(args.report, args.boot)
        return
    import os
    done = set()
    if os.path.exists(args.out):                        # resume: pairs already played are skipped
        for line in gzip.open(args.out, "rt", encoding="utf-8"):
            g = json.loads(line)
            done.add((g["pair"], g["k"]))
    jobs = [(a, b, k, args.seed + k, args.agent) for k in range(args.pairs)
            for a, b in combinations_with_replacement(args.decks, 2)
            if (f"{a}/{b}", k) not in done and (a == b or not args.mirror_second)]
    t0 = time.perf_counter()
    with Pool(args.workers) as pool, gzip.open(args.out, "at", encoding="utf-8") as fh:
        for n, pair in enumerate(pool.imap_unordered(mirror_second if args.mirror_second else play_pair, jobs,
                                                     chunksize=1), 1):
            for g in pair:
                fh.write(json.dumps(g) + "\n")
            fh.flush()
            if n % 50 == 0:
                print(f"  {n} / {len(jobs)} 对，{time.perf_counter() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
