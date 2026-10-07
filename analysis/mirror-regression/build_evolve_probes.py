"""Build evolve_probes.json: Salem's turns where evolving was possible, held or used.

    cd <svsim checkout> && PYTHONPATH=. python3 build_evolve_probes.py salem_games.json > evolve_probes.json

For every turn of Salem (seat 0) in salem_games.json that did not win the game:
- evolve_hold: an evolution was legal at some decision of the turn (points
  left, unlocked, a follower that can evolve) and Salem did not evolve. The
  check: the bot, playing the whole turn from its start, does not evolve either.
- evolve_use: Salem evolved (or super-evolved) this turn. The check: the bot
  evolves too (any evolution), so that a bot that never evolves does not pass.
- erntz_unevolved: a held turn on which Salem played Erntz and left it
  unevolved. Salem (2026-10-07): Erntz unevolved is another way to use it, as
  strong as evolving it, not a held point; so it is not an evolve_hold. The
  check: the bot plays Erntz and does not evolve it.
The two together reward evolving at Salem's moments, not holding as such
(the architecture thread, 2026-10-07: the bot spends its points as soon as they
unlock and runs dry in long games). Records stay in salem_games.json.
The text fields (why, context) name the cards the way Salem reads them: the glossary's common name
with cost and stats (glossary.py).
"""
import json
import sys

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import Evolve, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from build_positions import ERNTZ, name  # noqa: E402
from glossary import labelled  # noqa: E402


def board(p):
    """Salem's naming (glossary): the common name with cost and stats, then the follower's attack/defense now."""
    return [f"{labelled(name(c))} 现 {c.atk}/{c.life}" for c in p.followers]


def turns(rec):
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    i = 0
    while i < len(acts) and not st.over:
        if st.active != 0 or type(acts[i]).__name__ == "Mulligan":
            apply(st, acts[i])
            i += 1
            continue
        start, snap, turn = i, st.clone(), []
        while i < len(acts) and st.active == 0 and not st.over:
            turn.append((st.clone(), acts[i]))
            apply(st, acts[i])
            i += 1
        yield start, snap, turn, st


def main(path):
    data = json.load(open(path, encoding="utf-8"))
    out = []
    for gid, rec in sorted(data["records"].items()):
        for start, snap, turn, after in turns(rec):
            if after.over and after.winner == 0:
                continue
            p, o = snap.players
            could = any(isinstance(a, Evolve) for s, _ in turn for a in legal_actions(s))
            used = [(("超进化" if a.super_ else "进化"), labelled(name(s.on_field(a.uid))))
                    for s, a in turn if isinstance(a, Evolve)]
            if not could and not used:
                continue
            ctx = {"own_turn": p.turns_taken, "first": snap.first == 0, "pp": f"{p.pp}/{p.max_pp}",
                   "hp": p.leader_hp, "opp_hp": o.leader_hp, "hand": [labelled(name(c)) for c in p.hand],
                   "board": board(p), "opp_board": board(o), "ep": p.ep, "sep": p.sep,
                   "opp_ep": o.ep, "opp_sep": o.sep, "turns_so_far": snap.turn}
            meta = data.get("meta", {}).get(gid, {})
            if used:
                cat, check = "evolve_use", {"evolves": True}
                why = f"Salem {'、'.join(k + ' ' + c for k, c in used)}（还剩 ep {p.ep} / sep {p.sep}）。"
            elif any(type(a).__name__ == "PlayCard" and name(s.in_hand(0, a.uid)) == ERNTZ for s, a in turn):
                # Salem (2026-10-07): Erntz played unevolved is another way to use it, as strong as
                # evolving it (8 to two followers, heal 8), not a held point: a probe of its own
                cat, check = "erntz_unevolved", {"plays_unevolved": ERNTZ}
                why = (f"Salem 这回合出了{labelled(ERNTZ)}、用不进化那面（回合结束打两个随从各 8、回 8 血），"
                       f"没进化任何随从（ep {p.ep} / sep {p.sep}）。")
            else:
                cat, check = "evolve_hold", {"no_evolve": True}
                why = f"Salem 能进化（ep {p.ep} / sep {p.sep}）但这回合没进化，也没在这回合赢。"
            out.append({"id": f"{gid}-t{p.turns_taken}-{cat}", "category": cat, "check": check,
                        "confidence": "中", "why": why, "game": gid, "at": start, "context": ctx,
                        "batch": meta.get("batch"), "salem_turn": [type(a).__name__ for _, a in turn]})
    json.dump({"source": "Salem's turns in salem_games.json where evolving was possible (held, Erntz unevolved) or done (used)",
               "records_file": "salem_games.json", "positions": out}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
