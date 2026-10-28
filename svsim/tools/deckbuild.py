"""Deck search: the bot builds its own decks by playing them.

    python -m svsim.tools.deckbuild --out runs/db1 --seed 84800000 --seeds-file seeds.txt --rounds 10 --workers 8
    python -m svsim.tools.deckbuild --out runs/db1 --report

Why (the player, 2026-10-28, after card set 10 came out and set 4 left Rotation): 「让ai尝试自己构筑」.

A deck is judged by games and nothing else: no card has a score of its own, and a change stays only if
the changed deck wins more often than the deck it would replace. Every class keeps one deck, its
incumbent; the seven incumbents are the field. A round goes through the classes in turn; for each:

1. variants: --variants copies of the incumbent, each with 1 to 3 cards swapped (each swap takes a
   card out of one slot and puts a legal card in, half the time one costing within 1 of it), up to
   3 copies of a card, the class's and Neutral Rotation cards only;
2. deals: a deal is a seed and an opponent from the field (the classes in turn, the own class's
   incumbent included); a deck plays a deal twice, once from each seat, both sides played by --agent,
   and scores its mean (win 1, draw 0.5). Every candidate plays the same deals with its cards in the
   same slots, so the shuffle puts the same slots on the same draws: two decks differ only where a
   swapped card is drawn, and the luck of the deal cancels out in their difference;
3. successive halving: all variants play --stage deals; the better half by mean score plays the next
   --stage x 2^k deals, until one is left. The incumbent plays every deal too, never dropped;
4. confirmation: the last variant and the incumbent play --confirm fresh deals (the halving picked
   the luckiest of many, so its own deals overrate it); the variant replaces the incumbent if its
   mean difference on those deals is more than --z (2) standard errors above 0. The field changes at once.
   (A first run on the old pool, 2026-10-28, 124 paired deals: the two decks' deal scores correlate 0.88,
   so the difference's variance is 0.037 against 0.31 unpaired, about 8 times fewer deals for the same
   precision; 105 of the 124 deals ended with the same score for both.)

Start (round 0): each class's seed decks (--seeds-file: lines "label|deck hash", Rotation hashes of
any class; cards no longer legal are swapped for legal ones of the nearest cost) and --random random
decks (costs drawn from the seed decks' cost curve, or flat without seeds) go through the same halving
against a provisional field (each class's first seed deck, else its first random deck); the winner
becomes the class's incumbent, no confirmation.

Everything is written to --out: state.json after every class (a rerun resumes from it, with the same
arguments), deals.jsonl one line per deck per deal (for the correlation of paired decks and any
later analysis), changes.jsonl one line per confirmation. --report prints each class's incumbent
(names, cost curve, deck hash), its accepted changes and its scores.

Refuses to start while some Rotation card has abilities but no script (decks.unimplemented), unless
--allow-missing: a pool with holes would build decks around what happens to be scripted.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

from svsim.cards import decks, deckcode, library  # noqa: F401  (library registers every card script)
from svsim.cards.pool import POOL, collectible
from svsim.core.enums import Craft

CONDITION = "对手卡表已知（牌序、手牌未知）"
CLASSES = [c for c in Craft if c != Craft.NEUTRAL]


# --- the pool and decks -------------------------------------------------------------

def legal_cards(craft: Craft) -> list:
    """The deck-buildable cards for `craft`: its own and Neutral Rotation cards with every ability scripted."""
    cards = collectible(craft)
    missing = set(decks.unimplemented(cards))
    return [c for c in cards if c not in missing and not c.is_token]


def missing_scripts() -> list:
    return decks.unimplemented(collectible())


def counts(ids) -> Counter:
    return Counter(ids)


def craft_of_ids(ids) -> Craft:
    return decks.craft_of([POOL[i] for i in ids])


def deck_hash(ids) -> str:
    return deckcode.encode_deck(deckcode.ROTATION, int(craft_of_ids(ids)), sorted(ids))


def _pick(options, rng: random.Random, have: Counter, cost: int | None = None, near: bool = False):
    """A card from `options` with fewer than 3 copies in `have`; with `near`, one costing within 1 of `cost`
    (any if none does)."""
    ok = [c for c in options if have[c.card_id] < decks.MAX_COPIES]
    if near and cost is not None:
        close = [c for c in ok if abs(c.cost - cost) <= 1]
        ok = close or ok
    return rng.choice(ok)


def legalize(ids: list, craft: Craft, rng: random.Random) -> list:
    """`ids` as a legal deck of `craft`, slot by slot: a card that isn't legal (left Rotation, another class, no
    script) or is a 4th copy gives its slot to a legal card of the nearest cost; short lists are filled at random."""
    options = legal_cards(craft)
    legal = {c.card_id for c in options}
    out, have = [], Counter()
    for i in ids[:decks.DECK_SIZE]:
        if i in legal and have[i] < decks.MAX_COPIES:
            out.append(i)
        else:
            cost = POOL[i].cost if i in POOL else None
            out.append(_pick(options, rng, have, cost, near=True).card_id)
        have[out[-1]] += 1
    while len(out) < decks.DECK_SIZE:
        out.append(_pick(options, rng, have).card_id)
        have[out[-1]] += 1
    return out


def curve_of(decklists: list) -> Counter:
    return Counter(min(POOL[i].cost, 10) for ids in decklists for i in ids)


def random_ids(craft: Craft, rng: random.Random, curve: Counter | None = None) -> list:
    """A random legal deck: each slot's cost drawn from `curve` (flat without one), then a card of that cost."""
    options = legal_cards(craft)
    by_cost: dict = {}
    for c in options:
        by_cost.setdefault(min(c.cost, 10), []).append(c)
    costs = sorted(by_cost)
    weights = [curve.get(k, 0) + 0.1 for k in costs] if curve else None
    out, have = [], Counter()
    while len(out) < decks.DECK_SIZE:
        cost = rng.choices(costs, weights)[0]
        exact = [c for c in by_cost[cost] if have[c.card_id] < decks.MAX_COPIES]
        out.append((rng.choice(exact) if exact else _pick(options, rng, have, cost, near=True)).card_id)
        have[out[-1]] += 1
    return out


