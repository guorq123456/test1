#!/bin/bash
# Why A runs slower and v2skx faster inside the gate than on the fit (the architecture thread 13:53Z, "顺手查", record
# only). Hypothesis tested here: the in-gate same-deck ratio times each side on ITS OWN positions, the fit times every
# spec on the mixture. Split the 60 position games by who played the deck: rec-81600000 has A's ramp-t and v2skx's
# nemesis-t decisions, rec-81600002 has v2skx's ramp-t and A's nemesis-t. Specs: v2skx and A at the first run's N
# (93 ramp-t, 84 nemesis-t), so the numbers line up with the first run's in-gate 98.41 / 81.11 and 103.64 / 90.54 ms.
# Gate conditions: CPUs 1-3, nice 10, three processes at a time (as svsim.tools.host does for the gate).
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm2g2/v2skx/why
POS=/home/user/test1/analysis/gates/scaling/nm2g2/v2skx/rerun/pos
cd $S/wt_samedeck
export PYTHONPATH=$S/wt_samedeck
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
run() {  # name records deck N prior
  taskset -c 1-3 nice -n 10 python3 analysis/scaling/puct_cost.py --records $POS/$2 --games 30 --deck $3 \
    --spec "v2skx=mcts:200+$P" --spec "A=mcts:$4+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/$5.npz:2:1" \
    --out $OUT/$1.json > $OUT/$1.log 2>&1
}
run ramp-Apos rec-81600000.jsonl.gz ramp-t 93 prior-nm2g2-ramp-t &
run ramp-Bpos rec-81600002.jsonl.gz ramp-t 93 prior-nm2g2-ramp-t &
run nem-Apos rec-81600002.jsonl.gz nemesis-t 84 prior-nm2g2-nemesis-t &
wait
run nem-Bpos rec-81600000.jsonl.gz nemesis-t 84 prior-nm2g2-nemesis-t &
run ramp-Apos-rep rec-81600000.jsonl.gz ramp-t 93 prior-nm2g2-ramp-t &
run ramp-Bpos-rep rec-81600002.jsonl.gz ramp-t 93 prior-nm2g2-ramp-t &
wait
for f in ramp-Apos ramp-Bpos nem-Apos nem-Bpos ramp-Apos-rep ramp-Bpos-rep; do
  python3 -c "import json,sys; d=json.load(open('$OUT/$f.json')); s=d['specs']; print('$f', d['decisions'], 'v2skx', s['v2skx']['ms_per_decision'], 'A', s['A']['ms_per_decision'])"
done > $OUT/split.txt
cat $OUT/split.txt
