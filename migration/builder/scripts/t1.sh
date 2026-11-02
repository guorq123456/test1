#!/bin/bash
# T1 (the architecture thread 2026-10-29 02:30Z): 300 fixed pairs each, bank 85800000, Y = mcts:100+plan
cd /home/user/test1
F=analysis/sharednet/fields/B-r1.txt
M=analysis/scaling/models
Y="mcts:100+plan"
run() { timeout 6600 python3 -m svsim.tools.deckgate --x "$2" --y "$Y" --field $F --seed 85800000 --pairs 300 --workers 4 --out runs/t1/$1.jsonl > runs/t1/$1.log 2>&1; }
run x-ramp   "mcts:55+plan+setnet=$M/net-mid-ramp-t.npz+netmid+netany"
run x-nm3    "mcts:49+plan+setnet=$M/net-nm3g3f-elf-nem.npz+netmid+netany"
run xc-ramp  "mcts:55+plan+setnet=$M/net-mid-ramp-t.npz+netmid+netany+netclip"
run xc-nm3   "mcts:49+plan+setnet=$M/net-nm3g3f-elf-nem.npz+netmid+netany+netclip"
