#!/bin/bash
# NM2 gen-2 bot directly against v2skx (report only; the architecture thread 10:57Z / 11:59Z; README, seeds in
# analysis/seed-banks.md, J172a-d registered before any game). Code cfd2df6. N measured on this machine under gate load
# right before the gate (samedeck/, same-deck fit against v2skx): ramp-t 93, nemesis-t 84. No check, no fix of N; the
# in-gate same-deck ratio is recorded. Gate 1: A plays ramp-t vs v2skx on nemesis-t; gate 2: A plays nemesis-t vs v2skx
# on ramp-t; 300 pairs each; the pooled score is the reading.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm2g2/v2skx
cd $S/wt_nm2g2gate
export PYTHONPATH=$S/wt_nm2g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
A_RAMP="mcts:93+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-ramp-t.npz:2:1"
A_NEM="mcts:84+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-nemesis-t.npz:2:1"
B="mcts:200+$P"
gate() {  # name deck opponent a seed
  mkdir -p $OUT/$1
  python3 -m svsim.tools.host svsim.tools.gate --deck $2 --opponent $3 --fixed --workers 3 --a "$4" --b "$B" --max 600 --seed $5 --out $OUT/$1/gate.jsonl > $OUT/$1/gate.log 2>&1 || { echo "$1 FAILED"; exit 1; }
  python3 $POOL $OUT/$1/gate.jsonl > $OUT/$1/gate_pooled.txt 2>&1
  echo "$1 done at $(date -u +%H:%M:%S)"
}
gate gate1-ramp ramp-t nemesis-t "$A_RAMP" 81200000
gate gate2-nem nemesis-t ramp-t "$A_NEM" 81300000
python3 $POOL $OUT/gate1-ramp/gate.jsonl $OUT/gate2-nem/gate.jsonl > $OUT/pooled.txt 2>&1
echo "DONE at $(date -u +%H:%M:%S)"
