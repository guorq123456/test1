#!/bin/bash
# D13' step 2 (README c7635b6, report only): A_or = net-midoph-ramp-t +netmid + ft-t05 PUCT +oracle vs A, N 83 both, 300 pairs, no check. Code 4e55dc6.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/d13p/aor
mkdir -p $OUT
cd $S/wt_oph
export PYTHONPATH=$S/wt_oph
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
A="mcts:83+$P+setnet=$M/net-midoph-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1+oracle"
B="mcts:83+$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1"
python3 -m svsim.tools.host svsim.tools.gate --deck ramp-t --opponent ramp-t --fixed --workers 3 --a "$A" --b "$B" --max 600 --seed 77200000 --out $OUT/gate.jsonl > $OUT/gate.log 2>&1
python3 /home/user/test1/analysis/oracle-hand/pooled.py $OUT/gate.jsonl > $OUT/gate_pooled.txt 2>&1
echo "aor done at $(date -u +%H:%M:%S)"
