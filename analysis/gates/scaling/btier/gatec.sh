#!/bin/bash
# ramp-t B-tier confirmation gate C (README 45212fb): same pair as gates A/B, N 88 no recheck, 75300000-299; code 72a5148
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
cd $S/wt_puct
export PYTHONPATH=$S/wt_puct
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
dir=$S/btier/ramp
python3 -m svsim.tools.host svsim.tools.gate --deck ramp-t --opponent ramp-t --fixed --workers 3 \
  --a "mcts:88+$P+setnet=$M/net-gen3-30000.npz+neteot+puct=$M/prior-ramp-ft-t05.npz:2:1" \
  --b "mcts:120+$P+setnet=$M/net-gen3-30000.npz+neteot" \
  --max 600 --seed 75300000 --out $dir/gate_c.jsonl > $dir/gate_c.log 2>&1
python3 $POOL $dir/gate_c.jsonl > $dir/gate_c_pooled.txt 2>&1
cat $dir/gate_a.jsonl $dir/gate_b.jsonl $dir/gate_c.jsonl > $dir/gate_abc.jsonl
python3 $POOL $dir/gate_abc.jsonl > $dir/gate_abc_pooled.txt 2>&1
echo "gate C done"
