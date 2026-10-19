"""Which scoring each bot uses in a pairing (the architecture thread 2026-10-19 00:34Z; report only, nothing changed).

For every spec (the trainer's levels, ui.session.LEVELS; v2skx; the new candidates) and every seat of the pairings
asked, the agent is built as the trainer builds it (tools.arena.make_agent), a game of that pairing is dealt (seed 0,
a fixed test position; no game is played), and the agent's turn-end and in-turn scores of its own side are asked
once. The report names what answered each:
- a per-pairing linear model (learn.phased PhasedLearned): its folder and file (<deck>-<deck>-<moment>.json), or the
  stand-in it fell back to (a mirror alias, a class pair);
- the per-deck linear model (learn.model Learned, svsim/learn/weights): its file;
- a value net (learn.setnet SetNetEnded): its file and pairing, and whether it answered here or passed the position
  to the model under it;
and, for a spec with +puct, the move prior's file and the pairing it was trained on (the prior checks no pairing:
it runs in any).

    python analysis/scaling/pairing_probe.py --pair ramp-t:elf-t --pair elf-t:ramp-t --out OUT
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from svsim.learn.scaledata import SPEC as V2SKX  # noqa: E402

CANDIDATES = {
    "A-ramp-t": "mcts:83+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/"
                "net-mid-ramp-t.npz+netmid+puct=analysis/scaling/models/prior-ramp-ft-t05.npz:2:1",
    "A-elf-t": "mcts:71+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/"
               "net-mid-elf-t.npz+netmid+puct=analysis/scaling/models/prior-elft-ft-t05.npz:2:1",
}


def _find(obj, kinds, depth=0, seen=None):
    """The first object of one of `kinds` reachable from obj's attributes (breadth-limited)."""
    seen = seen if seen is not None else set()
    if id(obj) in seen or depth > 6:
        return None
    seen.add(id(obj))
    if isinstance(obj, kinds):
        return obj
    for v in list(getattr(obj, "__dict__", {}).values()):
        if isinstance(v, (int, float, str, bytes, bool, type(None))):
            continue
        hit = _find(v, kinds, depth + 1, seen)
        if hit is not None:
            return hit
    return None


def _folder(spec: str):
    from svsim.learn.phased import folder_of
    opt = next((o for o in spec.split("+") if o.startswith("phased=")), None)
    if opt:
        return folder_of(opt[len("phased="):])
    return Path(__import__("svsim.learn.phased", fromlist=["x"]).__file__).resolve().parent / "phased_models"


def answered_by(spec: str, weights, state, player: int, moves_next: bool) -> dict:
    from svsim.learn.model import Learned, deck_craft, matchup_keys
    from svsim.learn.phased import PhasedLearned
    from svsim.learn.setnet import SetNetEnded
    out = {}
    w = weights
    if isinstance(w, SetNetEnded):
        pair = (state.players[player].deck_name, state.players[1 - player].deck_name)
        path = next(o for o in spec.split("+") if o.startswith("setnet="))[len("setnet="):]
        out["net"] = {"file": path, "pairing": list(w.pair), "answers_here": (pair == w.pair
                                                                                             and not moves_next)}
        if out["net"]["answers_here"]:
            return out
        w = w.base
    if isinstance(w, PhasedLearned):
        moment = "act" if moves_next else "ended"
        w.score(state, player, moves_next)
        mine, theirs = state.players[player].deck_name, state.players[1 - player].deck_name
        model = w._named.get((mine, theirs, moment)) if mine and theirs else None
        if model is None:
            model = next((w.models[k + (moment,)] for k in matchup_keys(state, player, w.aliases)
                          if k + (moment,) in w.models), None)
        if model is not None:
            key = next(k for k, v in w.models.items() if v is model)
            name = lambda x: x if isinstance(x, str) else x.name.lower()   # noqa: E731
            out["phased"] = {"folder": str(_folder(spec).relative_to(HERE.parents[1])),
                             "file": f"{name(key[0])}-{name(key[1])}-{key[2]}.json",
                             "exact_pairing": (key[0], key[1]) == (mine, theirs)}
            return out
        out["phased"] = None
        w = w.fallback
    if isinstance(w, Learned):
        model = next((w.models[k] for k in matchup_keys(state, player, w.aliases) if k in w.models), None)
        key = next((k for k in matchup_keys(state, player, w.aliases) if k in w.models), None)
        if model is None:
            key = deck_craft(state, player)
        name = lambda x: x if isinstance(x, str) else x.name.lower()   # noqa: E731
        out["learned"] = {"file": ("-".join(name(x) for x in key) if isinstance(key, tuple) else name(key)) + ".json"
                          if key is not None else None}
        return out
    out["other"] = type(w).__name__
    return out


def probe(spec: str, deck: str, opp: str) -> dict:
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned
    from svsim.learn.setnet import SetNetEnded
    from svsim.learn.setpolicy import SetPolicy
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    state = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opp][1]), seed=0)
    assert (state.players[0].deck_name, state.players[1].deck_name) == (deck, opp)
    agent = make_agent(spec, 0)
    weights = _find(agent, (SetNetEnded, PhasedLearned, Learned))
    row = {"turn_end": answered_by(spec, weights, state, 0, False) if weights is not None else None,
           "in_turn": answered_by(spec, weights, state, 0, True) if weights is not None else None}
    prior = _find(agent, (SetPolicy,))
    if prior is not None:
        path = next(o for o in spec.split("+") if o.startswith("puct="))[len("puct="):].split(":")[0]
        row["prior"] = {"file": path, "pairing": [prior.info.get("deck"), prior.info.get("opponent")]}
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pair", action="append", required=True, metavar="DECK:OPPONENT", help="the bot plays DECK")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from svsim.ui.session import LEVELS
    specs = {**{f"level-{k}": v for k, v in LEVELS.items()}, "v2skx": V2SKX, **CANDIDATES}
    report = {"specs": specs, "pairs": {}}
    for pair in args.pair:
        deck, opp = pair.split(":")
        report["pairs"][pair] = {name: probe(spec, deck, opp) for name, spec in specs.items()}
        print(json.dumps({pair: report["pairs"][pair]}, ensure_ascii=False, indent=1), flush=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
