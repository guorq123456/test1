"""Which positions the net scores inside the search (the architecture thread 20:55Z asked the analysis line to check
its reading that every non-terminal value in a v2skx+setnet search comes from the net).

Plays games of A = v2skx+setnet against B = v2skx (svsim.tools.gate's agents and deals) with the net's scorer
(learn.setnet.SetNetEnded.score) wrapped, nothing else changed. At every call that the net answers it records the
kind of position:
  - "ended": the search stepped EndTurn into it (search.mcts _step: end-of-turn abilities resolved, the next turn
    not started) - the moment the net was trained on (learn.tokens);
  - "mid": the player to act is still the scored player, the turn not ended - a leaf inside the turn, or the root's
    centre; the net never saw this moment in training.
For "mid" positions it also scores after_end_of_turn(position) (the same position with the turn ended there, the
moment the net knows) with the net and with the installed linear evaluation, and reports how far each moves:
d = logit(position) - logit(after_end_of_turn(position)), linear in the same units (score / SCALE).
Condition: the opponent's deck list is known (order and hand not).

    PYTHONPATH=SVSIM python3 leaf_probe.py --net analysis/scaling/models/net-10000.npz --seed 71000000 --games 6 \
        --out probe.json        # run from the svsim checkout (the net path is relative to it)
"""
import argparse
import json
import time

import numpy as np

P = "plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--games", type=int, default=6)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from svsim.cards import decks
    from svsim.learn import setnet as SN
    from svsim.learn.model import SCALE
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools import gate
    from svsim.ui.session import DECKS

    rows = []
    decision = [0]                              # A's searched decisions, counted by its act()
    original = SN.SetNetEnded.score

    def wrapped(self, state, player, player_moves_next=False):
        v = original(self, state, player, player_moves_next)
        if state.winner is not None or player_moves_next or \
                (state.players[player].deck_name, state.players[1 - player].deck_name) != self.pair:
            return v
        mid = state.active == player
        row = {"mid": mid, "turn": state.turn, "logit": v / SCALE, "decision": decision[0]}
        if mid:
            e = after_end_of_turn(state)
            if e.winner is None:
                row["logit_end"] = self.net.logit(e, player)
                row["lin"] = self.base.score(state, player, False) / SCALE
                row["lin_end"] = self.base.score(e, player, False) / SCALE
                row["fresh"] = sum(1 for c in state.players[player].field if c.entered_turn == state.turn)
        rows.append(row)
        return v

    SN.SetNetEnded.score = wrapped
    deck = decks.build(DECKS["ramp-t"][1])
    a = f"mcts:{args.n}+{P}+setnet={args.net}"
    b = f"mcts:200+{P}"
    t0 = time.time()
    results = []
    for k in range(args.games):
        seed, seat = args.seed + k // 2, k % 2
        agent_a = gate._agent(a, 2 * seed + seat, None)
        act = agent_a.act

        def counted(state, legal, act=act):
            decision[0] += 1
            return act(state, legal)

        agent_a.act = counted
        pts, _ = gate._game(deck, deck, seat, agent_a, gate._agent(b, 2 * seed + 1 - seat, None), seed, "probe",
                            ["ramp-t", "ramp-t"])
        results.append(pts)
        print(f"game {k}: seed {seed} seat {seat} A {pts}  calls so far {len(rows)}  {time.time() - t0:.0f}s",
              flush=True)

    mid = [r for r in rows if r["mid"]]
    ended = [r for r in rows if not r["mid"]]
    both = [r for r in mid if "logit_end" in r]
    d_net = np.array([r["logit"] - r["logit_end"] for r in both])
    d_lin = np.array([r["lin"] - r["lin_end"] for r in both])
    fresh = np.array([r["fresh"] for r in both])

    by = {}
    for r in ended:                             # the spread of the net's turn-end scores within one search
        by.setdefault(r["decision"], []).append(r["logit"])
    spread = [v for v in by.values() if len(v) >= 10]
    sib_sd = np.array([np.std(v) for v in spread])
    sib_gap = np.array([np.percentile(v, 90) - np.percentile(v, 50) for v in spread])

    def stats(x):
        if len(x) == 0:
            return None
        return {"n": int(len(x)), "mean": round(float(np.mean(x)), 4), "sd": round(float(np.std(x)), 4),
                "mean_abs": round(float(np.mean(np.abs(x))), 4),
                "p10": round(float(np.percentile(x, 10)), 4), "p90": round(float(np.percentile(x, 90)), 4)}

    report = {
        "condition": gate.CONDITION, "a": a, "b": b, "seeds": [args.seed, args.seed + (args.games - 1) // 2],
        "games": args.games, "a_points": results, "seconds": round(time.time() - t0),
        "net_calls": len(rows), "ended": len(ended), "mid": len(mid), "mid_share": round(len(mid) / max(len(rows), 1), 4),
        "d_net": stats(d_net), "d_lin": stats(d_lin),
        "d_net_fresh0": stats(d_net[fresh == 0]), "d_net_fresh1plus": stats(d_net[fresh >= 1]),
        "d_lin_fresh0": stats(d_lin[fresh == 0]), "d_lin_fresh1plus": stats(d_lin[fresh >= 1]),
        "within_search_sd_of_ended_logits": stats(sib_sd),
        "within_search_p90_minus_median": stats(sib_gap),
        "corr_d_net_d_lin": round(float(np.corrcoef(d_net, d_lin)[0, 1]), 4) if len(both) > 2 else None,
        "note": "d = logit(mid-turn position) - logit(the same position with the turn ended there); linear in the same "
                "units (score / SCALE). A mid-turn leaf is scored by the net at a moment it never trained on.",
    }
    text = json.dumps(report, indent=1, ensure_ascii=False)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
