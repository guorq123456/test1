import sys, json
root, spec = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
from svsim.learn.netdata import play
out = []
for g in range(8):
    a, b = (("elf-t", "ramp-t"), ("nemesis-t", "elf-t"), ("elf-t", "pirate-t"), ("elf-t", "elf-t"))[g % 4]
    rec = play((g, 919191, a, b, spec, 0.0))
    out.append([json.dumps(x, sort_keys=True) for x in rec["actions"]])
print(json.dumps(out))
