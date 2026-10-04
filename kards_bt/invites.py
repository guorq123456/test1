"""Ladder-invite credit for OCC Top 8 (method F1 in experiments.py).

In an OCC month with both qualifier and Top 8 data, a Top 8 entrant who never played that month's
qualifier was invited from the in-game ladder. Qualifier advancers bank several wins on their way
in; invitees bank nothing, although an invite is as hard to earn as a qualifier win. So each
invitee is credited with the month's median advancer qualifier record (wins and losses) against a
virtual opponent rated at the mean pre-month rating of the opponents the advancers faced. No free
parameter. Credits are dated at the Top 8 start, when invite status and advancer records are known.

Not applied to months whose qualifier brackets are missing (2024-04..08) or to events without
ladder invites (expansion / seasonal tournaments, OCC Ultimate).
"""
import csv
import os
import re
from collections import defaultdict
from datetime import datetime
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
NO_QUALIFIER = {f"OCC 2024-0{m}" for m in range(4, 9)}
MONTH = re.compile(r"OCC \d{4}-\d\d$")


def _t(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def months():
    """[(month, qualifier_start, top8_start, invitees, {advancer: [(opponent, won)]})]."""
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", "matches.csv"))))
    seen = defaultdict(lambda: defaultdict(set))
    starts = defaultdict(dict)
    for r in rows:
        if not MONTH.match(r["event"]) or r["event"] in NO_QUALIFIER:
            continue
        kind = "top8" if re.search(r"top|final", r["stage"] or "", re.I) else "qual"
        for p in (r["p1"], r["p2"]):
            if p != "ch:BYE":
                seen[r["event"]][kind].add(p)
        if r["valid"] == "1":
            t = _t(r["time"])
            starts[r["event"]][kind] = min(starts[r["event"]].get(kind, t), t)
    out = []
    for month, s in seen.items():
        inv, adv = s["top8"] - s["qual"], s["top8"] & s["qual"]
        if not inv or not adv or "top8" not in starts[month] or "qual" not in starts[month]:
            continue
        rec = defaultdict(list)
        for r in rows:
            if r["event"] != month or r["valid"] != "1" or re.search(r"top|final", r["stage"] or "", re.I):
                continue
            w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
            if w in adv:
                rec[w].append((l, True))
            if l in adv:
                rec[l].append((w, False))
        out.append((month, starts[month]["qual"], starts[month]["top8"], inv, rec))
    return sorted(out, key=lambda m: m[2])


def credits(fit_before):
    """[(time, player, level, wins, losses)]; fit_before(t) -> {player: rating} from results before t."""
    out = []
    for month, qual_start, top8_start, inv, rec in months():
        adv = list(rec)
        if not adv:
            continue
        wins = median(sum(1 for _, won in rec[a] if won) for a in adv)
        losses = median(sum(1 for _, won in rec[a] if not won) for a in adv)
        pre = fit_before(qual_start)
        opps = [o for a in adv for o, _ in rec[a]]
        level = sum(pre.get(o, 0.0) for o in opps) / len(opps)
        out += [(top8_start, p, level, wins, losses) for p in sorted(inv)]
    return out
