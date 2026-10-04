"""Peak ratings with hindsight (data/peaks.csv), for the site's peak leaderboard.

The timeline in bt.py only uses results up to each date, so it lags: a short strong run is only half
credited when it ends, and a peak is judged before the dip that followed. For a career peak we can use
hindsight: at every event date, refit on ALL results weighted by their distance in time (either side),
0.5 ** (|d| / half_life), same prior, and the same virtual evidence as the production model (newcomer
anchors, ladder-invite credits), faded on both sides of the date too. A player's peak is their highest rank score (rating - 1 standard
error) at any event date where they had played at least MIN_MATCHES official matches so far.

    python3 peaks.py
"""
import argparse
import csv
import os
from collections import Counter

import numpy as np

import bt
import invites
import newcomers

MIN_MATCHES = 10


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--half-life", type=float, default=240)
    ap.add_argument("--prior-sd", type=float, default=0.4)
    ap.add_argument("--newcomer-anchor", type=float, default=2)
    ap.add_argument("--invite-half-life", type=float, default=120)
    ap.add_argument("--invite-shrink", type=float, default=20,
                    help="as in bt.py; the peak board shrinks each invite credit by n0/(n0 + real evidence) so repeat "
                         "invitees are not carried by the credit (bt.py keeps the uniform credit: equal out of sample)")
    args = ap.parse_args()

    ms = sorted(bt.load_matches(set(bt.RATED), False))
    names = {r["player_id"]: r["name"] for r in csv.DictReader(open(os.path.join(bt.DATA, "players.csv")))}
    ids = sorted({p for m in ms for p in (m[1], m[2])})
    idx = {p: i for i, p in enumerate(ids)}
    win, lose = np.array([idx[m[1]] for m in ms]), np.array([idx[m[2]] for m in ms])
    times = np.array([m[0].timestamp() for m in ms])
    credits = invites.credits(lambda t: bt._fit_before(ms, t, args.half_life, args.prior_sd))
    credits = [c + (args.invite_half_life,) for c in credits if c[1] in idx]  # (t, p, level, wins, losses, half-life)
    anchors = newcomers.anchors(ms, args.half_life, args.prior_sd, bt.fit_bt, args.newcomer_anchor)
    n_inv = len(credits)

    peak, played = {}, Counter()
    k = 0
    for t, ev in bt.event_snapshots(ms):
        while k < len(ms) and ms[k][0] <= t:
            played[ms[k][1]] += 1
            played[ms[k][2]] += 1
            k += 1
        w = 0.5 ** (np.abs(t.timestamp() - times) / 86400 / args.half_life)
        evidence = np.bincount(np.concatenate([win, lose]), weights=np.concatenate([w, w]), minlength=len(ids))
        v = []
        for j, (tc, p, level, wins, losses, hl) in enumerate(credits + anchors):
            fade = 0.5 ** (abs((t - tc).total_seconds()) / 86400 / hl)
            if j < n_inv and args.invite_shrink > 0:
                fade *= args.invite_shrink / (args.invite_shrink + evidence[idx[p]])
            v += [(idx[p], level, 1.0, wins * fade), (idx[p], level, -1.0, losses * fade)]
        virtual = tuple(np.array(c) for c in zip(*v)) if v else None
        b, se = bt.fit_bt(win, lose, w, len(ids), args.prior_sd, virtual=virtual)
        elo, sd = 1500 + bt.ELO_SCALE * b, bt.ELO_SCALE * se
        board = sorted(((elo[idx[p]] - sd[idx[p]], p) for p, n in played.items() if n >= MIN_MATCHES), reverse=True)
        for rank, (score, p) in enumerate(board, 1):
            if p not in peak or score > peak[p]["score"]:
                peak[p] = {"score": score, "elo": elo[idx[p]], "se": sd[idx[p]], "date": t.strftime("%Y-%m-%d"),
                           "event": ev, "rank_then": rank}
    total = Counter(p for m in ms for p in (m[1], m[2]))
    rows = sorted(({"player_id": p, "name": names.get(p, p), "peak_score": round(v["score"], 1), "peak_elo": round(v["elo"], 1),
                    "peak_se": round(v["se"], 1), "peak_date": v["date"], "peak_event": v["event"],
                    "rank_then": v["rank_then"], "results": total[p]} for p, v in peak.items()),
                  key=lambda r: -r["peak_score"])
    with open(os.path.join(bt.DATA, "peaks.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    print(f"data/peaks.csv: {len(rows)} players; top 5: " + ", ".join(f"{r['name']} {r['peak_score']:.0f}" for r in rows[:5]))


if __name__ == "__main__":
    main()
