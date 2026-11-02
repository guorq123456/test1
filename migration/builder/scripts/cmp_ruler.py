import sys, json
sys.path.insert(0, "/home/user/test1")
from svsim.learn.netdata import play
spec = sys.argv[1]
out = []
for g, (a, b) in enumerate((("ramp-t", "ramp-t"), ("elf-t", "ramp-t"))):
    rec = play((g, 616161, a, b, spec, 0.0))
    out.append([json.dumps(x, sort_keys=True) for x in rec["actions"]])
print(json.dumps(out))
