#!/bin/bash
# Full new bot vs installed strong v2skx (README, registered before any game; report only). Code 75b5119 (svsim/ = fbb3c21).
# Waits for the R1 relabel shard in hand to finish (PAUSE), runs ramp-t then elf-t, then resumes the relabel.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
OUT=/home/user/test1/analysis/gates/scaling/direct
until grep -qE 'paused|DONE|FAILED' $S/r1/run_mine2.log; do sleep 10; done
while pgrep -f relabel.py > /dev/null; do sleep 5; done
echo "relabel stopped: $(tail -1 $S/r1/run_mine2.log) at $(date -u +%H:%M:%S)"
cd $S/wt_elfmid
export PYTHONPATH=$S/wt_elfmid
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
B="mcts:200+$P"
run() {   # deck N0 asuffix checkseed gateseed
  local deck=$1 n0=$2 asuf=$3 cs=$4 gs=$5 dir=$OUT/$1
  mkdir -p $dir
  local G="python3 -m svsim.tools.host svsim.tools.gate --deck $deck --opponent $deck --fixed --workers 3"
  $G --a "mcts:$n0$asuf" --b "$B" --max 40 --seed $cs --out $dir/ncheck.jsonl > $dir/ncheck.log 2>&1
  local q=$(python3 $S/scalegates/ratio.py $dir/ncheck.jsonl)
  local n=$(python3 -c "q=$q; print($n0 if 0.97 <= q <= 1.03 else round($n0 / q))")
  echo "{\"N0\": $n0, \"check_ratio\": $q, \"N\": $n}" > $dir/check.json
  echo "$deck check ratio $q -> N=$n at $(date -u +%H:%M:%S)"
  $G --a "mcts:$n$asuf" --b "$B" --max 600 --seed $gs --out $dir/gate.jsonl > $dir/gate.log 2>&1
  python3 $POOL $dir/gate.jsonl > $dir/gate_pooled.txt 2>&1
  echo "$deck gate done at $(date -u +%H:%M:%S)"
}
run ramp-t 83 "+$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1" 76799000 76700000
run elf-t 67 "+$P+setnet=$M/net-mid-elf-t.npz+netmid+puct=$M/prior-elft-ft-t05.npz:2:1" 76899000 76800000
rm -f $S/r1/PAUSE
nohup $S/r1/run_mine.sh > $S/r1/run_mine3.log 2>&1 &
echo "relabel resumed at $(date -u +%H:%M:%S)"
