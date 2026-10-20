#!/bin/bash
# NM3 generation-2 gates (README 47d4360 seeds, J169a-e 2b8f5fc / 150d9b8; specs and N0 from the builder 7f1d5fb, registered before any
# game). Code 7f1d5fb (svsim/ = 2e5e17a apart from training-only changes: the --split option, setpolicy fit info).
# A = the NM3 gen-2 bot (N0 88 / 75; no 1/1.10, B is not v2skx), B = the NM3 gen-1 bot at its install N (elf-t 88, nemesis-t 75).
# Gate 1: A plays elf-t vs B on nemesis-t; gate 2: A plays nemesis-t vs B on elf-t. Each: a 20-pair check; outside
# 0.97-1.03 A's N is fixed once to round(N0 / ratio); then 300 pairs.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/nm3g2/gate
cd $S/wt_nm3g2gate
export PYTHONPATH=$S/wt_nm3g2gate
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
G1_ELF="mcts:88+$P+setnet=$M/net-nm3f-elf-nem.npz+netmid+puct=$M/prior-nm3-elf-t.npz:2:1"
G1_NEM="mcts:75+$P+setnet=$M/net-nm3f-elf-nem.npz+netmid+puct=$M/prior-nm3-nemesis-t.npz:2:1"
run gate1-elf elf-t nemesis-t 88 "+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-elf-t.npz:2:1" "$G1_NEM" 80799000 80700000
run gate2-nem nemesis-t elf-t 75 "+$P+setnet=$M/net-nm3g2f-elf-nem.npz+netmid+puct=$M/prior-nm3g2-nemesis-t.npz:2:1" "$G1_ELF" 80899000 80800000
python3 $POOL $OUT/gate1-elf/gate.jsonl $OUT/gate2-nem/gate.jsonl > $OUT/pooled.txt 2>&1
echo "DONE at $(date -u +%H:%M:%S)"
