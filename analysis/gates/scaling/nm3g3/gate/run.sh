#!/bin/bash
# NM3 generation-3 gate (README "NM3 第 3 代门：选手串登记"; J180a-c, J182a registered before any game). Code ac238cd.
# A = the NM3 gen-3 bot, B = the gen-2 bot; same-deck N 88 / 75 on both sides. No check, no fix of N; the in-gate same-deck
# ratio is recorded. Usage: run.sh gate1 | gate2 | read. Gate 1: A elf-t vs B nemesis-t (84400000); gate 2: A nemesis-t vs
# B elf-t (84500000); 300 pairs each; the verdict is the pooled score.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm3g3/gate
cd $S/wt_nm3g3gate
export PYTHONPATH=$S/wt_nm3g3gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
A_ELF="mcts:88+$P+setnet=$M/net-nm3g3f-elf-nem.npz+netmid+puct=$M/prior-nm3g3-elf-t.npz:2:1"
A_NEM="mcts:75+$P+setnet=$M/net-nm3g3f-elf-nem.npz+netmid+puct=$M/prior-nm3g3-nemesis-t.npz:2:1"
B_ELF="mcts:88+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1"
B_NEM="mcts:75+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-nemesis-t.npz:2:1"
gate() {  # name deck opponent a b seed
  mkdir -p $OUT/$1
  python3 -m svsim.tools.host svsim.tools.gate --deck $2 --opponent $3 --fixed --workers 3 --a "$4" --b "$5" --max 600 --seed $6 --out $OUT/$1/gate.jsonl > $OUT/$1/gate.log 2>&1 || { echo "$1 FAILED"; exit 1; }
  python3 $POOL $OUT/$1/gate.jsonl > $OUT/$1/gate_pooled.txt 2>&1
  echo "$1 done at $(date -u +%H:%M:%S)"
}
case $1 in
  gate1) gate gate1-elf elf-t nemesis-t "$A_ELF" "$B_NEM" 84400000 ;;
  gate2) gate gate2-nem nemesis-t elf-t "$A_NEM" "$B_ELF" 84500000 ;;
  read)
    python3 $POOL $OUT/gate1-elf/gate.jsonl $OUT/gate2-nem/gate.jsonl > $OUT/pooled.txt 2>&1
    python3 /home/user/test1/analysis/gates/scaling/nm2g2/v2skx/cal/samedeck_ratio.py $OUT/gate1-elf/gate.jsonl $OUT/gate2-nem/gate.jsonl elf-t nemesis-t > $OUT/samedeck_ratio.txt 2>&1 ;;
esac
