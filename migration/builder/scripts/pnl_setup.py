import json, sys
sys.path.insert(0, "/home/user/test1")
from svsim.tools.puzzles import puzzles, play, facts
from svsim.search.foresight import next_lethal_prob
bank = {n: (b, a) for n, b, a in puzzles()}
build, _ = bank["pirate-flags-setup"]
out = {}
for spec in ("level-strong", "mcts:1000+plan+learned+phased"):
    end, me, ms = play(build, spec, 1)
    f = facts(end, me)
    f["flags"] = sorted(c.countdown for c in end.players[me].field if c.countdown is not None)
    f["hand_cards"] = sorted(c.defn.name for c in end.players[me].hand)
    r = next_lethal_prob(end, k=16, seed=0, reply_spec="level-strong", opponent_started=False)
    out[f"{spec} seed 1"] = {"end": f, "P_NL": r["p"], "samples": r["samples"], "ends": r["ends"],
                             "incomplete": r["incomplete"], "ms": r["ms"]}
    print(json.dumps({spec: out[f"{spec} seed 1"]}, ensure_ascii=False), flush=True)
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
