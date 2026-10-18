#!/bin/bash
# mid-turn value net gate, elf-t (README 31f6e3c): A = net-mid-elf-t +netmid + ft-t05 PUCT vs B = elftgen2 + ft-t05 N 71; code 75b5119 (svsim/ = fbb3c21)
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
cd $S/wt_elfmid
export PYTHONPATH=$S/wt_elfmid
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
POOL=/home/user/test1/analysis/oracle-hand/pooled.py
dir=$S/midgate/elft; mkdir -p $dir
G="python3 -m svsim.tools.host svsim.tools.gate --deck elf-t --opponent elf-t --fixed --workers 3"
ASUF="+$P+setnet=$M/net-mid-elf-t.npz+netmid+puct=$M/prior-elft-ft-t05.npz:2:1"
B="mcts:71+$P+setnet=$M/net-elft-gen2-19500.npz+neteot+puct=$M/prior-elft-ft-t05.npz:2:1"
$G --a "mcts:71$ASUF" --b "$B" --max 40 --seed 76299000 --out $dir/ncheck.jsonl > $dir/ncheck.log 2>&1
N=$(python3 - <<PY
import json, subprocess
q = float(subprocess.check_output(["python3", "$S/scalegates/ratio.py", "$dir/ncheck.jsonl"]))
n = 71 if 0.97 <= q <= 1.03 else round(71 / q)
json.dump({"N0": 71, "check_ratio": q, "N": n}, open("$dir/check.json", "w"), indent=1)
print(n)
PY
)
echo "elft check done N=$N"
$G --a "mcts:$N$ASUF" --b "$B" --max 600 --seed 76200000 --out $dir/gate_a.jsonl > $dir/gate_a.log 2>&1
python3 $POOL $dir/gate_a.jsonl > $dir/gate_a_pooled.txt 2>&1
echo "elft gate A done"
$G --a "mcts:$N$ASUF" --b "$B" --max 600 --seed 76300000 --out $dir/gate_b.jsonl > $dir/gate_b.log 2>&1
python3 $POOL $dir/gate_b.jsonl > $dir/gate_b_pooled.txt 2>&1
cat $dir/gate_a.jsonl $dir/gate_b.jsonl > $dir/gate_ab.jsonl
python3 $POOL $dir/gate_ab.jsonl > $dir/gate_ab_pooled.txt 2>&1
echo "elft gate B done"
