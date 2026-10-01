cd /tmp/claude-0/conj/verify-gp-independence-parity/
(time python3 dp_bigint.py 5 200) > log_k5.txt 2>&1 &
(time python3 dp_bigint.py 6 200) > log_k6.txt 2>&1 &
(time python3 dp_bigint.py 7 150) > log_k7.txt 2>&1 &
(time python3 dp_bigint.py 8 150) > log_k8.txt 2>&1 &
wait
(time python3 dp_bigint.py 9 120) > log_k9.txt 2>&1 &
(time python3 dp_bigint.py 10 120) > log_k10.txt 2>&1 &
wait
