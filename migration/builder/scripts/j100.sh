#!/bin/bash
# J100 (the analysis line, b955062): wait for generation 2's k = 0-4, then the 20-pair check and the gate, on 69e3ad2.
set -e
W=/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/wt-j100
G=/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/scale/gen2/rec
O=/home/user/test1/analysis/scaling/data/j100
until [ $(ls $G/rec-708*.jsonl.gz 2>/dev/null | wc -l) -ge 5 ]; do sleep 30; done
B="mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
A_REST="+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-10000.npz+neteot"
cd $W
echo "check start $(date -u +%H:%M:%S)"
python -m svsim.tools.host svsim.tools.gate --a "mcts:138$A_REST" --b "$B" --deck ramp-t --opponent ramp-t --fixed --max 40 --seed 71299000 --workers 3 --out $O/ncheck_j100.jsonl > $O/ncheck_j100.log 2>&1
N=$(python - $O/ncheck_j100.jsonl <<'PY'
import json, sys
a = b = na = nb = 0.0
for line in open(sys.argv[1], encoding="utf-8"):
    d = json.loads(line)
    for m in d["ms"]: a += m["total"]; na += m["n"]
    for m in d["ms_b"]: b += m["total"]; nb += m["n"]
r = (a / na) / (b / nb)
n = 138 if 0.97 <= r <= 1.03 else round(138 / r)
print(n)
with open(sys.argv[1].replace(".jsonl", "_ratio.json"), "w") as fh:
    json.dump({"ms_per_searched_decision_A": round(a / na, 2), "ms_per_searched_decision_B": round(b / nb, 2),
               "ratio": round(r, 4), "N": n, "decisions_A": na, "decisions_B": nb}, fh, indent=1)
PY
)
echo "N=$N $(date -u +%H:%M:%S)"
python -m svsim.tools.host svsim.tools.gate --a "mcts:$N$A_REST" --b "$B" --deck ramp-t --opponent ramp-t --fixed --max 600 --seed 71200000 --workers 3 --out $O/gate_j100.jsonl > $O/gate_j100.log 2>&1
echo "gate done $(date -u +%H:%M:%S)"
