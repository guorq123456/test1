set -e
cd /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/wt_mid
export PYTHONPATH=/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/wt_mid
python3 /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d10/d10.py /home/user/test1/analysis/scaling/data/gen4/rec/rec-71600018.jsonl.gz --scan /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d8/scan-ramp.json --seed-base 76400000 --out /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d10/d10-71600018.json --workers 3
python3 /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d10/d10.py /home/user/test1/analysis/scaling/data/ramp-t4/rec/rec-75400038.jsonl.gz --scan /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d8/scan-ramp4.json --seed-base 76402000 --out /tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d10/d10-75400038.json --workers 3
echo DONE
