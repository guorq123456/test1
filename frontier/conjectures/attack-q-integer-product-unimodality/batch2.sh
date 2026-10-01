#!/bin/bash
cd /tmp/claude-0/conj/attack-q-integer-product-unimodality
run(){ out=$1; shift; s=$SECONDS; timeout 900 ./c54 "$@" > $out 2>&1; echo "exit=$? elapsed $((SECONDS-s)) args: $*" >> $out; }
case $1 in
 a) run S2_r2_k12_A19.out 2 2 1 12 19 2 0; run S2_r4-6_k10_A16.out 4 6 1 10 16 2 0 ;;
 b) run S2_r7-12_k8_A20.out 7 12 1 8 20 2 0; run S2_r3_k12_A20.out 3 3 11 12 20 2 0 ;;
 c) run S2_r4-30_k4_A60.out 4 30 4 4 60 2 0; run S2_r13-30_k6_A30.out 13 30 5 6 30 2 0 ;;
esac
