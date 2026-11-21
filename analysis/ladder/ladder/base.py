"""The base's non-peeking core (phase 1, item 1.2; deviation D1).

Information condition: before the game a seat knows only the opponent's class, not their list, deck order or hand.
During the game it knows what a human player sees: the opponent's class, the cards the opponent has played or shown,
both boards, the size of the opponent's hand and deck, its own hand and its own list.

Three pieces:
- `Tracker` (referee side): follows a game and records, per seat, which of the opponent's cards have become public.
  A card of the opponent's starting 40 is public once it has been on the field or in the leader area, or has left
  the hand / deck (played, discarded, burned, banished: the real game shows it). Cards created after the start
  (tokens, copies, crests) are public. Cards that only moved between the deck and the hand (draws, searches,
  mulligan) stay hidden.
- `public_position(state, me, tracker)`: what the seat `me` may use, built so that it holds nothing secret: the
  opponent's hidden cards that are not public are taken out (only their number is kept), both decks are put in a
  fixed order (by uid), the random generator is reset, the opponent's deck name is blanked. Two real states that
  differ only in secrets give the same public position (tests/test_base.py).
- `sample(pos, guess, rng)`: one full game state consistent with the public position, the opponent's unknown
  cards drawn from the strategy's own guess at the opponent's list (a weighted list of 40-card lists, updated by
  the cards the opponent has shown), both decks shuffled, future randomness reseeded. Search runs on these.

A strategy never receives the real state: only a `PublicPosition` (and through it `sample`).

Known limits (v1, written in public/base-interface.md when phase 2 publishes it):
- a card the opponent gets by an effect is treated as public, though a few effects hide what was given;
- hidden cards the opponent's effects changed in the hand or deck (cost, stats) come back unchanged in a sample;
- per decision one list is drawn from the guess, and when the guess has more cards left than the opponent has
  unknown cards, one random subset of them is used for that decision.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import svsim.cards.library  # noqa: F401  every card script; the engine plays an unregistered card as vanilla
from svsim.core.state import CardInstance, GameState
from svsim.core.view import observe, shuffle

EPS = 0.05        # a guessed list's weight for a shown card it doesn't hold (as analysis/deck-inference, 10-07)
ROOT = Path(__file__).resolve().parents[3]


def craft_of(cards) -> int:
    """A list's class: its most common non-neutral craft (the craft enum's NEUTRAL is 0)."""
    crafts = Counter(int(c.craft) for c in cards if int(c.craft) != 0)
    return crafts.most_common(1)[0][0] if crafts else 0


class Tracker:
    """What each seat has seen of the other's starting cards. Call `before(state)` and `after(state)` around every
    `apply`, on the real state (referee side only)."""

    def __init__(self, state: GameState):
        self.originals = [set(), set()]      # uids of each player's starting 40 (deck + opening hand)
        self.known = [set(), set()]          # of those, the ones that have become public
        self.revealed = [Counter(), Counter()]   # card ids of the public originals, per owner
        self.log = [[], []]                  # (global turn, card id) in the order they became public, per owner
        self.lists = [None, None]            # each player's own starting list (card ids, sorted)
        self.crafts = [0, 0]
        for i, p in enumerate(state.players):
            cards = p.hand + p.deck_view()
            self.originals[i] = {c.uid for c in cards}
            self.lists[i] = tuple(sorted(c.defn.card_id for c in cards))
            self.crafts[i] = craft_of(c.defn for c in cards)
        self._hidden = None
        self._mark_board(state)

    def _hidden_now(self, state):
        return [{c.uid: c.defn.card_id for c in p.hand + p.deck_view()} for p in state.players]

    def _reveal(self, owner: int, uid: int, card_id: int, turn: int) -> None:
        if uid in self.originals[owner] and uid not in self.known[owner]:
            self.known[owner].add(uid)
            self.revealed[owner][card_id] += 1
            self.log[owner].append((turn, card_id))

    def _mark_board(self, state: GameState) -> None:
        for i, p in enumerate(state.players):
            for c in p.field + p.leader_area:
                self._reveal(i, c.uid, c.defn.card_id, state.turn)

    def before(self, state: GameState) -> None:
        self._hidden = self._hidden_now(state)

    def after(self, state: GameState) -> None:
        now = self._hidden_now(state)
        for i in (0, 1):
            for uid, cid in self._hidden[i].items():
                if uid not in now[i]:                      # left the hand / deck: shown in the real game
                    self._reveal(i, uid, cid, state.turn)
        self._mark_board(state)
        self._hidden = None

    def is_public(self, owner: int, uid: int) -> bool:
        return uid not in self.originals[owner] or uid in self.known[owner]


@dataclass
class PublicPosition:
    """Everything seat `me` may use at a decision. `state` holds nothing secret (see module docstring); do not
    search it directly (its opponent hand and deck are short of the unknown cards): use `sample`."""
    state: GameState
    me: int
    opp_unknown_hand: int
    opp_unknown_deck: int
    opp_hand_size: int
    opp_deck_size: int
    opp_revealed: Counter            # card ids of the opponent's starting cards seen so far
    opp_log: list                    # (global turn, card id) in the order seen
    opp_craft: int
    my_list: tuple                   # my own starting list (card ids)
    extra: dict = field(default_factory=dict)

    def observation(self) -> dict:
        """view.observe on the public state, with the opponent's true hand and deck sizes, plus the opponent's
        class and the cards seen."""
        o = observe(self.state, self.me)
        o["opponent"]["hand"] = self.opp_hand_size
        o["opponent"]["deck"] = self.opp_deck_size
        o["opponent"]["craft"] = self.opp_craft
        o["opponent"]["seen"] = list(self.opp_log)
        return o


def public_position(state: GameState, me: int, tracker: Tracker) -> PublicPosition:
    """The public position of seat `me` (referee side). The real state is not changed."""
    opp = 1 - me
    p = state.clone(copy_rng=False)
    p.rng.seed(0)
    op, mine = p.players[opp], p.players[me]
    real_op = state.players[opp]
    hand_known = sorted((c for c in op.hand if tracker.is_public(opp, c.uid)), key=lambda c: c.uid)
    deck_known = sorted((c.copy() for c in op.deck_view() if tracker.is_public(opp, c.uid)), key=lambda c: c.uid)
    n_uh = len(real_op.hand) - len(hand_known)
    n_ud = len(real_op.deck_view()) - len(deck_known)
    op.hand = hand_known
    op.deck = deck_known
    op.deck_name = ""
    mine.deck = sorted((c.copy() for c in mine.deck_view()), key=lambda c: c.uid)
    return PublicPosition(state=p, me=me, opp_unknown_hand=n_uh, opp_unknown_deck=n_ud,
                          opp_hand_size=len(real_op.hand), opp_deck_size=len(real_op.deck_view()),
                          opp_revealed=Counter(tracker.revealed[opp]), opp_log=list(tracker.log[opp]),
                          opp_craft=tracker.crafts[opp], my_list=tracker.lists[me])


# --- guesses -------------------------------------------------------------------------------------------------

def _ids(cards) -> tuple:
    return tuple(sorted(c if isinstance(c, int) else c.card_id for c in cards))


def posterior(guess, revealed: Counter) -> list[float]:
    """Weights of the guessed lists given the shown cards: prior x the chance of drawing the shown cards from the
    list without replacement (a shown card the list lacks counts EPS). `guess`: [(cards, prior weight), ...]."""
    logs = []
    for cards, w in guess:
        if w <= 0:
            logs.append(-math.inf)
            continue
        cnt = Counter(_ids(cards))
        lw = math.log(w)
        for cid, r in revealed.items():
            n = cnt.get(cid, 0)
            for i in range(r):
                lw += math.log(n - i) if n - i > 0 else math.log(EPS)
        logs.append(lw)
    top = max(logs)
    ws = [math.exp(x - top) if x > -math.inf else 0.0 for x in logs]
    total = sum(ws)
    return [x / total for x in ws]


def out_of_guess(guess, revealed: Counter) -> int:
    """Shown opponent cards no guessed list can hold (copies beyond the largest count any list has)."""
    most = Counter()
    for cards, _ in guess:
        for cid, n in Counter(_ids(cards)).items():
            most[cid] = max(most[cid], n)
    return sum(max(0, r - most.get(cid, 0)) for cid, r in revealed.items())


def sample(pos: PublicPosition, guess, rng: random.Random) -> tuple[GameState, dict]:
    """One full state consistent with `pos`, the opponent's unknown cards drawn from `guess`. Returns (state, info);
    info: the list drawn (index), and `short` when the list had fewer cards left than the opponent has unknown."""
    from svsim.cards.pool import card
    opp = 1 - pos.me
    weights = posterior(guess, pos.opp_revealed)
    r, acc, pick = rng.random(), 0.0, len(weights) - 1
    for i, w in enumerate(weights):
        acc += w
        if r < acc:
            pick = i
            break
    listed = _ids(guess[pick][0])
    left = Counter(listed) - pos.opp_revealed
    pool = sorted(left.elements())
    shuffle(rng, pool)
    need = pos.opp_unknown_hand + pos.opp_unknown_deck
    short = max(0, need - len(pool))
    for _ in range(short):                                  # only if the guess is not a 40-card list
        pool.append(listed[rng.randrange(len(listed))])
    chosen = pool[:need]
    s = pos.state.clone(copy_rng=False)
    op, mine = s.players[opp], s.players[pos.me]
    new = [s.new_instance(card(cid), opp) for cid in chosen]
    hand = op.hand + new[:pos.opp_unknown_hand]
    shuffle(rng, hand)
    op.hand = hand
    deck = [c.copy() for c in op.deck_view()] + new[pos.opp_unknown_hand:]
    shuffle(rng, deck)
    op.deck = deck
    md = [c.copy() for c in mine.deck_view()]
    shuffle(rng, md)
    mine.deck = md
    s.rng.seed(rng.getrandbits(64))
    return s, {"list": pick, "short": short}


# --- the default guess -------------------------------------------------------------------------------------------

_BASELINE = None


def baseline_lists() -> dict:
    """Craft -> the baseline member's list (bot-frozen7: the pool's baselines, public to everyone)."""
    global _BASELINE
    if _BASELINE is None:
        from svsim.cards.decks import from_hash
        out = {}
        for line in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                _, code = line.strip().split("|")
                cards = from_hash(code)
                out[craft_of(cards)] = _ids(cards)
        _BASELINE = out
    return _BASELINE


def default_guess(craft: int) -> list:
    """The base's default guess: the opponent plays the baseline list of its class (weight 1)."""
    return [(baseline_lists()[craft], 1.0)]


