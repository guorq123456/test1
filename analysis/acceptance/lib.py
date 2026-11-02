"""The acceptance library (process item 5, analysis/process/PROCESS.md): positions rebuilt from the engine only,
checked by fingerprint, and scored by any value net, any move prior, or the hand-set evaluation.

A position file (positions/<id>.json) holds the decks as codes, how to rebuild the position, its fingerprint, Salem's
line and reason, the line he calls wrong, the scorings that apply and the tier (clear / marginal). A replay position
is rebuilt by applying its stored action list from the deal (recorded once by record.py); no search runs, so a change
to search or evaluation does not move it. A rebuild whose fingerprint differs is an error and the item is not scored.

These are checks, never fitting targets: Salem's games and the external lists never enter search, self-play or
training. Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import svsim.tools.arena  # noqa: E402,F401  (card scripts)
from svsim.cards import deckcode  # noqa: E402
from svsim.cards.pool import POOL  # noqa: E402
from svsim.core.actions import EndTurn  # noqa: E402
from svsim.core.engine import apply, legal_actions, new_game  # noqa: E402
from svsim.search import evaluate as EV  # noqa: E402
from svsim.ui.text import describe  # noqa: E402

POSITIONS = Path(__file__).resolve().parent / "positions"
SCORINGS = ("turn_end", "mid_turn", "prior", "handset")


class Moved(Exception):
    """A rebuilt position whose fingerprint is not the stored one."""


def cards(code: str) -> list:
    return [POOL[i] for i in deckcode.decode_deck(code)[2]]


def fingerprint(state, seat: int) -> dict:
    me = state.players[seat]
    return {"hand": sorted(c.defn.card_id for c in me.hand), "field": sorted(c.defn.card_id for c in me.field),
            "pp": me.pp, "leader_hp": me.leader_hp, "turn": state.turn}


def load(folder=POSITIONS) -> list:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(folder).glob("*.json"))]


def _replay(pos: dict):
    r = pos["rebuild"]
    seat = r["seat"]
    decks = [None, None]
    decks[seat], decks[1 - seat] = cards(pos["deck_code"]), cards(pos["opponent_code"])
    state = new_game(decks[0], decks[1], seed=r["seed"])
    for n, (index, text) in enumerate(r["actions"]):
        acts = legal_actions(state)
        if index >= len(acts) or describe(state, acts[index]) != text:
            raise Moved(f"{pos['id']}: step {n} is no longer「{text}」")
        apply(state, acts[index])
    return state, seat


def rebuild(pos: dict, variant: int = 0):
    """(state, seat) of the position; raises Moved when its fingerprint differs from the stored one. A builder
    position (the bunny board) has several variants (deals of the opponent's unknown cards)."""
    kind = pos["rebuild"]["kind"]
    if kind == "replay":
        state, seat = _replay(pos)
        want = pos["fingerprint"]
    elif kind == "builder":
        import builders
        state, seat = getattr(builders, pos["rebuild"]["function"])(pos, pos["rebuild"]["seeds"][variant])
        want = pos["fingerprint"][variant]
    else:
        raise ValueError(f"{pos['id']}: unknown rebuild kind {kind}")
    got = fingerprint(state, seat)
    if got != want:
        raise Moved(f"{pos['id']}: fingerprint {got} != stored {want}")
    names = [None, None]
    names[seat], names[1 - seat] = pos["deck"], pos["opponent"]
    for p, name in zip(state.players, names):
        p.deck_name = name
    return state, seat


def variants(pos: dict) -> int:
    return len(pos["rebuild"]["seeds"]) if pos["rebuild"]["kind"] == "builder" else 1


def play_line(state, seat: int, line, pos: dict):
    """Apply a line to (a copy of) the state: a list of action descriptions (each the first legal action whose
    description contains it, as acceptance.py), or a named builder line."""
    if isinstance(line, str):                                   # a builder's named line
        import builders
        return getattr(builders, pos["rebuild"]["line_function"])(state, line)
    for step in line:
        acts = legal_actions(state)
        action = next((a for a in acts if step in describe(state, a)), None)
        if action is None:
            raise Moved(f"{pos['id']}: no legal action「{step}」")
        apply(state, action)
    return state


def line_score(pos: dict, line, evaluate, k: int | None = None) -> float:
    """The mean of evaluate(state_after_line, seat) over the variants and k reseeded copies each."""
    k = k or pos.get("copies", 40)
    total, n = 0.0, 0
    after = pos.get("reseed") == "after_line"          # the bunny script reseeds after the line, acceptance.py before
    for v in range(variants(pos)):
        state, seat = rebuild(pos, v)
        if after:
            state = play_line(state, seat, line, pos)
        for j in range(k):
            t = state.clone()
            t.rng = random.Random(j)
            if not after:
                t = play_line(t, seat, line, pos)
            total += evaluate(t, seat)
            n += 1
    return total / n


def evaluators(net=None) -> dict:
    """The line scorings: hand-set always; turn-end and mid-turn with a net (mid-turn only for a flagged net)."""
    out = {"handset": lambda s, p: EV.evaluate(EV.after_end_of_turn(s), p, EV.DEFAULT)}
    if net is not None:
        out["turn_end"] = lambda s, p: net.logit(EV.after_end_of_turn(s), p)
        if getattr(net, "flag", False):
            out["mid_turn"] = lambda s, p: net.logit(s, p, mid=True)
    return out


def prior_first_step(pos: dict, prior) -> tuple:
    """(P(Salem's first step), P(the wrong line's first step)) at the position, summed over the legal actions whose
    description contains the step (prior_acceptance.py's rule); an empty wrong line is ending the turn."""
    state, seat = rebuild(pos)
    acts = legal_actions(state)
    mass: dict = {}
    for a, q in zip(acts, prior.priors(state, acts)):
        d = describe(state, a)
        mass[d] = mass.get(d, 0.0) + float(q)
    first = lambda line: line[0] if line else None  # noqa: E731
    s, w = first(pos["salem"]["line"]), first(pos["wrong"][0]["line"])
    ps = sum(q for d, q in mass.items() if s in d)
    pw = mass.get(describe(state, next(a for a in acts if isinstance(a, EndTurn))), 0.0) if w is None \
        else sum(q for d, q in mass.items() if w in d)
    return ps, pw


def judge(pos: dict, net=None, prior=None) -> dict:
    """{scoring: {"pass": bool, "salem": x, "wrong": y}} for each scoring this position takes that can be run."""
    out = {}
    evs = evaluators(net)
    for name in pos["scorings"]:
        if name == "prior":
            if prior is not None:
                ps, pw = prior_first_step(pos, prior)
                out[name] = {"pass": ps > pw, "salem": ps, "wrong": pw}
            continue
        if name not in evs:
            continue
        a = line_score(pos, pos["salem"]["line"], evs[name])
        bs = [line_score(pos, w["line"], evs[name]) for w in pos["wrong"]]
        out[name] = {"pass": all(a > b for b in bs), "salem": a, "wrong": max(bs)}
    return out


def tally(rows: list) -> dict:
    """{scoring: {tier: [passed, total]}} over [(pos, judged)]."""
    out: dict = {}
    for pos, judged in rows:
        for name, r in judged.items():
            cell = out.setdefault(name, {}).setdefault(pos.get("tier", "unassigned"), [0, 0])
            cell[0] += bool(r["pass"])
            cell[1] += 1
    return out
