#!/bin/sh
# Step B / C gates (equal compute: same search, only the linear models differ). Run from the checkout root.
V="mcts:100+plan+learned+phased"
M=svsim/learn/phased_models
G="python3 -m svsim.tools.gate --a $V --b $V --versus $V --workers 4"
# G1: a pairing nobody fitted (nemesis-t vs elf-t). A = additive from the other pairings, B = today's fallback.
$G --phased-a $M/additive-all --deck nemesis-t --opponent elf-t --seed 41000000 --max 1200 --out analysis/universal-bot/gates/g1_nemesis_vs_elf.jsonl
$G --phased-a $M/additive-all --deck elf-t --opponent nemesis-t --seed 42000000 --max 1200 --out analysis/universal-bot/gates/g1_elf_vs_nemesis.jsonl
# G2: pirate-t vs elf-t held out of the fit. A = additive from the rest, B = the specialist (both sides).
$G --phased-a $M/additive-lopo-pirate-elf --phased-b $M/specialists-all --deck pirate-t --opponent elf-t --seed 43000000 --max 600 --fixed --out analysis/universal-bot/gates/g2_lopo_pirate_vs_elf.jsonl
