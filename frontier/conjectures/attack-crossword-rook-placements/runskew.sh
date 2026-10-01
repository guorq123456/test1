#!/bin/bash
for N in "$@"; do s=$(date +%s.%N); ./skewcand $N; e=$(date +%s.%N); echo "N=$N wall $(echo "$e - $s" | bc) s"; done
