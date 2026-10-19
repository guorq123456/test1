#!/bin/bash
# NM1 generation-2 gates (README edaf773; specs from the builder b9e6f75, registered before any game). Code b9e6f75
# (svsim/ = 0ccb583). A = the gen-2 bot, B = the gen-1 bot (NM1's gate specs, N 94 / 95).
# Gate 1: A plays ramp-t vs B on elf-t; gate 2: A plays elf-t vs B on ramp-t. Each: a 20-pair check; outside
# 0.97-1.03 A's N is fixed once to round(N0 / ratio); then 300 pairs.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm1g2/gate
cd $S/wt_g2gate
export PYTHONPATH=$S/wt_g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
run() {   # name deck opponent N0 asuffix bspec checkseed gateseed
  local name=$1 deck=$2 opp=$3 n0=$4 asuf=$5 B=$6 cs=$7 gs=$8 dir=$OUT/$1
  mkdir -p $dir
  local G="python3 -m svsim.tools.host svsim.tools.gate --deck $deck --opponent $opp --fixed --workers 3"
  $G --a "mcts:$n0$asuf" --b "$B" --max 40 --seed $cs --out $dir/ncheck.jsonl > $dir/ncheck.log 2>&1 || { echo "$name check FAILED"; exit 1; }
  local q=$(python3 $S/scalegates/ratio.py $dir/ncheck.jsonl)
  local n=$(python3 -c "q=$q; print($n0 if 0.97 <= q <= 1.03 else round($n0 / q))")
  echo "{\"N0\": $n0, \"check_ratio\": $q, \"N\": $n}" > $dir/check.json
  echo "$name check ratio $q -> N=$n at $(date -u +%H:%M:%S)"
  $G --a "mcts:$n$asuf" --b "$B" --max 600 --seed $gs --out $dir/gate.jsonl > $dir/gate.log 2>&1 || { echo "$name gate FAILED"; exit 1; }
  python3 $POOL $dir/gate.jsonl > $dir/gate_pooled.txt 2>&1
  echo "$name gate done at $(date -u +%H:%M:%S)"
}
G1_RAMP="mcts:94+$P+setnet=$M/net-nm1f-ramp-elf.npz+netmid+puct=$M/prior-nm1-ramp-t.npz:2:1"
G1_ELF="mcts:95+$P+setnet=$M/net-nm1f-ramp-elf.npz+netmid+puct=$M/prior-nm1-elf-t.npz:2:1"
run gate1-ramp ramp-t elf-t 94 "+$P+setnet=$M/net-nm1g2-ramp-elf.npz+netmid+puct=$M/prior-nm1g2-ramp-t.npz:2:1" "$G1_ELF" 78599000 78500000
run gate2-elf elf-t ramp-t 95 "+$P+setnet=$M/net-nm1g2-ramp-elf.npz+netmid+puct=$M/prior-nm1g2-elf-t.npz:2:1" "$G1_RAMP" 78699000 78600000
python3 $POOL $OUT/gate1-ramp/gate.jsonl $OUT/gate2-elf/gate.jsonl > $OUT/pooled.txt 2>&1
echo "DONE at $(date -u +%H:%M:%S)"
