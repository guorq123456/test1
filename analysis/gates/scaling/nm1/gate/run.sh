#!/bin/bash
# NM1 gates (README c66d599; specs and N0 from the builder cb81fd4, registered before any game). Code cb81fd4
# (svsim/ = 91e88e0). Gate 1: A plays ramp-t vs B (v2skx) on elf-t; gate 2: A plays elf-t vs B on ramp-t.
# Each: a 20-pair check; outside 0.97-1.03 the N is fixed once to round(N0 / ratio); then 300 pairs.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm1/gate
cd $S/wt_nm1
export PYTHONPATH=$S/wt_nm1
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
B="mcts:200+$P"
run() {   # name deck opponent N0 asuffix checkseed gateseed
  local name=$1 deck=$2 opp=$3 n0=$4 asuf=$5 cs=$6 gs=$7 dir=$OUT/$1
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
run gate1-ramp ramp-t elf-t 99 "+$P+setnet=$M/net-nm1f-ramp-elf.npz+netmid+puct=$M/prior-nm1-ramp-t.npz:2:1" 77799000 77700000
run gate2-elf elf-t ramp-t 91 "+$P+setnet=$M/net-nm1f-ramp-elf.npz+netmid+puct=$M/prior-nm1-elf-t.npz:2:1" 77899000 77800000
python3 $POOL $OUT/gate1-ramp/gate.jsonl $OUT/gate2-elf/gate.jsonl > $OUT/pooled.txt 2>&1
echo "DONE at $(date -u +%H:%M:%S)"
