"""Main-stage-only board (data/mainboard.csv): ratings fitted on Top 8 / Top 16 / playoff / grand-final matches
alone, as of the latest event.

A different question from the main model: not "how strong is this player" but "how strong in main stages",
where every opponent came through a qualifier. Same decay, prior and newcomer anchor as bt.py; no ladder-invite
credit (it compensates for qualifier wins, which are not scored here). Only ~1,000 matches, so the bar of 10
matches leaves about 50 players; out of sample it predicts main-stage matches about as well as the full model
(qualdrop_exp.py), with far fewer players rated.

    python3 mainboard.py
"""
import argparse
import csv
import os
from collections import Counter

import numpy as np

import bt
import newcomers
from normalize import MAIN, stage_name


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--half-life", type=float, default=240)
    ap.add_argument("--prior-sd", type=float, default=0.4)
    ap.add_argument("--newcomer-anchor", type=float, default=2)
    args = ap.parse_args()

    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(bt.DATA, "players.csv")))}
    ms = []
    for r in csv.DictReader(open(os.path.join(bt.DATA, "matches.csv"))):
        if r["valid"] == "1" and r["category"] in bt.RATED and stage_name(r["event"], r["stage"] or "", r["stage_type"] or "") in MAIN:
            w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
            ms.append((bt.parse_time(r["time"]), w, l, 1.0, r["event"]))
    ms.sort()
    t_last = max(m[0] for m in ms)
    ids = sorted({p for m in ms for p in (m[1], m[2])})
    idx = {p: i for i, p in enumerate(ids)}
    age = np.array([(t_last - m[0]).total_seconds() / 86400 for m in ms])
    w = 0.5 ** (age / args.half_life)
    v = []
    for t, p, level, wins, losses, hl in newcomers.anchors(ms, args.half_life, args.prior_sd, bt.fit_bt, args.newcomer_anchor):
        if p in idx:
            f = 0.5 ** ((t_last - t).total_seconds() / 86400 / hl)
            v += [(idx[p], level, 1.0, wins * f), (idx[p], level, -1.0, losses * f)]
    b, se = bt.fit_bt(np.array([idx[m[1]] for m in ms]), np.array([idx[m[2]] for m in ms]), w, len(ids), args.prior_sd,
                      virtual=tuple(np.array(c) for c in zip(*v)) if v else None)
    rec, last = Counter(), {}
    for m in ms:
        rec[(m[1], "w")] += 1
        rec[(m[2], "l")] += 1
        for p in (m[1], m[2]):
            last[p] = max(last.get(p, m[0]), m[0])
    rows = []
    for p, i in idx.items():
        elo, sd = 1500 + bt.ELO_SCALE * b[i], bt.ELO_SCALE * se[i]
        rows.append({"player_id": p, "name": names.get(p, p), "elo": round(elo, 1), "se": round(sd, 1), "score": round(elo - sd, 1),
                     "wins": rec[(p, "w")], "losses": rec[(p, "l")], "last_played": last[p].strftime("%Y-%m-%d")})
    rows.sort(key=lambda r: -r["score"])
    with open(os.path.join(bt.DATA, "mainboard.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    top = [r for r in rows if r["wins"] + r["losses"] >= 10][:8]
    print(f"data/mainboard.csv: {len(rows)} players as of {t_last:%Y-%m-%d} ({len(ms)} main-stage matches); "
          f"top with >=10: " + ", ".join(f"{r['name']} {r['elo']:.0f}" for r in top))


if __name__ == "__main__":
    main()
