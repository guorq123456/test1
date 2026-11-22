"""python tools/probe_period_eval.py G REPS PERIODS   (11-22; LEDGER LD-30; REPS >= 2)
Final-evaluation check on made-up games: freeze the live pool (last-1000 average, A22) after P periods of G games
per member, then read known-strength probes with the frozen-pool evaluator (5 repeats x 1200, last 600)."""
import random, statistics as st, sys, json
import sys as _s; from pathlib import Path as _P; _s.path.insert(0, str(_P(__file__).resolve().parent))
import probe_period_games as PG
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parents[2])]
from ladder import evaluator as E

G, reps, periods = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
PG.P_PROTECT = 1000
PROBES = (-0.06, 0.0, 0.06, 0.12, 0.25)
out = {f"{p*100:+.0f}pp": [] for p in PROBES}
young = []
for r in range(reps):
    rng = random.Random(f"ef:{G}:{r}")
    last = PG.run(G, periods, rng)[-1]
    frozen, strength = [], {}
    for m, _, _, _ in last["rows"]:
        tail = m.pts[-1000:] or [m.cr]
        frozen.append(E.Frozen(mid=m.mid, anon="", craft=m.craft, cr=round(sum(tail) / len(tail)), deck=[],
                               strategy="made-up", protected=m.protected))
        strength[m.mid] = m.strength
    young.append(sum(len(m.pts) < 1000 for m, *_ in last["rows"]) / len(last["rows"]))
    others, mu = E.opponents_for(frozen, None)
    smean = st.mean(strength.values())
    for p in PROBES:
        cs = smean + p
        vals = []
        for k in range(5):
            g = random.Random(f"ef:{G}:{r}:{p}:{k}")
            vals.append(E.repeat_sync(lambda opp, gg: gg.random() < PG.prob(cs, strength[opp.mid]), others, mu,
                                      1200, 600, g))
        out[f"{p*100:+.0f}pp"].append(st.mean(vals))
print(json.dumps({"G": G, "periods": periods, "reps": reps,
                  "share_under_1000_games": round(st.mean(young), 2),
                  "probe_rel_cr": {k: [round(st.mean(v), 1), round(st.stdev(v), 1)] for k, v in out.items()}}))
