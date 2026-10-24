"""Smoke test of a deck pairing: errors, time per turn, legal moves per decision, missed lethals.

    python -m svsim.tools.smoke --deck elf-t --opponent ramp-t --games 100 --out smoke-elf.jsonl
    python -m svsim.tools.smoke --report smoke-elf.jsonl smoke-ramp.jsonl
    python -m svsim.tools.smoke --recheck 50000 smoke-elf.jsonl ...     # the turns the probe didn't finish

Games come in pairs on one seed with the seats swapped (as tools.gate), both sides `--agent`. For
each own turn of each side it keeps the wall time of the side's decisions, the most legal actions
at one decision, and a lethal probe: at the start of the turn search.lethal.LethalSearch with
PROBE_NODES (more than the agents' own) looks for a sure lethal (one that wins whatever the deck
order and random results, so the real state is fair to search); a turn the probe found one and the
side did not win in is a missed lethal. Each game keeps its record (tools.records) and each turn the
action it starts at, so `--recheck NODES` can search again, with a bigger budget, only the turns whose
probe ran out of nodes (the architecture session: the probe budget below the agents' own catches the
lethals the agent could have found and didn't, not the ones a budget misses); the report then has two
columns of missed lethals, found by the probe and found only on the recheck. A game that raises is kept with its traceback and the run
goes on; a decision over SLOW seconds or a game over LONG seconds is counted as a timeout. The
condition is tools.gate's: the opponent's 40-card list is known (order and hand not).
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import traceback
from multiprocessing import Pool

PROBE_NODES = 50000     # the agents' own lethal search: 20000
SLOW = 10.0             # seconds for one decision
LONG = 600.0            # seconds for one game


def play_pair(job) -> list[dict]:
    """Seed `seed` twice, `deck` in seat 0 then in seat 1: one result per game."""
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.search.lethal import LethalSearch
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    k, seed, deck, opponent, spec = job[:5]
    nodes = job[5] if len(job) > 5 else PROBE_NODES
    screen = job[6] if len(job) > 6 else None      # search.lethal's screen: a small budget when the damage
                                                   # estimate falls short (the agents' lethal search does too)
    out = []
    for seat in (0, 1):
        cards = [None, None]
        cards[seat], cards[1 - seat] = decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])
        names = [deck, opponent] if seat == 0 else [opponent, deck]
        result = {"k": k, "seed": seed, "seat": seat, "names": names, "turns": [], "error": None,
                  "winner": None, "slow": 0}
        t_game = time.perf_counter()
        try:
            agents = [make_agent(spec, 2 * seed + i) for i in (0, 1)]
            state = new_game(cards[0], cards[1], seed=seed)
            record = R.new_record(cards[0], cards[1], seed, state.first, f"{spec} / {spec}")
            result["record"] = record
            probe = LethalSearch(max_nodes=nodes, seed=seed, screen=screen)
            turn = None
            while not state.over:
                if state.phase == Phase.MAIN and (turn is None or turn["turn"] != state.turn):
                    if turn is not None:
                        turn["won"] = False
                        result["turns"].append(turn)
                    p = state.active
                    found = probe.solve(state.clone())
                    turn = {"turn": state.turn, "player": p, "deck": names[p], "ms": 0.0, "max_legal": 0,
                            "decisions": 0, "lethal": bool(found.sure), "probe_complete": bool(found.complete),
                            "screened": bool(found.screened),
                            "i": len(record["actions"])}
                legal = legal_actions(state)
                t = time.perf_counter()
                action = agents[state.active].act(state, legal)
                dt = time.perf_counter() - t
                result["slow"] += dt > SLOW
                if state.phase == Phase.MAIN and turn is not None:
                    turn["ms"] += 1000 * dt
                    turn["max_legal"] = max(turn["max_legal"], len(legal))
                    turn["decisions"] += 1
                R.add(record, action)
                apply(state, action)
            if turn is not None:
                turn["won"] = state.winner == turn["player"]
                result["turns"].append(turn)
            result["winner"] = state.winner
        except Exception:
            result["error"] = traceback.format_exc()
        result["seconds"] = time.perf_counter() - t_game
        out.append(result)
    return out


def recheck(result: dict, nodes: int, only=None) -> int:
    """Search again with `nodes` the turns of `result` whose probe ran out of nodes without a lethal
    (turn["recheck"]: a sure lethal found then), or only those whose start `i` is in `only`; the number of
    turns searched again."""
    from svsim.search.lethal import LethalSearch
    from svsim.tools import records as R
    todo = {t["i"]: t for t in result["turns"] if not t["probe_complete"] and not t["lethal"] and "i" in t
            and (only is None or t["i"] in only)}
    if not todo or "record" not in result:
        return 0
    probe = LethalSearch(max_nodes=nodes, seed=result["seed"])
    for i, (state, _) in enumerate(R.steps(result["record"])):
        if i in todo:
            todo[i]["recheck"] = bool(probe.solve(state.clone()).sure)
    return sum(1 for t in result["turns"] if "recheck" in t)


def _recheck_job(job):
    line, nodes, only = job
    result = json.loads(line)
    if only is None or only:
        recheck(result, nodes, only)
    return json.dumps(result)


def _pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else float("nan")


def report(results: list[dict]) -> str:
    """Per deck (the side that played it): games, errors, timeouts, time per turn, legal moves, lethals."""
    lines = ["条件：对手卡表已知（牌序、手牌未知）"]
    games = len(results)
    errors = [r for r in results if r["error"]]
    long = sum(r["seconds"] > LONG for r in results)
    lines.append(f"{games} 局：异常 {len(errors)}，超时（单步 >{SLOW:.0f}s 的步数 {sum(r['slow'] for r in results)}，"
                 f"单局 >{LONG:.0f}s 的局数 {long}）")
    for r in errors[:3]:
        lines.append("  异常：" + r["error"].strip().splitlines()[-1])
    by = {}
    for r in results:
        for t in r["turns"]:
            by.setdefault(t["deck"], []).append(t)
    for deck, turns in sorted(by.items()):
        ms = [t["ms"] for t in turns]
        legal = [t["max_legal"] for t in turns]
        lethal = [t for t in turns if t["lethal"]]
        missed = [t for t in lethal if not t["won"]]
        unfinished = [t for t in turns if not t["probe_complete"] and not t["lethal"]]
        rechecked = [t for t in turns if "recheck" in t]
        late = [t for t in rechecked if t["recheck"] and not t["won"]]
        lines.append(f"{deck}：{len(turns)} 个回合，每回合用时中位数 {statistics.median(ms):.0f} ms、"
                     f"90% {_pct(ms, 0.9):.0f} ms、最长 {max(ms):.0f} ms；每回合最多候选行动 中位数 "
                     f"{statistics.median(legal):.0f}、90% {_pct(legal, 0.9)}、最大 {max(legal)}；"
                     f"探针找到必杀 {len(lethal)} 回合，没杀 {len(missed)} 回合"
                     f"（探针没搜完的回合 {sum(not t['probe_complete'] for t in turns)}"
                     + (f"，其中补搜了 {len(rechecked)} / {len(unfinished)} 回合，补搜才找到必杀 "
                        f"{sum(1 for t in rechecked if t['recheck'])} 回合、其中没杀 {len(late)} 回合" if rechecked else "")
                     + "）")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deck", default="elf-t")
    parser.add_argument("--opponent", default="ramp-t")
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--agent", default="mcts:100+plan+learned+phased")
    parser.add_argument("--seed", type=int, default=24000000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--probe-nodes", type=int, default=PROBE_NODES)
    parser.add_argument("--probe-screen", type=int, default=None,
                        help="nodes for a turn whose damage estimate falls short (search.lethal screen; default off)")
    parser.add_argument("--out", default=None)
    parser.add_argument("--report", nargs="+", default=None, help="only print the report of these files")
    parser.add_argument("--recheck", nargs="+", default=None, metavar="NODES FILE",
                        help="search again with NODES the turns the probe didn't finish, in these files (rewritten)")
    parser.add_argument("--recheck-sample", type=int, default=None,
                        help="with --recheck: only this many of a file's unfinished turns, drawn at random (seeded)")
    args = parser.parse_args()
    if args.recheck:
        nodes, paths = int(args.recheck[0]), args.recheck[1:]
        for path in paths:
            lines = open(path, encoding="utf-8").read().splitlines()
            picks = [None] * len(lines)
            if args.recheck_sample is not None:     # a random sample of the unfinished turns, the same each run
                import random
                spots = [(k, t["i"]) for k, line in enumerate(lines) for t in json.loads(line)["turns"]
                         if not t["probe_complete"] and not t["lethal"] and "i" in t]
                chosen = random.Random(len(spots)).sample(spots, min(args.recheck_sample, len(spots)))
                picks = [set() for _ in lines]
                for k, i in chosen:
                    picks[k].add(i)
            with Pool(args.workers) as pool:
                done = list(pool.imap(_recheck_job, [(line, nodes, pick) for line, pick in zip(lines, picks)]))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(done) + "\n")
            print(path)
            print(report([json.loads(line) for line in done]))
        return
    if args.report:
        for path in args.report:
            print(path)
            print(report([json.loads(line) for line in open(path, encoding="utf-8")]))
        return
    jobs = [(k, args.seed + k, args.deck, args.opponent, args.agent, args.probe_nodes, args.probe_screen)
            for k in range(args.games // 2)]
    results = []
    fh = open(args.out, "w", encoding="utf-8") if args.out else None
    with Pool(args.workers) as pool:
        for pair in pool.imap_unordered(play_pair, jobs):
            for r in pair:
                results.append(r)
                if fh:
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
    if fh:
        fh.close()
    print(report(results))


if __name__ == "__main__":
    main()
