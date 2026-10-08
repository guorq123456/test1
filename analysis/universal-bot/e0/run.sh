#!/bin/sh
# E0 (taken over from the analyst session, 10-08): inferred vs known opponent list, ramp-t vs pirate-t, v2s.
# Script: the analyst's analysis/deck-inference/e0_gate.py (ccr-da4857cc-rkpgwr @ ade107b), unchanged.
L=/mnt/project-files/shadowverse/meta-research-2026-10-07/v2
E=analysis/universal-bot/e0
PYTHONPATH=.:$E python3 $E/e0_gate.py --lists $L --phase sprt --seed 36000000 --workers 4 --out $E/sprt.jsonl
PYTHONPATH=.:$E python3 $E/e0_gate.py --lists $L --phase fixed --pairs 300 --seed 36500000 --workers 4 --out $E/fixed.jsonl
PYTHONPATH=.:$E python3 $E/e0_gate.py --report $E/sprt.jsonl $E/fixed.jsonl
