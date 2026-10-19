#!/bin/bash
# D15 (README 8893379, report only): D15a reply vs A (78100000), D15b omniscient + oracle + reply vs A (78200000); N 83, 300 pairs each, no check. Code 91e88e0.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=$S/d15
mkdir -p $OUT
cd $S/wt_oph
export PYTHONPATH=$S/wt_oph
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
G="python3 -m svsim.tools.host svsim.tools.gate --deck ramp-t --opponent ramp-t --fixed --workers 3"
B="mcts:83+$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1"
A1="mcts-reply:83+$P+lazy+focus+setnet=$M/net-mid-ramp-t.npz+netmid+netreply+puct=$M/prior-ramp-ft-t05.npz:2:1"
A2="mcts-reply:83+$P+lazy+focus+setnet=$M/net-midoph-ramp-t.npz+netmid+netreply+puct=$M/prior-ramp-ft-t05.npz:2:1+oracle"
$G --a "$A1" --b "$B" --max 600 --seed 78100000 --out $OUT/d15a.jsonl > $OUT/d15a.log 2>&1
python3 /home/user/test1/analysis/oracle-hand/pooled.py $OUT/d15a.jsonl > $OUT/d15a_pooled.txt 2>&1
echo "d15a done at $(date -u +%H:%M:%S)"
$G --a "$A2" --b "$B" --max 600 --seed 78200000 --out $OUT/d15b.jsonl > $OUT/d15b.log 2>&1
python3 /home/user/test1/analysis/oracle-hand/pooled.py $OUT/d15b.jsonl > $OUT/d15b_pooled.txt 2>&1
echo "d15b done at $(date -u +%H:%M:%S)"
