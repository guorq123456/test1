import sys, json
root, spec = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
from svsim.learn.netdata import play
out = []
for g, (a, b) in enumerate((("ramp", "ramp"), ("rhino", "ramp"))):
    rec = play((g, 515151, a, b, spec, 0.0))
    out.append([json.dumps(x, sort_keys=True) for x in rec["actions"]])
print(json.dumps(out))
