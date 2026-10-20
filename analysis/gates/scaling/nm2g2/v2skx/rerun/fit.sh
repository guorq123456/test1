#!/bin/bash
# Same-deck N for the NM2 gen-2 vs v2skx rerun, fitted on A-vs-v2skx positions (the architecture thread 13:32Z): the 60
# games of pos/ (81600000: A ramp-t N 93 vs v2skx; 81600002: v2skx ramp-t vs A nemesis-t N 84). Three processes at once
# (ramp-t, nemesis-t, a second ramp-t) as the gate's load; N 55 / 70 / 85; the builder's puct_cost.py and
# samedeck_fit.py (ac985de); bot code cfd2df6's models.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm2g2/v2skx/rerun
cd $S/wt_samedeck
export PYTHONPATH=$S/wt_samedeck
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
R=$OUT/pos/rec-cost-gate.jsonl.gz
specs() {  # prior
  echo --spec "v2skx=mcts:200+$P"
  for n in 55 70 85; do echo --spec "n$n=mcts:$n+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/$1.npz:2:1"; done
}
python3 analysis/scaling/puct_cost.py --records $R --games 60 --deck ramp-t $(specs prior-nm2g2-ramp-t) --out $OUT/ramp-t.json > $OUT/ramp-t.log 2>&1 &
python3 analysis/scaling/puct_cost.py --records $R --games 60 --deck nemesis-t $(specs prior-nm2g2-nemesis-t) --out $OUT/nemesis-t.json > $OUT/nemesis-t.log 2>&1 &
python3 analysis/scaling/puct_cost.py --records $R --games 60 --deck ramp-t $(specs prior-nm2g2-ramp-t) --out $OUT/ramp-t-rep.json > $OUT/ramp-t-rep.log 2>&1 &
wait
python3 analysis/scaling/samedeck_fit.py $OUT/ramp-t.json $OUT/nemesis-t.json $OUT/ramp-t-rep.json > $OUT/fit.jsonl 2>&1
cat $OUT/fit.jsonl