# --- the check ---------------------------------------------------------------------------------------------------

def _card_key(c: CardInstance) -> tuple:
    return (c.uid, c.defn.card_id, c.owner, c.cost, c.atk, c.life, c.max_life, int(c.keywords), c.countdown,
            c.evolved, c.super_evolved, c.entered_turn, c.attacks_made, c.max_attacks, c.order, c.fate,
            c.engaged_turn, c.fused_turn, c.silenced, c.no_last_words,
            None if c.counters is None else repr(sorted(c.counters.items())),
            None if c.grants is None else repr(c.grants), None if c.cost_mods is None else repr(c.cost_mods))


def fingerprint(pos: PublicPosition) -> tuple:
    """Everything in a public position, as a comparable value."""
    s = pos.state
    players = []
    for p in s.players:
        scalars = tuple((k, repr(getattr(p, k))) for k in p.__slots__
                        if k not in ("_deck", "hand", "field", "leader_area", "_deck_shared"))
        zones = tuple(tuple(_card_key(c) for c in z) for z in (p.deck_view(), p.hand, p.field, p.leader_area))
        players.append((scalars, zones))
    head = (s.first, s.active, s.turn, int(s.phase), s.winner, s.next_uid, s.next_order, s.max_turns,
            s.rng.getstate())
    meta = (pos.me, pos.opp_unknown_hand, pos.opp_unknown_deck, pos.opp_hand_size, pos.opp_deck_size,
            tuple(sorted(pos.opp_revealed.items())), tuple(pos.opp_log), pos.opp_craft, pos.my_list)
    return head, tuple(players), meta


def vary_secrets(state: GameState, me: int, tracker: Tracker, rng: random.Random,
                 replacements: list | None = None) -> GameState:
    """Another real state that `me` can't tell from `state`: the opponent's unknown cards replaced (by cards from
    `replacements`, card ids, else the same cards permuted), both decks reshuffled, the generator reseeded."""
    from svsim.cards.pool import card
    s = state.clone()
    opp = 1 - me
    op = s.players[opp]
    hidden = [c for c in op.hand + op.deck_view() if not tracker.is_public(opp, c.uid)]
    ids = [c.defn.card_id for c in hidden]
    if replacements:
        ids = [replacements[rng.randrange(len(replacements))] for _ in ids]
    else:
        rng.shuffle(ids)
    swap = {c.uid: CardInstance.create(c.uid, card(cid), opp) for c, cid in zip(hidden, ids)}
    op.hand = [swap.get(c.uid, c) for c in op.hand]
    deck = [swap.get(c.uid, c.copy()) for c in op.deck_view()]
    rng.shuffle(deck)
    op.deck = deck
    mine = s.players[me]
    md = [c.copy() for c in mine.deck_view()]
    rng.shuffle(md)
    mine.deck = md
    s.rng.seed(rng.getrandbits(64))
    return s
