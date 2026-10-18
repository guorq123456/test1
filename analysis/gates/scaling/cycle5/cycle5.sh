#!/bin/bash
# next-cycle gates (README 45212fb / f13dfcf): new value net + new prior vs candidate + prior (the self-play players); code 72a5148
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
cd $S/wt_puct
export PYTHONPATH=$S/wt_puct
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
mirror () {   # deck A-suffix B-spec N0 check gateA gateB dir
  local deck=$1 asuf=$2 B=$3 n0=$4 check=$5 ga=$6 gb=$7 dir=$8
  mkdir -p $dir
  local G="python3 -m svsim.tools.host svsim.tools.gate --deck $deck --opponent $deck --fixed --workers 3"
  $G --a "mcts:$n0$asuf" --b "$B" --max 40 --seed $check --out $dir/ncheck.jsonl > $dir/ncheck.log 2>&1
  local N=$(python3 - <<PY
import json, subprocess
q = float(subprocess.check_output(["python3", "$S/scalegates/ratio.py", "$dir/ncheck.jsonl"]))
n = $n0 if 0.97 <= q <= 1.03 else round($n0 / q)
json.dump({"N0": $n0, "check_ratio": q, "N": n}, open("$dir/check.json", "w"), indent=1)
print(n)
PY
)
  echo "$deck check done N=$N"
  $G --a "mcts:$N$asuf" --b "$B" --max 600 --seed $ga --out $dir/gate_a.jsonl > $dir/gate_a.log 2>&1
  python3 $POOL $dir/gate_a.jsonl > $dir/gate_a_pooled.txt 2>&1
  echo "$deck gate A done"
  $G --a "mcts:$N$asuf" --b "$B" --max 600 --seed $gb --out $dir/gate_b.jsonl > $dir/gate_b.log 2>&1
  python3 $POOL $dir/gate_b.jsonl > $dir/gate_b_pooled.txt 2>&1
  cat $dir/gate_a.jsonl $dir/gate_b.jsonl > $dir/gate_ab.jsonl
  python3 $POOL $dir/gate_ab.jsonl > $dir/gate_ab_pooled.txt 2>&1
  echo "$deck gate B done"
}
mirror ramp-t "+$P+setnet=$M/net-gen5-68500.npz+neteot+puct=$M/prior-ramp-gen5-ft-t05.npz:2:1" \
  "mcts:88+$P+setnet=$M/net-gen3-30000.npz+neteot+puct=$M/prior-ramp-ft-t05.npz:2:1" 88 75699000 75600000 75700000 $S/cycle5/ramp
mirror elf-t "+$P+setnet=$M/net-elft-gen4-38500.npz+neteot+puct=$M/prior-elft-gen4-ft-t05.npz:2:1" \
  "mcts:71+$P+setnet=$M/net-elft-gen2-19500.npz+neteot+puct=$M/prior-elft-ft-t05.npz:2:1" 71 75899000 75800000 75900000 $S/cycle5/elft
echo "ALL DONE"