def variant(ids: list, craft: Craft, rng: random.Random) -> list:
    """`ids` with 1 to 3 slots given new cards (half the time costing within 1 of the card they replace)."""
    options = legal_cards(craft)
    out = list(ids)
    for slot in rng.sample(range(len(out)), rng.randint(1, 3)):
        have = Counter(out)
        old = out[slot]
        have[old] -= 1
        pool = [c for c in options if c.card_id != old]
        out[slot] = _pick(pool, rng, have, POOL[old].cost, near=rng.random() < 0.5).card_id
    return out


def read_seeds(path: str) -> list:
    """(label, ids) for each line "label|hash" or "hash" of `path`; '#' starts a comment."""
    out = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines()):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        label, _, h = line.rpartition("|")
        _, _, ids = deckcode.decode_deck(h.strip())
        out.append((label.strip() or f"seed{n}", ids))
    return out


# --- games --------------------------------------------------------------------------

def play_deal(job) -> dict:
    """One deck on one deal: the seed twice, the deck in seat 0 then seat 1, against `opp`; both sides `spec`.
    Agent seeds as tools.gate's pairs, so every deck on a deal meets the same opponent agent."""
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    key, ids, opp, seed, spec = job
    mine, theirs = [POOL[i] for i in ids], [POOL[i] for i in opp]
    points = []
    for seat in (0, 1):
        cards = [None, None]
        cards[seat], cards[1 - seat] = mine, theirs
        state = new_game(cards[0], cards[1], seed=seed)
        agents = [None, None]
        agents[seat] = make_agent(spec, 2 * seed + seat)
        agents[1 - seat] = make_agent(spec, 2 * seed + 1 - seat + 7919)
        while not state.over:
            apply(state, agents[state.active].act(state, legal_actions(state)))
        points.append(1.0 if state.winner == seat else 0.5 if state.winner not in (0, 1) else 0.0)
        if seat == 0:
            first = state.first
    return {"key": key, "seed": seed, "points": points, "first": first}


