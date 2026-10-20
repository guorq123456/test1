#!/bin/bash
# NM3 elf-t regression: three report-only half-gates on the elf-t seat (the architecture thread 10:30Z; README, seeds in
# analysis/seed-banks.md, J171a-e registered before any game). Code 7f1d5fb. A plays elf-t vs B = the NM3 gen-1 bot on
# nemesis-t (install N 75). b1: gen-2 net + gen-1 elf-t prior; b2: gen-1 net + gen-2 elf-t prior (each a 20-pair
# check, outside 0.97-1.03 A's N fixed once to round(88 / ratio), then 300 pairs); a: the gen-2 elf-t bot at N 88 with no
# time alignment (300 pairs, no check).
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm3g2/elfcheck
cd $S/wt_nm3g2gate
export PYTHONPATH=$S/wt_nm3g2gate
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
B="mcts:75+$P+setnet=$M/net-nm3f-elf-nem.npz+netmid+puct=$M/prior-nm3-nemesis-t.npz:2:1"
G="python3 -m svsim.tools.host svsim.tools.gate --deck elf-t --opponent nemesis-t --fixed --workers 3"
run() {   # name N0 asuffix checkseed gateseed
  local name=$1 n0=$2 asuf=$3 cs=$4 gs=$5 dir=$OUT/$1
  mkdir -p $dir
  $G --a "mcts:$n0$asuf" --b "$B" --max 40 --seed $cs --out $dir/ncheck.jsonl > $dir/ncheck.log 2>&1 || { echo "$name check FAILED"; exit 1; }
  local q=$(python3 $S/scalegates/ratio.py $dir/ncheck.jsonl)
  local n=$(python3 -c "q=$q; print($n0 if 0.97 <= q <= 1.03 else round($n0 / q))")
  echo "{\"N0\": $n0, \"check_ratio\": $q, \"N\": $n}" > $dir/check.json
  echo "$name check ratio $q -> N=$n at $(date -u +%H:%M:%S)"
  $G --a "mcts:$n$asuf" --b "$B" --max 600 --seed $gs --out $dir/gate.jsonl > $dir/gate.log 2>&1 || { echo "$name gate FAILED"; exit 1; }
  python3 $POOL $dir/gate.jsonl > $dir/gate_pooled.txt 2>&1
  echo "$name gate done at $(date -u +%H:%M:%S)"
}
run b1 88 "+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3-elf-t.npz:2:1" 80999000 80900000
run b2 88 "+$P+setnet=$M/net-nm3f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1" 81099000 81000000
mkdir -p $OUT/a
$G --a "mcts:88+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1" --b "$B" --max 600 --seed 81100000 --out $OUT/a/gate.jsonl > $OUT/a/gate.log 2>&1 || { echo "a gate FAILED"; exit 1; }
python3 $POOL $OUT/a/gate.jsonl > $OUT/a/gate_pooled.txt 2>&1
echo "a gate done at $(date -u +%H:%M:%S)"
echo "DONE at $(date -u +%H:%M:%S)"
