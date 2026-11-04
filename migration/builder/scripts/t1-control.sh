#!/bin/bash
# T1 control: the NM3 net on its own pairing through tools.deckgate (seeds 85810000+, the 858 block)
cd /home/user/test1
F=analysis/sharednet/fields/control-elf-nem.txt
M=analysis/scaling/models
X="mcts:49+plan+setnet=$M/net-nm3g3f-elf-nem.npz+netmid"
timeout 6600 python3 -m svsim.tools.deckgate --x "$X" --y "mcts:100+plan" --field $F --seed 85810000 --pairs 100 --workers 4 --out runs/t1/c1.jsonl > runs/t1/c1.log 2>&1
timeout 3000 python3 -m svsim.tools.deckgate --x "$X+netany" --y "mcts:100+plan" --field $F --seed 85810000 --pairs 20 --workers 4 --out runs/t1/c2.jsonl > runs/t1/c2.log 2>&1
tail -6 runs/t1/c1.log
