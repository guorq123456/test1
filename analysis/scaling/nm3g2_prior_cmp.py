"""NM3 gen-2 elf-t diagnosis (1): the gen-1 vs the gen-2 elf-t prior on the gen-2 holdout's elf-t decisions (report only).

DEC holds the holdout shards encoded with setpolicy encode --deck elf-t (dec-80600000.npz ... dec-80600008.npz); the
search targets come from the gen-1 bots that played those shards. No game is played, so no seed is drawn.

    python analysis/scaling/nm3g2_prior_cmp.py DEC CARDS OUT
"""
import copy, json, sys
import numpy as np
ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from svsim.learn import setpolicy as SP
D = sys.argv[1]; CARDS = sys.argv[2]; OUT = sys.argv[3]
files = [f"{D}/dec-{80600000 + 2 * h}.npz" for h in range(5)]
data = SP.Decisions(files, CARDS)
def remap(pol, d):
    tab = {c: i for i, c in enumerate(pol.card_ids.tolist())}
    m = np.array([tab[c] for c in d.card_ids.tolist()])
    e = copy.copy(d); e.cards = m[d.cards]; e.card_ids = pol.card_ids; e.static = pol.static.astype(np.float32)
    return e
pols = {g: SP.SetPolicy.load(f"{ROOT}/analysis/scaling/models/{f}.npz")
        for g, f in (("g1", "prior-nm3-elf-t"), ("g2", "prior-nm3g2-elf-t"))}
P = {g: p.evaluate(remap(p, data)) for g, p in pols.items()}
moff, pi, kind, tkind = data.moff, data.pi.astype(np.float64), data.kind, data.tkind
n = data.n
def per_decision_argmax(x):
    out = np.empty(n, np.int64)
    for i in range(n):
        a, b = moff[i], moff[i + 1]; out[i] = a + int(np.argmax(x[a:b]))
    return out
pi_s = pi.copy()                                   # tau 0.5 targets, as in the fits
for i in range(n):
    a, b = moff[i], moff[i + 1]; v = pi[a:b] ** 2; s = v.sum(); pi_s[a:b] = v / s if s > 0 else v
top = {g: per_decision_argmax(P[g]) for g in P}; top_pi = per_decision_argmax(pi)
nl = np.diff(moff)
multi = nl > 1                                     # decisions with a real choice
res = {"decisions": int(n), "with_choice": int(multi.sum())}
for g in P:
    ce = -np.add.reduceat(pi_s * np.log(P[g] + 1e-12), moff[:-1])
    res[g] = {"ce_tau05": round(float(ce.mean()), 5),
              "ce_tau05_choice": round(float(ce[multi].mean()), 5),
              "top1_vs_search": round(float((top[g] == top_pi)[multi].mean()), 4),
              "p_on_search_top": round(float(P[g][top_pi][multi].mean()), 4)}
agree = top["g1"] == top["g2"]
res["top1_g1_vs_g2"] = round(float(agree[multi].mean()), 4)
KN, TK = SP.KINDS, SP.TARGET_KINDS
def table(keyf, names):
    rows = {}
    for i in np.flatnonzero(multi):
        k = keyf(i); r = rows.setdefault(k, [0, 0, 0, 0])
        r[0] += 1; r[1] += top["g1"][i] == top_pi[i]; r[2] += top["g2"][i] == top_pi[i]; r[3] += agree[i]
    return {names(k): {"n": r[0], "g1_hits_search": round(r[1] / r[0], 4), "g2_hits_search": round(r[2] / r[0], 4),
                       "g1_g2_agree": round(r[3] / r[0], 4)} for k, r in sorted(rows.items(), key=lambda kv: -kv[1][0])}
res["by_search_top_kind"] = table(lambda i: (int(kind[top_pi[i]]), int(tkind[top_pi[i]])),
                                  lambda k: f"{KN[k[0]]}->{TK[k[1]]}")
res["by_turn"] = table(lambda i: min(int(data.turn[i]), 14) // 2 * 2, lambda k: f"turn {k}-{k + 1}" if k < 14 else "turn 14+")
# where the two disagree: which kind each prior prefers
dis = {}
for i in np.flatnonzero(multi & ~agree):
    k = (KN[kind[top["g1"][i]]], KN[kind[top["g2"][i]]]); dis[k] = dis.get(k, 0) + 1
res["disagreements_g1kind_to_g2kind"] = {f"{a} -> {b}": c for (a, b), c in sorted(dis.items(), key=lambda kv: -kv[1])[:12]}
json.dump(res, open(OUT, "w"), indent=1); print(json.dumps(res, indent=1))
