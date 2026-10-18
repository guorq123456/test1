#!/bin/bash
# D11 self-play (A vs A, 200 games per mirror) then D12 (ramp-t mcts:166 vs mcts:83, 300 pairs). README registration; code d00ab33.
S=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad
cd $S/wt_r1
export PYTHONPATH=$S/wt_r1
P="plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M=analysis/scaling/models
RAMP="$P+setnet=$M/net-mid-ramp-t.npz+netmid+puct=$M/prior-ramp-ft-t05.npz:2:1"
ELF="$P+setnet=$M/net-mid-elf-t.npz+netmid+puct=$M/prior-elft-ft-t05.npz:2:1"
D11=$S/d11; mkdir -p $D11/ramp $D11/elft
python3 -m svsim.learn.scaledata play --base 76900000 --shards 0 1 --per-shard 200 --deck ramp-t --opponent ramp-t --spec "mcts:83+$RAMP" --workers 3 --out $D11/ramp > $D11/ramp.log 2>&1
echo "d11 ramp self-play done at $(date -u +%H:%M:%S)"
python3 -m svsim.learn.scaledata play --base 77000000 --shards 0 1 --per-shard 200 --deck elf-t --opponent elf-t --spec "mcts:67+$ELF" --workers 3 --out $D11/elft > $D11/elft.log 2>&1
echo "d11 elf self-play done at $(date -u +%H:%M:%S)"
OUT=/home/user/test1/analysis/gates/scaling/d12
python3 -m svsim.tools.host svsim.tools.gate --deck ramp-t --opponent ramp-t --fixed --workers 3 --a "mcts:166+$RAMP" --b "mcts:83+$RAMP" --max 600 --seed 77100000 --out $S/d12_gate.jsonl > $S/d12_gate.log 2>&1
python3 /home/user/test1/analysis/oracle-hand/pooled.py $S/d12_gate.jsonl > $S/d12_gate_pooled.txt 2>&1
echo "d12 done at $(date -u +%H:%M:%S)"
