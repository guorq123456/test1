#!/bin/bash
# NM3 generation-2 gates reopened under the new rules (the architecture thread 11:44Z; README, seeds in
# analysis/seed-banks.md, J173a-d registered before any game). Code 7f1d5fb. A = the NM3 gen-2 bot, B = the NM3 gen-1
# bot; N by same-deck offline timing: elf-t 88 and nemesis-t 75 on both sides (gen-2 / gen-1 1.004 / 1.006). No check, no
# fix of N; the in-gate same-deck ratio is recorded. Gate 1: A plays elf-t vs B on nemesis-t; gate 2: A plays nemesis-t
# vs B on elf-t; 300 pairs each; the verdict is the pooled score.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm3g2/regate
cd $S/wt_nm3g2gate
export PYTHONPATH=$S/wt_nm3g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
A_ELF="mcts:88+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1"
A_NEM="mcts:75+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-nemesis-t.npz:2:1"
B_ELF="mcts:88+$P+setnet=$M/net-nm3f-elf-nem.npz+netmid+puct=$M/prior-nm3-elf-t.npz:2:1"
B_NEM="mcts:75+$P+setnet=$M/net-nm3f-elf-nem.npz+netmid+puct=$M/prior-nm3-nemesis-t.npz:2:1"
gate() {  # name deck opponent a b seed
  mkdir -p $OUT/$1
  python3 -m svsim.tools.host svsim.tools.gate --deck $2 --opponent $3 --fixed --workers 3 --a "$4" --b "$5" --max 600 --seed $6 --out $OUT/$1/gate.jsonl > $OUT/$1/gate.log 2>&1 || { echo "$1 FAILED"; exit 1; }
  python3 $POOL $OUT/$1/gate.jsonl > $OUT/$1/gate_pooled.txt 2>&1
  echo "$1 done at $(date -u +%H:%M:%S)"
}
gate gate1-elf elf-t nemesis-t "$A_ELF" "$B_NEM" 81400000
gate gate2-nem nemesis-t elf-t "$A_NEM" "$B_ELF" 81500000
python3 $POOL $OUT/gate1-elf/gate.jsonl $OUT/gate2-nem/gate.jsonl > $OUT/pooled.txt 2>&1
echo "DONE at $(date -u +%H:%M:%S)"
