#!/bin/bash
# B tier (README c01d2c5 / 556daca / b96d546): candidate + prior PUCT (c 2, T 1) wall-clock matched vs candidate; code 72a5148
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
cd $S/wt_puct
export PYTHONPATH=$S/wt_puct
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
mirror () {   # deck net Nb N0 prior check gateA gateB dir
  local deck=$1 net=$2 nb=$3 n0=$4 prior=$5 check=$6 ga=$7 gb=$8 dir=$9
  mkdir -p $dir
  local G="python3 -m svsim.tools.host svsim.tools.gate --deck $deck --opponent $deck --fixed --workers 3"
  local B="mcts:$nb+$P+setnet=$M/$net+neteot"
  local A="+$P+setnet=$M/$net+neteot+puct=$M/$prior:2:1"
  $G --a "mcts:$n0$A" --b "$B" --max 40 --seed $check --out $dir/ncheck.jsonl > $dir/ncheck.log 2>&1
  local N=$(python3 - <<PY
import json, subprocess
q = float(subprocess.check_output(["python3", "$S/scalegates/ratio.py", "$dir/ncheck.jsonl"]))
n = $n0 if 0.97 <= q <= 1.03 else round($n0 / q)
json.dump({"N0": $n0, "check_ratio": q, "N": n}, open("$dir/check.json", "w"), indent=1)
print(n)
PY
)
  echo "$deck check done N=$N"
  $G --a "mcts:$N$A" --b "$B" --max 600 --seed $ga --out $dir/gate_a.jsonl > $dir/gate_a.log 2>&1
  python3 $POOL $dir/gate_a.jsonl > $dir/gate_a_pooled.txt 2>&1
  echo "$deck gate A done"
  $G --a "mcts:$N$A" --b "$B" --max 600 --seed $gb --out $dir/gate_b.jsonl > $dir/gate_b.log 2>&1
  python3 $POOL $dir/gate_b.jsonl > $dir/gate_b_pooled.txt 2>&1
  cat $dir/gate_a.jsonl $dir/gate_b.jsonl > $dir/gate_ab.jsonl
  python3 $POOL $dir/gate_ab.jsonl > $dir/gate_ab_pooled.txt 2>&1
  echo "$deck gate B done"
}
mirror ramp-t net-gen3-30000.npz 120 97 prior-ramp-ft-t05.npz 74999000 74900000 75000000 $S/btier/ramp
mirror elf-t net-elft-gen2-19500.npz 105 75 prior-elft-ft-t05.npz 75199000 75100000 75200000 $S/btier/elft
echo "ALL DONE"
