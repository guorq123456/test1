#!/bin/sh
# ground-truth check of the non-monotone example r=6, a=(2,3,3,4,4,4,5), b=1..5 and (1+q)^6(1+q^3) family
printf "6 7 2 3 3 4 4 4 5 1\n6 7 2 3 3 4 4 4 5 2\n6 7 2 3 3 4 4 4 5 3\n6 7 2 3 3 4 4 4 5 4\n6 7 2 3 3 4 4 4 5 5\n" | /tmp/claude-0/qu/tools/uni | tr '\n' ' '; echo
printf "3 6 2 2 2 2 2 2 1\n3 6 2 2 2 2 2 2 2\n3 6 2 2 2 2 2 2 3\n3 6 2 2 2 2 2 2 4\n3 5 2 2 2 2 2 2\n" | /tmp/claude-0/qu/tools/uni | tr '\n' ' '; echo
