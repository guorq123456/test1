for n in $(seq 1 24); do for k in $(seq 1 24); do c=$(( (n+1)*(k+1) )); if [ $c -le 26 ]; then ./bf $n $k; fi; done; done
