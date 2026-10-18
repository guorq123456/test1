#!/bin/bash
# mid-turn value net gate, ramp-t (README 31f6e3c / this commit): A = net-mid-ramp-t +netmid + ft-t05 PUCT vs B = gen3 + ft-t05 N 88; code fbb3c21
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
cd $S/wt_mid
export PYTHONPATH=$S/wt_mid
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
dir=$S/midgate/ramp; mkdir -p $dir
G="python3 -m svsim.tools.host svsim.tools.gate --deck ramp-t --opponent ramp-t --fixed --workers 3"
ASUF="+$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1"
B="mcts:88+$P+setnet=$M/net-gen3-30000.npz+neteot+puct=$M/prior-ramp-ft-t05.npz:2:1"
$G --a "mcts:88$ASUF" --b "$B" --max 40 --seed 76099000 --out $dir/ncheck.jsonl > $dir/ncheck.log 2>&1
N=$(python3 - <<PY
import json, subprocess
q = float(subprocess.check_output(["python3", "$S/scalegates/ratio.py", "$dir/ncheck.jsonl"]))
n = 88 if 0.97 <= q <= 1.03 else round(88 / q)
json.dump({"N0": 88, "check_ratio": q, "N": n}, open("$dir/check.json", "w"), indent=1)
print(n)
PY
)
echo "ramp check done N=$N"
$G --a "mcts:$N$ASUF" --b "$B" --max 600 --seed 76000000 --out $dir/gate_a.jsonl > $dir/gate_a.log 2>&1
python3 $POOL $dir/gate_a.jsonl > $dir/gate_a_pooled.txt 2>&1
echo "ramp gate A done"
$G --a "mcts:$N$ASUF" --b "$B" --max 600 --seed 76100000 --out $dir/gate_b.jsonl > $dir/gate_b.log 2>&1
python3 $POOL $dir/gate_b.jsonl > $dir/gate_b_pooled.txt 2>&1
cat $dir/gate_a.jsonl $dir/gate_b.jsonl > $dir/gate_ab.jsonl
python3 $POOL $dir/gate_ab.jsonl > $dir/gate_ab_pooled.txt 2>&1
echo "ramp gate B done"
