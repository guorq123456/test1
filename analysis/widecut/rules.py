"""Pruning rules on visible information, tried on collect.py's wide decisions (the architecture thread 18:37Z).
Condition: the opponent's deck list is known (order and hand not).

The two largest buckets by the strongest tier's choice, each with a rule:
1. **discard** (a discard choice): search.xprune as gated, +xprune=3:3:cost, and the first version m 2 when.
2. **play** (which card to play now), rule "budget":
   - this turn's play-point budget is the play points left (plus the Bonus Play Point if unused);
   - each playable hand card may be played at its cost, an Enhance cost within the budget, or an Accelerate /
     Crystallize cost;
   - the most play points any set of hand cards can use this turn is B;
   - a play is kept if its card is in some set using B - SLACK or more (the card at the cost the play would use
     now); every other play (plays, plays with targets, Choose plays) is cut;
   - nothing else is touched, and if every play would be cut none is.
   Tried at SLACK 0, 1, 2. Read off the cards' costs and the play points only; no fixed value per card.

For each rule and decision: the moves it cuts, and whether the strongest tier's choice survives. Reported per bucket
of the strongest tier's choice and over all wide decisions.

    python3 rules.py STEP1_DIR WIDE.jsonl OUT.json
"""
import json
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def rebuild(step1, games, row):
    sys.path.insert(0, f"{step1}/ana")
    import student_data as SD
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    s = SD._state_at(games[row["game"]], row["at"])
    for a in row["prefix"]:
        apply(s, from_dict(a))
    return s


def _options(p, card, budget):
    """The play-point costs `card` can be played at this turn within `budget`."""
    from svsim.core.script import script_for
    out = set()
    if card.cost <= budget:
        out.add(card.cost)
        for e in script_for(card.defn.card_id).enhance or ():
            if e <= budget:
                out.add(e)
    for alt in (card.defn.accelerate, card.defn.crystallize):
        if alt is not None and alt.cost <= budget:
            out.add(alt.cost)
    return sorted(out)


def budget_keep(state, slack):
    """uids of hand cards in some set of plays using at least B - slack of this turn's budget."""
    from svsim.core.engine import play_form
    p = state.players[state.active]
    budget = p.pp + (1 if p.bonus_ready and not p.bonus_active else 0)
    cards = [c for c in p.hand if play_form(p, c) is not None or _options(p, c, budget)]
    opts = [[0] + _options(p, c, budget) for c in cards]       # 0: not played
    best, sets = 0, []
    if len(cards) > 12:
        return {c.uid for c in cards}
    for pick in product(*opts):
        total = sum(pick)
        if total <= budget:
            sets.append((total, pick))
            best = max(best, total)
    keep = set()
    for total, pick in sets:
        if total >= best - slack:
            keep |= {cards[i].uid for i, x in enumerate(pick) if x}
    return keep


def play_cut(state, legal, slack, kind):
    """The plays the budget rule cuts (indices into legal)."""
    keep = budget_keep(state, slack)
    plays = [i for i, a in enumerate(legal) if kind(state, a) in ("play", "play_target", "choose")]
    cut = [i for i in plays if legal[i].uid not in keep]
    return [] if len(cut) == len(plays) else cut


def main():
    step1, wide, out = sys.argv[1:4]
    sys.path.insert(0, f"{step1}/ana")
    sys.path.insert(0, str(ROOT / "analysis/widecut"))
    import student_data as SD
    from collect import _after, kind
    from svsim.core.actions import from_dict
    from svsim.core.engine import legal_actions
    from svsim.search.xprune import XPrune
    games = {r["g"]: r for r in SD._lines(f"{step1}/selfplay.jsonl")}
    rows = [json.loads(l) for l in open(wide, encoding="utf-8") if l.strip()]
    rules = {"xprune m2 when": ("x", XPrune(2, 3, "when")), "xprune m3 cost": ("x", XPrune(3, 3, "cost")),
             "budget slack 0": ("b", 0), "budget slack 1": ("b", 1), "budget slack 2": ("b", 2)}
    res = {k: [] for k in rules}
    for r in rows:
        s = rebuild(step1, games, r)
        legal = legal_actions(s)
        chosen = from_dict(r["max"])
        target = _after(s, chosen)
        for name, (typ, arg) in rules.items():
            if typ == "x":
                cut = [i for i, a in enumerate(legal) if arg(s, a)]
                if len(cut) == len(legal):
                    cut = []
            else:
                cut = play_cut(s, legal, arg, kind)
            kept_keys = {_after(s, legal[i]) for i in range(len(legal)) if i not in set(cut)}
            res[name].append({"bucket": r["max_kind"], "legal": len(legal), "cut": len(cut),
                              "kept": target in kept_keys, "same": r["same"]})
    summary = {}
    for name, v in res.items():
        def agg(sel):
            sel = list(sel)
            touched = [x for x in sel if x["cut"]]
            return {"decisions": len(sel), "touched": len(touched),
                    "chosen_kept": round(sum(x["kept"] for x in sel) / len(sel), 4) if sel else None,
                    "chosen_kept_where_touched": round(sum(x["kept"] for x in touched) / len(touched), 4)
                    if touched else None,
                    "moves_cut_share": round(sum(x["cut"] for x in sel) / sum(x["legal"] for x in sel), 4)
                    if sel else None,
                    "moves_cut_share_where_touched": round(sum(x["cut"] for x in touched) /
                                                           sum(x["legal"] for x in touched), 4) if touched else None}
        summary[name] = {"all": agg(v)} | {b: agg(x for x in v if x["bucket"] == b)
                                          for b in ("play", "discard")}
    Path(out).write_text(json.dumps({"summary": summary, "rows": res}, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
