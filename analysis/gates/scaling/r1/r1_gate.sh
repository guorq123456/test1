#!/bin/bash
# R1 gate, ramp-t (README 96c5b24): A' = net-mid-ramp-t +netmid + prior-ramp-r1 PUCT vs A = same + ft-t05, N0 83.
# Runs in $S/wt_r1, a checkout of the builder commit that adds prior-ramp-r1.npz (svsim/ = fbb3c21).
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/r1/gate
mkdir -p $OUT
cd $S/wt_r1
export PYTHONPATH=$S/wt_r1
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
G="python3 -m svsim.tools.host svsim.tools.gate --deck ramp-t --opponent ramp-t --fixed --workers 3"
ASUF="+$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-r1.npz:2:1"
B="mcts:83+$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1"
$G --a "mcts:83$ASUF" --b "$B" --max 40 --seed 76599000 --out $OUT/ncheck.jsonl > $OUT/ncheck.log 2>&1
q=$(python3 $S/scalegates/ratio.py $OUT/ncheck.jsonl)
N=$(python3 -c "q=$q; print(83 if 0.97 <= q <= 1.03 else round(83 / q))")
echo "{\"N0\": 83, \"check_ratio\": $q, \"N\": $N}" > $OUT/check.json
echo "r1 check ratio $q -> N=$N at $(date -u +%H:%M:%S)"
$G --a "mcts:$N$ASUF" --b "$B" --max 600 --seed 76500000 --out $OUT/gate_a.jsonl > $OUT/gate_a.log 2>&1
python3 $POOL $OUT/gate_a.jsonl > $OUT/gate_a_pooled.txt 2>&1
echo "r1 gate A done at $(date -u +%H:%M:%S)"
$G --a "mcts:$N$ASUF" --b "$B" --max 600 --seed 76600000 --out $OUT/gate_b.jsonl > $OUT/gate_b.log 2>&1
python3 $POOL $OUT/gate_b.jsonl > $OUT/gate_b_pooled.txt 2>&1
cat $OUT/gate_a.jsonl $OUT/gate_b.jsonl > $OUT/gate_ab.jsonl
python3 $POOL $OUT/gate_ab.jsonl > $OUT/gate_ab_pooled.txt 2>&1
echo "r1 gate B done at $(date -u +%H:%M:%S)"
