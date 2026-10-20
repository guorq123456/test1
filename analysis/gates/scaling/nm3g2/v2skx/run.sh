#!/bin/bash
# NM3 gen-2 bot directly against v2skx (report only; the architecture thread 14:44Z; README "NM3 第 2 代直接对 v2skx",
# seeds in analysis/seed-banks.md, J176a-d registered before any game). Code 7f1d5fb, 3 workers. N calibrated inside
# gate games (14:36Z rule): one 30-pair round, geometric mean of the two in-gate same-deck ratios within 0.90-1.10.
# Usage: run.sh STAGE N_ELF N_NEM SEED1 SEED2 PAIRS
#   cal: not scored -- only the in-gate same-deck ratio is computed (samedeck_ratio.py reads ms/ms_b);
#   formal: the gate, pooled score is the reading.
# Gate 1: A plays elf-t vs v2skx on nemesis-t; gate 2: A plays nemesis-t vs v2skx on elf-t.
STAGE=$1; NE=$2; NN=$3; SEED1=$4; SEED2=$5; PAIRS=$6
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
HERE=/home/user/test1/analysis/gates/scaling/nm3g2/v2skx
OUT=$HERE/$STAGE
cd $S/wt_nm3g2gate
export PYTHONPATH=$S/wt_nm3g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
A_ELF="mcts:$NE+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1"
A_NEM="mcts:$NN+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-nemesis-t.npz:2:1"
B="mcts:200+$P"
gate() {  # name deck opponent a seed
  mkdir -p $OUT/$1
  python3 -m svsim.tools.host svsim.tools.gate --deck $2 --opponent $3 --fixed --workers 3 --a "$4" --b "$B" --max $((2 * PAIRS)) --seed $5 --out $OUT/$1/gate.jsonl > $OUT/$1/gate.log 2>&1 || { echo "$1 FAILED"; exit 1; }
  echo "$1 done at $(date -u +%H:%M:%S)"
}
gate gate1-elf elf-t nemesis-t "$A_ELF" $SEED1
gate gate2-nem nemesis-t elf-t "$A_NEM" $SEED2
python3 $HERE/samedeck_ratio.py $OUT/gate1-elf/gate.jsonl $OUT/gate2-nem/gate.jsonl elf-t nemesis-t > $OUT/samedeck_ratio.txt 2>&1
if [ "$STAGE" = formal ]; then
  for g in gate1-elf gate2-nem; do python3 $POOL $OUT/$g/gate.jsonl > $OUT/$g/gate_pooled.txt 2>&1; done
  python3 $POOL $OUT/gate1-elf/gate.jsonl $OUT/gate2-nem/gate.jsonl > $OUT/pooled.txt 2>&1
fi
echo "$STAGE DONE at $(date -u +%H:%M:%S)"
