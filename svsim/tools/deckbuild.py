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
2. deals: a deal is a seed and an opponent from the field (the other classes in turn: once a deck holds
   its class, its mirror scores even whichever deck it is, so the old incumbent as an opponent would only
   reward beating its predecessor; run A's first Haven change gained +15% against its predecessor and
   +4% against the rest, 2026-10-29); a deck plays a deal twice, once from each seat, both sides played by --agent,
   and scores its mean (win 1, draw 0.5). Every candidate plays the same deals with its cards in the
   same slots, so the shuffle puts the same slots on the same draws: two decks differ only where a
   swapped card is drawn, and the luck of the deal cancels out in their difference;
3. successive halving: all variants play --stage deals; the better half by mean score (ties broken at
   random) plays the next --stage x 2^k deals, until one is left. The incumbent plays every deal too;
4. confirmation: the last variant and the incumbent play fresh deals (the halving picked the luckiest of
   several, so its own deals overrate it), --batch at a time, with a sequential test on the deal
   differences (tools.gate.llr, H0 = 0, H1 = --h1, error rates 5%) up to --confirm deals; the variant
   replaces the incumbent when H1 is accepted with at least --min-nonzero deals where the two decks
   scored differently, or, when the test reaches the cap undecided, if its mean gain over all the deals
   is more than --at-max standard errors above 0 (a gain near H1 keeps the test between its lines:
   run B's first Forest change, +2.0% +- 0.9% over 560 deals); else nothing changes. The field changes
   at once.
   (A first run on the old pool, 2026-10-28, 124 paired deals: the two decks' deal scores correlate 0.88,
   so the difference's variance is 0.037 against 0.31 unpaired, about 8 times fewer deals for the same
   precision; but 105 of the 124 deals ended with the same score for both, so a difference rests on the
   few deals where a swapped card mattered: hence the floor on those, from the analysis line's review.)

The field moves with every accepted change, so the search has no fixed target and could go round in
circles (each class beating the field of the moment, not getting better). The anchor: round 0's field,
frozen; after every round each incumbent plays it on the same --anchor-deals deals (the same seeds every
round, --anchor-seed on, by default --seed + 900000), and the report prints the curve. A curve that stops rising means the search is circling.
With 7 classes and many rounds, some changes are accepted by luck alone (5% of the changes that
gain nothing); the anchor curve and the final league are the check on them.

Start (round 0): each class's seed decks (--seeds-file: lines "label|deck hash", Rotation hashes of
any class; cards no longer legal are swapped for legal ones of the nearest cost) and --random random
decks (costs drawn from the seed decks' cost curve, or flat without seeds) go through the same halving
against a provisional field (each class's first seed deck, else its first random deck), with
--start-stage deals in the first stage (many candidates, and the search corrects a poor start); the
winner becomes the class's incumbent, no confirmation.

Everything is written to --out: state.json after every class (a rerun resumes from it, with the same
arguments), deals.jsonl one line per deck per deal (for the correlation of paired decks and any
later analysis; a resumed class step plays its deals again, so count each (tag, key, seed) once),
changes.jsonl one line per confirmation. --report prints each class's incumbent
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
ANCHOR_OFFSET = 900_000                    # the anchor's deals by default: seeds --seed + ANCHOR_OFFSET on, every round
# agent options that choose models by the decks' identity (decks.identify, the matchup's models): a deck changed by
# the search isn't recognized and plays on another model, so the search's default agent has none of them
DECK_MODELS = ("learned", "phased", "net", "prior", "puct", "mimic", "timing", "level-", "ruler", "ref")


# --- the pool and decks -------------------------------------------------------------

# --sets: the card sets a run builds from instead of the Rotation (e.g. the Rotation before set 10, for a search in
# the old pool whose records train the deck model that then guides the search in the new one)
SETS: frozenset | None = None


def legal_cards(craft: Craft) -> list:
    """The deck-buildable cards for `craft`: its own and Neutral Rotation cards (cards of SETS, when set) with every
    ability scripted."""
    cards = collectible(craft) if SETS is None else [c for c in collectible(craft, unlimited=True) if c.card_set in SETS]
    missing = set(decks.unimplemented(cards))
    out, names = [], set()
    # one card per name: the copy limit is by name, and a reprint under a new id (Stormy Blast, 10131320 and
    # 10831310) let a deck hold 3 + 1 of it (found in search F's round 0, 10-29)
    for c in (c for c in cards if c not in missing and not c.is_token):
        if c.name not in names:
            names.add(c.name)
            out.append(c)
    return out


def missing_scripts() -> list:
    cards = collectible() if SETS is None else [c for c in collectible(unlimited=True) if c.card_set in SETS]
    return decks.unimplemented(cards)


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
    script) or is a 4th copy gives its slot to a legal card of the nearest cost; short lists are filled at random.
    A reprint counts as the card of the same name the pool keeps, so 3 + 1 Stormy Blast loses only the 4th copy."""
    options = legal_cards(craft)
    legal = {c.card_id for c in options}
    same = {c.name: c.card_id for c in options}
    out, have = [], Counter()
    for i in (same.get(POOL[i].name, i) if i in POOL else i for i in ids[:decks.DECK_SIZE]):
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


def random_ids(craft: Craft, rng: random.Random, curve: Counter | None = None, prefer: list | None = None,
               share: float = 0.0) -> list:
    """A random legal deck: `share` of its slots random cards of `prefer` (the new set's, so that the search
    can start inside an archetype a 1-3 card swap would never assemble), each other slot's cost drawn from
    `curve` (flat without one), then a card of that cost."""
    options = legal_cards(craft)
    by_cost: dict = {}
    for c in options:
        by_cost.setdefault(min(c.cost, 10), []).append(c)
    costs = sorted(by_cost)
    weights = [curve.get(k, 0) + 0.1 for k in costs] if curve else None
    out, have = [], Counter()
    while prefer and len(out) < round(share * decks.DECK_SIZE):
        left = [c for c in prefer if have[c.card_id] < decks.MAX_COPIES]
        if not left:
            break
        out.append(rng.choice(left).card_id)
        have[out[-1]] += 1
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


# --shape: round 0 condenses decks to the make-up of real lists of the class (how many cards three, two and one
# times: --shape-profiles, the pre-set-10 tournament lists), and the variants change cards and copy counts, so
# each class's make-up drifts where the games say. The 10-29 review found the free-form search's decks at 27-31
# different cards (Salem 19:30Z: 「在玩家视角甚至不能叫真卡组」); a fixed 13x3+1 was wrong too (Salem 19:40Z: the
# Cutthroat deck holds 37 cards once).
def profiles(path: str) -> dict:
    """Class name -> the (three-, two-, one-of counts) of each list in `path` (read_seeds format)."""
    out: dict = {}
    for _, ids in read_seeds(path):
        c = Counter(ids)
        out.setdefault(craft_of_ids(ids).name, []).append(
            tuple(sum(v == n for v in c.values()) for n in (3, 2, 1)))
    return out


def shaped(ids: list, craft: Craft, rng: random.Random, profile: tuple = (13, 0, 1)) -> list:
    """`ids` condensed to `profile` (n3, n2, n1 cards three, two and one times): the cards it holds most often
    first (ties by chance), then the ones it holds once in a random order; short of cards, random legal ones."""
    have = Counter(ids)
    multi = sorted((i for i in have if have[i] >= 2), key=lambda i: (-have[i], rng.random()))
    single = sorted(i for i in have if have[i] == 1)
    rng.shuffle(single)
    want = sum(profile)
    picks = (multi + single)[:want]
    options = sorted(c.card_id for c in legal_cards(craft))
    while len(picks) < want:
        picks.append(rng.choice([o for o in options if o not in picks]))
    n3, n2, _ = profile
    copies = [3] * n3 + [2] * n2 + [1] * (want - n3 - n2)
    return [i for i, n in zip(picks, copies) for _ in range(n)]


def shift(ids: list, craft: Craft, rng: random.Random) -> list:
    """One copy, in place, from one card the deck holds to another it holds fewer than 3 times (a card whose last
    copy goes leaves the deck)."""
    have = Counter(ids)
    to = sorted(i for i in have if have[i] < decks.MAX_COPIES)
    if not to:
        return type_swap(ids, craft, rng)
    y = rng.choice(to)
    out = list(ids)
    out[rng.choice([k for k, i in enumerate(ids) if i != y])] = y
    return out


def add_new(ids: list, craft: Craft, rng: random.Random, prefer: list | None = None) -> list:
    """One copy of a card the deck doesn't hold in place of one copy of a card it does (half the time costing
    within 1 of it, a quarter of the time one of `prefer`)."""
    have = Counter(ids)
    pool = [c for c in legal_cards(craft) if c.card_id not in have]
    if prefer and rng.random() < 0.25:
        pool = [c for c in pool if c in prefer] or pool
    k = rng.randrange(len(ids))
    out = list(ids)
    out[k] = _pick(pool, rng, Counter(), POOL[ids[k]].cost, near=rng.random() < 0.5).card_id
    return out


def drop(ids: list, craft: Craft, rng: random.Random) -> list:
    """Every copy of one card, in place, given one by one to cards the deck holds fewer than 3 times."""
    have = Counter(ids)
    x = rng.choice(sorted(have))
    left = Counter({i: n for i, n in have.items() if i != x})
    out = list(ids)
    for k in [k for k, i in enumerate(ids) if i == x]:
        room = sorted(i for i in left if left[i] < decks.MAX_COPIES)
        if not room:
            return type_swap(ids, craft, rng)
        y = rng.choice(room)
        out[k] = y
        left[y] += 1
    return out


def type_swap(ids: list, craft: Craft, rng: random.Random, prefer: list | None = None) -> list:
    """Every copy of 1 of the deck's cards (a third of the time 2) given, in place, to a card it doesn't hold:
    half the time one costing within 1 of the card it replaces, a quarter of the time one of `prefer` (the new
    set's); when 2 go, half the time a pair from one set that belong together (a seed and one of its _partners).
    Copy counts stay as they were."""
    options = legal_cards(craft)
    have = Counter(ids)
    gone = rng.sample(sorted(have), 1 if rng.random() < 2 / 3 else min(2, len(have)))
    pool = [c for c in options if c.card_id not in have]
    new: list = []
    if len(gone) == 2 and rng.random() < 0.5:
        seeds = [c for c in pool if prefer and c in prefer] if rng.random() < 0.5 else pool
        seed = rng.choice(seeds or pool)
        mates = [c for c in _partners(seed, pool)[:6]]
        if mates:
            new = [seed.card_id, rng.choice(mates).card_id]
    for g in gone[len(new):]:
        left = [c for c in pool if c.card_id not in new]
        if prefer and rng.random() < 0.25:
            left = [c for c in left if c in prefer] or left
        new.append(_pick(left, rng, Counter(), POOL[g].cost, near=rng.random() < 0.5).card_id)
    swap = dict(zip(gone, new))
    return [swap.get(i, i) for i in ids]


def consolidate(ids: list, craft: Craft, rng: random.Random) -> list:
    """`ids` with 1 or 2 slots of cards it holds once given more copies of a card it already holds (up to 3): real
    lists are a dozen full sets, and swaps of random cards almost never build one (the 10-29 review found the
    search's decks at 27-31 different cards, 1-4 of them three times). Falls back to variant when it can't."""
    have = Counter(ids)
    grow = sorted(i for i in have if have[i] < decks.MAX_COPIES)
    if not grow:
        return variant(ids, craft, rng)
    c = rng.choice(grow)
    n = min(rng.randint(1, 2), decks.MAX_COPIES - have[c])
    singles = [k for k, i in enumerate(ids) if have[i] == 1 and i != c]
    if len(singles) < n:
        return variant(ids, craft, rng)
    out = list(ids)
    for k in rng.sample(singles, n):
        out[k] = c
    return out


def _partners(seed, options: list) -> list:
    """`options` of the seed's card set except the seed, closest to it first: cards naming a card the seed names
    (the same token or amulet) before the rest, each group by cosine between standardized static rows."""
    import numpy as np
    from svsim.learn.tokens import static
    same = [c for c in options if c.card_set == seed.card_set and c.card_id != seed.card_id]
    if not same:
        return []
    rows = np.stack([static(c) for c in [seed] + same]).astype(np.float64)
    rows = (rows - rows.mean(0)) / np.where(rows.std(0) > 1e-9, rows.std(0), 1.0)
    rows /= np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), 1e-9)
    cos = rows[1:] @ rows[0]
    named = set(seed.related) | {seed.card_id}
    order = sorted(range(len(same)), key=lambda j: (not set(same[j].related) & named, -cos[j]))
    return [same[j] for j in order]


def package(ids: list, craft: Craft, rng: random.Random, prefer: list | None = None, top: int = 6) -> list:
    """`ids` with every copy of a few of its cards (4 to 6 slots or just over) given to a package: 2-3 copies of a
    seed card (half the time one of `prefer`, the new set's, when given) and the rest from the seed's set, drawn
    among its `top` closest cards (_partners). One step of the search can then try several cards that work
    together, which 1-3 single swaps (variant) would almost never assemble."""
    options = legal_cards(craft)
    have = Counter(ids)
    want, gone = rng.randint(4, 6), []
    for i in rng.sample(sorted(have), len(have)):
        if sum(have[g] for g in gone) >= want:
            break
        gone.append(i)
    slots = [k for k, i in enumerate(ids) if i in gone]          # given new cards in place, as variant does
    pool = [c for c in options if c.card_id not in gone]
    seeds = [c for c in (prefer or []) if c in pool] if prefer and rng.random() < 0.5 else pool
    seed = rng.choice(seeds or pool)
    out = list(ids)
    have = Counter(i for i in ids if i not in gone)
    fill = [seed.card_id] * min(decks.MAX_COPIES - have[seed.card_id], len(slots), rng.randint(2, 3))
    have[seed.card_id] += len(fill)
    near = _partners(seed, pool)[:top]
    while len(fill) < len(slots):
        left = [c for c in near if have[c.card_id] < decks.MAX_COPIES]
        if not left:
            break
        c = rng.choice(left)
        n = min(rng.randint(1, 3), decks.MAX_COPIES - have[c.card_id], len(slots) - len(fill))
        fill += [c.card_id] * n
        have[c.card_id] += n
    while len(fill) < len(slots):
        fill.append(_pick(pool, rng, have).card_id)
        have[fill[-1]] += 1
    for k, i in zip(slots, fill):
        out[k] = i
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
    points, touched = [], []
    for seat in (0, 1):
        cards = [None, None]
        cards[seat], cards[1 - seat] = mine, theirs
        state = new_game(cards[0], cards[1], seed=seed)
        me = state.players[seat]
        slot = {uid: k for k, uid in enumerate(sorted(c.uid for c in me.deck + me.hand))}   # made in list order
        seen = {slot[c.uid] for c in me.hand}
        agents = [None, None]
        agents[seat] = make_agent(spec, 2 * seed + seat)
        agents[1 - seat] = make_agent(spec, 2 * seed + 1 - seat + 7919)
        while not state.over:
            apply(state, agents[state.active].act(state, legal_actions(state)))
        points.append(1.0 if state.winner == seat else 0.5 if state.winner not in (0, 1) else 0.0)
        left = {c.uid for c in me.deck}
        touched.append(sorted(seen | {k for uid, k in slot.items() if uid not in left}))
        if seat == 0:
            first = state.first
    # both lists as deck codes, so the records alone can train a model of deck strength (deck, opponent, score)
    # touched: per game, the deck's slots that were in the opening hand or left the deck (screened halving)
    return {"key": key, "seed": seed, "points": points, "first": first, "deck": deck_hash(ids), "opp": deck_hash(opp),
            "touched": touched}


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
    except (OSError, AttributeError):          # Windows has no os.nice: start the run at low priority there
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
        self.model = None

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

    def play(self, decklists: dict, deals: list, tag: str, screen: str | None = None) -> dict:
        """Each deck of `decklists` (key -> ids) on each deal; key -> list of deal scores in deal order. With
        `screen` (the incumbent's key) the incumbent plays first, and a deck that differs from it only in slots
        neither of its two games touched (opening hand or drawn) takes its score on that deal unplayed: up to
        the first touched changed slot the games are the same, so the difference such a deal adds is 0 (the
        search's own sampling of the unseen deck can still differ; screening is for the halving only)."""
        for ids in [*decklists.values(), *(opp for _, opp in deals)]:
            # a registered deck redraws by its own data (agents.mulligan) and is filed under its name
            # (new_game's deck_name): its variants, unrecognized, wouldn't be, and a card swap would mix with a
            # change of redraw (the builder's review, 2026-10-28)
            name = decks.identify([POOL[i] for i in ids])
            if name is not None:
                raise ValueError(f"a registered deck ({name}) is in the search")
        order = {seed: j for j, (seed, _) in enumerate(deals)}
        got = {k: [None] * len(deals) for k in decklists}
        rest = dict(decklists)
        with open(self.out / "deals.jsonl", "a", encoding="utf-8") as fh:
            def run(lists, skip=frozenset()):
                jobs = [(k, ids, opp, seed, self.args.agent) for k, ids in lists.items() for seed, opp in deals
                        if (k, seed) not in skip]
                out = {}
                for res in self.pool.imap_unordered(play_deal, jobs):
                    got[res["key"]][order[res["seed"]]] = sum(res["points"]) / 2
                    fh.write(json.dumps({"tag": tag, **res}) + "\n")
                    out[res["seed"]] = res
                return out
            skip = set()
            if screen is not None:
                base = run({screen: rest.pop(screen)})
                inc = decklists[screen]
                for k, ids in rest.items():
                    changed = {j for j, (a, b) in enumerate(zip(ids, inc)) if a != b}
                    for seed, _ in deals:
                        if not changed & set(base[seed]["touched"][0]) and not changed & set(base[seed]["touched"][1]):
                            skip.add((k, seed))
                            got[k][order[seed]] = got[screen][order[seed]]
                            fh.write(json.dumps({"tag": tag, **base[seed], "key": k, "deck": deck_hash(ids),
                                                 "screened": True}) + "\n")
            run(rest, skip)
        return got

    def halving(self, cands: dict, incumbent: tuple | None, field: dict, tag: str, first: int | None = None) -> tuple:
        """Successive halving of `cands` (key -> ids), the incumbent (key, ids) playing every deal; returns
        (survivor key, {key: scores}) with each key's scores over the deals it played."""
        scores = {k: [] for k in cands}
        if incumbent:
            scores[incumbent[0]] = []
        alive, size, stage = list(cands), first or self.args.stage, 0
        while True:
            deals = self.deals(size, field)
            playing = {k: cands[k] for k in alive}
            if incumbent:
                playing[incumbent[0]] = incumbent[1]
            got = self.play(playing, deals, f"{tag}:s{stage}",
                            screen=incumbent[0] if incumbent and getattr(self.args, "screen", False) else None)
            for k, v in got.items():
                scores[k] += v
            if len(alive) == 1:
                return alive[0], scores
            self.rng.shuffle(alive)                          # ties go by chance, not by the variants' numbers
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
        shape = getattr(self.args, "shape", False)
        for craft in CLASSES:
            cands = dict(by_class.get(craft.name, []))
            prefer = [c for c in legal_cards(craft) if str(c.card_set) == str(self.args.new_set)] \
                if self.args.new_set else None
            for r in range(self.args.random):
                cands[f"random{r}"] = random_ids(craft, self.rng, curve, prefer, self.args.new_share)
            if shape:       # each seed as it is and condensed --shape-tries ways to make-ups of real lists of
                # its class, each random deck condensed once; doubles and registered decks dropped
                prof = profiles(self.args.shape_profiles).get(craft.name) or [(13, 0, 1)]
                out, seen = {}, set()
                for label, ids in cands.items():
                    tries = [None] if label.startswith("random") else [ids]
                    tries += [None] * (0 if label.startswith("random") else self.args.shape_tries - 1)
                    for m, v in enumerate(tries):
                        v = v if v is not None else shaped(ids, craft, self.rng, self.rng.choice(prof))
                        if deck_hash(v) not in seen and decks.identify([POOL[i] for i in v]) is None:
                            seen.add(deck_hash(v))
                            out[f"{label}~{m}"] = v
                cands = out
            cands_by_class[craft.name] = cands
        field = {k: next(iter(v.values())) for k, v in cands_by_class.items()}
        field.update(self.st["field"])                     # resumed: the classes already done keep their decks
        for name, cands in cands_by_class.items():
            if name in self.st["field"]:
                continue
            print(f"[起点] {name}: {len(cands)} 套候选", flush=True)
            others = {k: v for k, v in field.items() if k != name}
            best, scores = self.halving(cands, None, others, f"r0:{name}", self.args.start_stage)
            mean = sum(scores[best]) / len(scores[best])
            self.st["field"][name] = cands[best]
            field[name] = cands[best]
            self.st["history"][name] = [{"round": 0, "from": best, "score": mean}]
            print(f"  → {best}，对临时环境 {mean:.1%}（{len(scores[best])} 个发牌）", flush=True)
            self.save()
        self.st["anchor"] = dict(self.st["field"])           # round 0's field, frozen
        if getattr(self.args, "anchor_file", None):         # or another run's, to put two runs on one scale
            self.st["anchor"] = {craft_of_ids(ids).name: ids for _, ids in read_seeds(self.args.anchor_file)}
        self.anchor()
        self.st["round"] = 1
        self.save()

    def confirm(self, inc: list, cand: list, key: str, field: dict, tag: str) -> tuple:
        """The sequential test of `cand` against the incumbent on fresh deals: ("accepted" | "accepted at the
        cap" | "rejected" | "undecided", the deal differences)."""
        from svsim.tools.gate import bounds, llr
        lo, hi = bounds(0.05, 0.05)
        diff: list = []
        while len(diff) < self.args.confirm:
            deals = self.deals(min(self.args.batch, self.args.confirm - len(diff)), field)
            got = self.play({"incumbent": inc, key: cand}, deals, f"{tag}:confirm")
            diff += [a - b for a, b in zip(got[key], got["incumbent"])]
            value = llr(diff, 0.0, self.args.h1)
            if value <= lo:
                return "rejected", diff
            if value >= hi and sum(d != 0 for d in diff) >= self.args.min_nonzero:
                return "accepted", diff
        # truncated at --confirm deals without a verdict (a gain near H1 keeps the test between its lines): a
        # fixed-sample test on all of them, the gain more than --at-max standard errors above 0
        mean = sum(diff) / len(diff)
        sd = math.sqrt(sum((d - mean) ** 2 for d in diff) / (len(diff) - 1)) if len(diff) > 1 else 0.0
        if sd > 0 and mean > self.args.at_max * sd / math.sqrt(len(diff)) \
                and sum(d != 0 for d in diff) >= self.args.min_nonzero:
            return "accepted at the cap", diff
        return "undecided", diff

    def anchor(self) -> None:
        """Each incumbent on the anchor's fixed deals (the same seeds every round): the round's point of the curve."""
        anchor = self.st["anchor"]
        keys = sorted(anchor, key=lambda k: Craft[k])
        first = self.args.anchor_seed if self.args.anchor_seed is not None else self.args.seed + ANCHOR_OFFSET
        deals = [(first + j, anchor[keys[j % len(keys)]]) for j in range(self.args.anchor_deals)]
        got = self.play(dict(self.st["field"]), deals, f"r{self.st['round']}:anchor")
        point = {k: sum(v) / len(v) for k, v in got.items()}
        self.st.setdefault("anchor_curve", []).append({"round": self.st["round"], **point})
        print(f"[第 {self.st['round']} 轮] 对固定参照：" + "，".join(f"{k} {v:.1%}" for k, v in point.items()), flush=True)

    def one_variant(self, inc: list, craft: Craft) -> list:
        """A package move (package) with probability --package, more copies of a card already held (consolidate)
        with probability --consolidate, else 1-3 single swaps (variant); with both 0 the draws are exactly the
        tool's before these options existed."""
        if getattr(self.args, "shape", False):         # cards and copy counts both move
            prefer = [c for c in legal_cards(craft) if str(c.card_set) == str(self.args.new_set)] \
                if getattr(self.args, "new_set", None) else None
            r = self.rng.random()
            if r < 0.45:
                return type_swap(inc, craft, self.rng, prefer)
            if r < 0.70:
                return shift(inc, craft, self.rng)
            if r < 0.90:
                return add_new(inc, craft, self.rng, prefer)
            return drop(inc, craft, self.rng)
        p = getattr(self.args, "package", 0.0) or 0.0
        q = getattr(self.args, "consolidate", 0.0) or 0.0
        if p or q:
            r = self.rng.random()
            if r < p:
                prefer = [c for c in legal_cards(craft) if str(c.card_set) == str(self.args.new_set)] \
                    if getattr(self.args, "new_set", None) else None
                return package(inc, craft, self.rng, prefer)
            if r < p + q:
                return consolidate(inc, craft, self.rng)
        return variant(inc, craft, self.rng)

    def propose(self, inc: list, craft: Craft, field: dict) -> dict:
        """--variants variants of the incumbent. With --guide MODEL (learn.deckmodel): --guide-pool distinct
        variants, of which the model's best by predicted mean score against `field` and --guide-explore drawn at
        random from the rest; the games still decide."""
        if not getattr(self.args, "guide", None):
            return {f"v{j}": self.one_variant(inc, craft) for j in range(self.args.variants)}
        if self.model is None:
            from svsim.learn.deckmodel import DeckModel
            self.model = DeckModel.load(self.args.guide)
        pool, seen = [], {deck_hash(inc)}
        for _ in range(self.args.guide_pool * 5):
            v = self.one_variant(inc, craft)
            if deck_hash(v) not in seen:
                seen.add(deck_hash(v))
                pool.append(v)
            if len(pool) == self.args.guide_pool:
                break
        opps = list(field.values())
        pred = self.model.predict([v for v in pool for _ in opps], [o for _ in pool for o in opps])
        means = pred.reshape(len(pool), len(opps)).mean(1)
        order = sorted(range(len(pool)), key=lambda j: -means[j])
        explore = min(self.args.guide_explore, self.args.variants)
        picked = order[:self.args.variants - explore]
        rest = order[self.args.variants - explore:]
        picked += self.rng.sample(rest, min(explore, len(rest)))
        return {f"v{j}": pool[k] for j, k in enumerate(picked)}

    def step(self, name: str) -> None:
        craft = Craft[name]
        inc = self.st["field"][name]
        field = {k: v for k, v in self.st["field"].items() if k != name}
        cands = self.propose(inc, craft, field)
        tag = f"r{self.st['round']}:{name}"
        best, scores = self.halving(cands, ("incumbent", inc), field, tag)
        cand_mean = sum(scores[best]) / len(scores[best])
        inc_mean = sum(scores["incumbent"][:len(scores[best])]) / len(scores[best])
        record = {"round": self.st["round"], "class": name, "opponents": sorted(field, key=lambda k: Craft[k]),
                  "halving_best": cand_mean, "halving_incumbent": inc_mean,
                  "out": sorted((counts(inc) - counts(cands[best])).elements()),
                  "in": sorted((counts(cands[best]) - counts(inc)).elements())}
        if cand_mean <= inc_mean:
            record["verdict"] = "no change (halving)"
        else:
            verdict, diff = self.confirm(inc, cands[best], best, field, tag)
            mean = sum(diff) / len(diff)
            sd = math.sqrt(sum((d - mean) ** 2 for d in diff) / (len(diff) - 1)) if len(diff) > 1 else 0.0
            record.update(confirm_diff=mean, confirm_se=sd / math.sqrt(len(diff)), confirm_deals=len(diff),
                          confirm_nonzero=sum(d != 0 for d in diff), confirm_better=sum(d > 0 for d in diff),
                          confirm_worse=sum(d < 0 for d in diff))
            record["verdict"] = verdict
            if verdict.startswith("accepted"):
                self.st["field"][name] = cands[best]
                self.st["history"][name].append({"round": self.st["round"], "gain": mean,
                                                 "out": record["out"], "in": record["in"]})
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
                self.anchor()
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
        print(f"接受的改动 {len(hist) - 1} 次" + ("；复核时的胜率差：" + "、".join(f"{h['gain']:+.1%}" for h in hist[1:])
                                              if len(hist) > 1 else ""))
    curve = st.get("anchor_curve", [])
    if curve:
        print("\n对固定参照（第 0 轮的环境，每轮同一批发牌）的得分：")
        for name in sorted(st["field"], key=lambda k: Craft[k]):
            print(f"  {name}: " + " → ".join(f"{p[name]:.1%}" for p in curve if name in p))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="run folder: state.json, deals.jsonl, changes.jsonl")
    ap.add_argument("--report", action="store_true", help="print the run's decks and changes, play nothing")
    ap.add_argument("--seed", type=int, help="first seed of the run's seed bank (deals use consecutive seeds)")
    ap.add_argument("--seeds-file", help='seed decks, one "label|deck hash" per line')
    ap.add_argument("--random", type=int, default=8, help="random decks per class in round 0 (8)")
    ap.add_argument("--agent", default="mcts:100+plan", help="the agent playing both sides (mcts:100+plan)")
    ap.add_argument("--new-set", default=None,
                    help="round 0's random decks fill --new-share of their slots with this card set's cards (e.g. 10010)")
    ap.add_argument("--new-share", type=float, default=0.6, help="see --new-set (0.6)")
    ap.add_argument("--shape", action="store_true",
                    help="round 0 condenses seeds and random decks to make-ups of real lists of the class "
                         "(--shape-profiles); variants swap whole cards, move copies, add or drop a card")
    ap.add_argument("--shape-tries", type=int, default=3,
                    help="--shape: candidates per seed deck, itself and the rest condensed (3)")
    ap.add_argument("--shape-profiles", default="analysis/deckbuild/seeds-tournament-2026-10-07.txt",
                    help="--shape: the lists whose make-ups (three-, two-, one-of counts) round 0 draws from")
    ap.add_argument("--anchor-file", help='the anchor decks ("label|deck hash", one per class) instead of round '
                                          "0's field")
    ap.add_argument("--consolidate", type=float, default=0.0,
                    help="share of variants that give 1-2 single-copy slots to more copies of a card already held (0)")
    ap.add_argument("--screen", action="store_true",
                    help="halving plays a variant only on deals where its incumbent touched a changed slot (the "
                         "confirmation and anchors still play every deal)")
    ap.add_argument("--package", type=float, default=0.0,
                    help="share of variants that replace every copy of 1-2 cards with a package of related cards "
                         "from one card set (0: single swaps only)")
    ap.add_argument("--sets", default=None,
                    help='build from these card sets instead of the Rotation: "pre10" (the Rotation before set 10) '
                         'or comma-separated set numbers (10000 is Basic)')
    ap.add_argument("--guide", default=None,
                    help="a learn.deckmodel model: it picks which variants are played (the games still decide)")
    ap.add_argument("--guide-pool", type=int, default=200, help="variants the model ranks per class per round (200)")
    ap.add_argument("--guide-explore", type=int, default=2,
                    help="of --variants, this many drawn at random from the model's rest (2)")
    ap.add_argument("--rounds", type=int, default=10, help="rounds after round 0 (10)")
    ap.add_argument("--variants", type=int, default=8, help="variants per class per round (8)")
    ap.add_argument("--stage", type=int, default=28, help="deals in the halving's first stage, doubled each stage (28)")
    ap.add_argument("--start-stage", type=int, default=7, help="the same in round 0 (7)")
    ap.add_argument("--confirm", type=int, default=560, help="fresh deals for the confirmation at most (560)")
    ap.add_argument("--batch", type=int, default=70, help="confirmation deals between two looks of the test (70)")
    ap.add_argument("--h1", type=float, default=0.02, help="the confirmation's H1: the variant scores this much more (0.02)")
    ap.add_argument("--at-max", type=float, default=2.0,
                    help="at the cap undecided: accept if the gain is this many standard errors above 0 (2.0)")
    ap.add_argument("--min-nonzero", type=int, default=20,
                    help="deals where the two decks scored differently, needed to accept (20)")
    ap.add_argument("--anchor-deals", type=int, default=70, help="the anchor's fixed deals per class per round (70)")
    ap.add_argument("--anchor-seed", type=int, help="first seed of the anchor's deals (default --seed + 900000)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--allow-missing", action="store_true", help="run although some Rotation cards have no script")
    ap.add_argument("--deck-models", action="store_true", help="allow an --agent that picks models by deck identity")
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
    if any(t in args.agent for t in DECK_MODELS) and not args.deck_models:
        ap.error(f"{args.agent} picks models by the decks' identity: a changed deck isn't recognized and falls back "
                 "to other models, so a swap and a change of evaluation would mix (--deck-models to run anyway)")
    if args.sets:
        global SETS
        SETS = decks.ROTATION_PRE10 if args.sets == "pre10" else frozenset(int(x) for x in args.sets.split(","))
        print(f"卡池：第 {sorted(SETS)} 弹，不是现在的轮换", flush=True)
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
