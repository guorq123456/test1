import sys, json
sys.path.insert(0, "/home/user/test1")
from svsim.learn.netdata import play
spec = sys.argv[1]
out = []
for g, (a, b) in enumerate((("elf-t", "ramp-t"), ("nemesis-t", "elf-t"), ("elf-t", "elf-t"), ("elf-t", "pirate-t"))):
    rec = play((g, 818181, a, b, spec, 0.0))
    out.append([json.dumps(x, sort_keys=True) for x in rec["actions"]])
print(json.dumps(out))