class _InProcess:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def imap_unordered(self, fn, jobs):
        return map(fn, jobs)


def _nice() -> None:
    try:
        os.nice(10)
    except OSError:
        pass


class Search:
    def __init__(self, args):
        self.args = args
        self.out = Path(args.out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.state_path = self.out / "state.json"
        if self.state_path.exists():
            self.st = json.loads(self.state_path.read_text(encoding="utf-8"))
        else:
            self.st = {"next_seed": args.seed, "round": 0, "class_index": 0, "field": {}, "history": {},
                       "args": {k: v for k, v in vars(args).items() if k not in ("report", "workers")}}
        self.rng = random.Random(f"{args.seed}:{self.st['round']}:{self.st['class_index']}")
        self.pool = None

    def save(self) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.st, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.state_path)

    def deals(self, n: int, field: dict) -> list:
        """`n` fresh deals (seed, opponent ids), the field's classes in turn."""
        keys = sorted(field, key=lambda k: Craft[k])
        out = []
        for j in range(n):
            out.append((self.st["next_seed"], field[keys[j % len(keys)]]))
            self.st["next_seed"] += 1
        return out

    def play(self, decklists: dict, deals: list, tag: str) -> dict:
        """Each deck of `decklists` (key -> ids) on each deal; key -> list of deal scores in deal order."""
        jobs = [(k, ids, opp, seed, self.args.agent) for k, ids in decklists.items() for seed, opp in deals]
        order = {seed: j for j, (seed, _) in enumerate(deals)}
        got = {k: [None] * len(deals) for k in decklists}
        with open(self.out / "deals.jsonl", "a", encoding="utf-8") as fh:
            for res in self.pool.imap_unordered(play_deal, jobs):
                got[res["key"]][order[res["seed"]]] = sum(res["points"]) / 2
                fh.write(json.dumps({"tag": tag, **res}) + "\n")
        return got

    def halving(self, cands: dict, incumbent: tuple | None, field: dict, tag: str) -> tuple:
        """Successive halving of `cands` (key -> ids), the incumbent (key, ids) playing every deal; returns
        (survivor key, {key: scores}) with each key's scores over the deals it played."""
        scores = {k: [] for k in cands}
        if incumbent:
            scores[incumbent[0]] = []
        alive, size, stage = list(cands), self.args.stage, 0
        while True:
            deals = self.deals(size, field)
            playing = {k: cands[k] for k in alive}
            if incumbent:
                playing[incumbent[0]] = incumbent[1]
            got = self.play(playing, deals, f"{tag}:s{stage}")
            for k, v in got.items():
                scores[k] += v
            if len(alive) == 1:
                return alive[0], scores
            alive.sort(key=lambda k: -sum(scores[k]) / len(scores[k]))
            alive = alive[:max(1, len(alive) // 2)]
            size, stage = size * 2, stage + 1
            if len(alive) == 1:
                return alive[0], scores

    def start(self) -> None:
        """Round 0: each class's incumbent from its seed decks and random decks."""
        seeds = read_seeds(self.args.seeds_file) if self.args.seeds_file else []
        by_class: dict = {}
        for label, ids in seeds:
            craft = craft_of_ids(ids)
            if craft == Craft.NEUTRAL:
                continue
            by_class.setdefault(craft.name, []).append((label, legalize(ids, craft, self.rng)))
        curve = curve_of([ids for _, ids in seeds]) if seeds else None
        cands_by_class = {}
        for craft in CLASSES:
            cands = dict(by_class.get(craft.name, []))
            for r in range(self.args.random):
                cands[f"random{r}"] = random_ids(craft, self.rng, curve)
            cands_by_class[craft.name] = cands
        field = {k: next(iter(v.values())) for k, v in cands_by_class.items()}
        for name, cands in cands_by_class.items():
            print(f"[起点] {name}: {len(cands)} 套候选", flush=True)
            best, scores = self.halving(cands, None, field, f"r0:{name}")
            mean = sum(scores[best]) / len(scores[best])
            self.st["field"][name] = cands[best]
            field[name] = cands[best]
            self.st["history"][name] = [{"round": 0, "from": best, "score": mean}]
            print(f"  → {best}，对临时环境 {mean:.1%}（{len(scores[best])} 个发牌）", flush=True)
            self.save()
        self.st["round"] = 1
        self.save()

    def step(self, name: str) -> None:
        craft = Craft[name]
        field = dict(self.st["field"])
        inc = field[name]
        cands = {f"v{j}": variant(inc, craft, self.rng) for j in range(self.args.variants)}
        tag = f"r{self.st['round']}:{name}"
        best, scores = self.halving(cands, ("incumbent", inc), field, tag)
        cand_mean = sum(scores[best]) / len(scores[best])
        inc_mean = sum(scores["incumbent"][:len(scores[best])]) / len(scores[best])
        record = {"round": self.st["round"], "class": name, "halving_best": cand_mean, "halving_incumbent": inc_mean,
                  "out": sorted((counts(inc) - counts(cands[best])).elements()),
                  "in": sorted((counts(cands[best]) - counts(inc)).elements())}
        if cand_mean <= inc_mean:
            record["verdict"] = "no change (halving)"
        else:
            deals = self.deals(self.args.confirm, field)
            got = self.play({"incumbent": inc, best: cands[best]}, deals, f"{tag}:confirm")
            diff = [a - b for a, b in zip(got[best], got["incumbent"])]
            mean = sum(diff) / len(diff)
            sd = math.sqrt(sum((d - mean) ** 2 for d in diff) / (len(diff) - 1)) if len(diff) > 1 else 0.0
            se = sd / math.sqrt(len(diff)) if diff else 0.0
            a_inc = sum(got["incumbent"]) / len(diff)
            record.update(confirm_diff=mean, confirm_se=se, confirm_incumbent=a_inc, confirm_deals=len(diff))
            if se > 0 and mean > self.args.z * se:
                record["verdict"] = "accepted"
                self.st["field"][name] = cands[best]
                self.st["history"][name].append({"round": self.st["round"], "score": a_inc + mean,
                                                 "out": record["out"], "in": record["in"]})
            else:
                record["verdict"] = "rejected"
        with open(self.out / "changes.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        names = lambda ids: "、".join(POOL[i].name_zh or POOL[i].name for i in ids)   # noqa: E731
        print(f"[第 {self.st['round']} 轮] {name}: {record['verdict']}；换下 {names(record['out'])}，换上 "
              f"{names(record['in'])}" + (f"；复核差 {record['confirm_diff']:+.1%} ± {record['confirm_se']:.1%}"
                                         if "confirm_diff" in record else ""), flush=True)

    def run(self) -> None:
        workers = self.args.workers
        with (Pool(workers, initializer=_nice) if workers > 1 else _InProcess()) as self.pool:
            if self.st["round"] == 0:
                self.start()
            while self.st["round"] <= self.args.rounds:
                for i in range(self.st["class_index"], len(CLASSES)):
                    self.rng = random.Random(f"{self.args.seed}:{self.st['round']}:{i}")
                    self.step(CLASSES[i].name)
                    self.st["class_index"] = i + 1
                    self.save()
                self.st["round"] += 1
                self.st["class_index"] = 0
                self.save()


def league(args) -> None:
    """--league FILE: every pair of FILE's decks on --deals deals each (seeds from --seed on, both seats per
    deal), both sides --agent; prints each deck's mean score and the score table, writes OUT/league.json."""
    entries = read_seeds(args.league)
    jobs, seed = [], args.seed
    for a in range(len(entries)):
        for b in range(a + 1, len(entries)):
            for _ in range(args.deals):
                jobs.append(((a, b), entries[a][1], entries[b][1], seed, args.agent))
                seed += 1
    table: dict = {}
    workers = args.workers
    with (Pool(workers, initializer=_nice) if workers > 1 else _InProcess()) as pool:
        for res in pool.imap_unordered(play_deal, jobs):
            a, b = res["key"]
            table.setdefault((a, b), []).append(sum(res["points"]) / 2)
    n = len(entries)
    score = [[None] * n for _ in range(n)]
    for (a, b), v in table.items():
        score[a][b] = sum(v) / len(v)
        score[b][a] = 1 - score[a][b]
    means = [sum(x for x in row if x is not None) / (n - 1) for row in score]
    print(f"条件：{CONDITION}；两边都由 {args.agent} 操作；每对 {args.deals} 个发牌（{2 * args.deals} 局）")
    for i in sorted(range(n), key=lambda i: -means[i]):
        print(f"  {means[i]:.1%}  {entries[i][0]}  " + " ".join("  -  " if x is None else f"{x:.0%}".rjust(5)
                                                             for x in score[i]))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "league.json").write_text(json.dumps({"agent": args.agent, "deals": args.deals, "seed": args.seed,
                                                 "decks": [e[0] for e in entries], "score": score, "means": means},
                                                ensure_ascii=False), encoding="utf-8")


def report(out: Path) -> None:
    st = json.loads((out / "state.json").read_text(encoding="utf-8"))
    print(f"第 {st['round']} 轮（已完成 {st['round'] - 1} 轮），条件：{CONDITION}")
    for name, ids in sorted(st["field"].items(), key=lambda kv: Craft[kv[0]]):
        c = Counter(ids)
        curve = Counter(min(POOL[i].cost, 10) for i in ids)
        print(f"\n## {name}  {deck_hash(ids)}")
        print("费用曲线：" + " ".join(f"{k}费{curve[k]}" for k in sorted(curve)))
        for i, n in sorted(c.items(), key=lambda kv: (POOL[kv[0]].cost, kv[0])):
            card = POOL[i]
            print(f"  {n}× {card.name_zh or card.name}（{card.cost}费，{card.name}）")
        hist = st["history"].get(name, [])
        print(f"接受的改动 {len(hist) - 1} 次；得分记录：" + "、".join(f"{h['score']:.1%}" for h in hist))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="run folder: state.json, deals.jsonl, changes.jsonl")
    ap.add_argument("--report", action="store_true", help="print the run's decks and changes, play nothing")
    ap.add_argument("--seed", type=int, help="first seed of the run's seed bank (deals use consecutive seeds)")
    ap.add_argument("--seeds-file", help='seed decks, one "label|deck hash" per line')
    ap.add_argument("--random", type=int, default=8, help="random decks per class in round 0 (8)")
    ap.add_argument("--agent", default="mcts:100+plan", help="the agent playing both sides (mcts:100+plan)")
    ap.add_argument("--rounds", type=int, default=10, help="rounds after round 0 (10)")
    ap.add_argument("--variants", type=int, default=16, help="variants per class per round (16)")
    ap.add_argument("--stage", type=int, default=14, help="deals in the halving's first stage, doubled each stage (14)")
    ap.add_argument("--confirm", type=int, default=140, help="fresh deals for the confirmation (140)")
    ap.add_argument("--z", type=float, default=2.0, help="standard errors the confirmed gain must exceed (2.0)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--allow-missing", action="store_true", help="run although some Rotation cards have no script")
    ap.add_argument("--league", help='round robin of this file\'s decks ("label|deck hash" lines) instead of a search')
    ap.add_argument("--deals", type=int, default=50, help="--league: deals per pair of decks (50)")
    args = ap.parse_args()
    out = Path(args.out)
    if args.report:
        report(out)
        return
    if args.league:
        if args.seed is None:
            ap.error("--seed is required (the analysis line allocates seed banks)")
        league(args)
        return
    if args.seed is None and not (out / "state.json").exists():
        ap.error("--seed is required for a new run (the analysis line allocates seed banks)")
    missing = missing_scripts()
    if missing and not args.allow_missing:
        ap.error(f"{len(missing)} Rotation cards have abilities but no script, e.g. "
                 + ", ".join(c.name for c in missing[:5]))
    t0 = time.time()
    print(f"条件：{CONDITION}；两边都由 {args.agent} 操作", flush=True)
    Search(args).run()
    print(f"完成，用时 {time.time() - t0:.0f}s", flush=True)
    report(out)


if __name__ == "__main__":
    main()
