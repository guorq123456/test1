#!/bin/bash
# NM2 gen-2 bot directly against v2skx, N calibrated inside gate games (the architecture thread 13:53Z; README "门里校准",
# seeds in analysis/seed-banks.md, J175a-d registered before any game). Code cfd2df6, 3 workers as in a gate.
# Usage: run.sh STAGE N_RAMP N_NEM SEED1 SEED2 PAIRS
#   cal1 / cal2: calibration, not scored -- only the in-gate same-deck ratio is computed (samedeck_ratio.py reads ms/ms_b);
#   formal: the gate, pooled score is the reading.
# Gate 1: A plays ramp-t vs v2skx on nemesis-t; gate 2: A plays nemesis-t vs v2skx on ramp-t.
STAGE=$1; NR=$2; NN=$3; SEED1=$4; SEED2=$5; PAIRS=$6
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
HERE=/home/user/test1/analysis/gates/scaling/nm2g2/v2skx/cal
OUT=$HERE/$STAGE
cd $S/wt_nm2g2gate
export PYTHONPATH=$S/wt_nm2g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
A_RAMP="mcts:$NR+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-ramp-t.npz:2:1"
A_NEM="mcts:$NN+$P+setnet=$M/net-nm2g2f-ramp-nem.npz+netmid+puct=$M/prior-nm2g2-nemesis-t.npz:2:1"
B="mcts:200+$P"
gate() {  # name deck opponent a seed
  mkdir -p $OUT/$1
  python3 -m svsim.tools.host svsim.tools.gate --deck $2 --opponent $3 --fixed --workers 3 --a "$4" --b "$B" --max $((2 * PAIRS)) --seed $5 --out $OUT/$1/gate.jsonl > $OUT/$1/gate.log 2>&1 || { echo "$1 FAILED"; exit 1; }
  echo "$1 done at $(date -u +%H:%M:%S)"
}
gate gate1-ramp ramp-t nemesis-t "$A_RAMP" $SEED1
gate gate2-nem nemesis-t ramp-t "$A_NEM" $SEED2
python3 $HERE/samedeck_ratio.py $OUT/gate1-ramp/gate.jsonl $OUT/gate2-nem/gate.jsonl ramp-t nemesis-t > $OUT/samedeck_ratio.txt 2>&1
if [ "$STAGE" = formal ]; then
  for g in gate1-ramp gate2-nem; do python3 $POOL $OUT/$g/gate.jsonl > $OUT/$g/gate_pooled.txt 2>&1; done
  python3 $POOL $OUT/gate1-ramp/gate.jsonl $OUT/gate2-nem/gate.jsonl > $OUT/pooled.txt 2>&1
fi
echo "$STAGE DONE at $(date -u +%H:%M:%S)"
