"""Install C3 hpphase in the ramp-t mirror (architecture thread 17:2x, gate a5a5a73): usage install_c3.py REPO_ROOT"""
import hashlib, json, shutil, sys
from pathlib import Path
root = Path(sys.argv[1]); M = root / "svsim/learn/phased_models"; cand = M / "cand-c3-hpphase-ramp-t-ramp-t"
old = {n: hashlib.sha256((M / n).read_bytes()).hexdigest() for n in ("ramp-t-ramp-t-act.json", "ramp-t-ramp-t-ended.json")}
for n in old:
    shutil.copy(cand / n, M / n)
new = {n: hashlib.sha256((M / n).read_bytes()).hexdigest() for n in old}
assert all(json.loads((M / n).read_text())["extras"] == ["hand", "hpphase"] for n in new)
t = root / "tests/test_learn.py"; s = t.read_text(encoding="utf-8")
for n in old:
    a = f'"{n}": "{old[n]}",'; b = f'"{n}": "{new[n]}",'
    assert s.count(a) == 1, n; s = s.replace(a, b)
rep = [('''    for pairing, folder in (("ramp-t-ramp-t", "cand-c2-hand-ramp"), ("elf-t-elf-t", "cand-c2-hand-elf-t-elf-t"),''',
        '''    for pairing, folder in (("ramp-t-ramp-t", "cand-c3-hpphase-ramp-t-ramp-t"), ("elf-t-elf-t", "cand-c2-hand-elf-t-elf-t"),'''),
       ('''    for mine, theirs, key, extras in (("ramp-t", "ramp-t", ("ramp-t", "ramp-t"), ("hand",)),''',
        '''    for mine, theirs, key, extras in (("ramp-t", "ramp-t", ("ramp-t", "ramp-t"), ("hand", "hpphase")),'''),
       ('''    snapshots), and the normal level stays on Version 15's frozen models."""''',
        '''    snapshots), and the normal level stays on Version 15's frozen models. Since C3 (hpphase on top of hand) passed in the
    ramp-t mirror (analysis a5a5a73: 56.3% over the installed, +60 CR) that pairing's pair is cand-c3-hpphase-ramp-t-ramp-t's."""''')]
for a, b in rep:
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
t.write_text(s, encoding="utf-8")
r = root / "svsim/ui/ratings.json"; d = json.loads(r.read_text(encoding="utf-8"))
d["tiers"]["strong"]["decks"]["ramp-t"] = {"cr": None, "ci": None, "games": 0, "measured_vs": None,
    "note": "待重标：跳费龙镜像装了 C3（hand 之上加 hpphase：双方 HP × 回合段；门 56.3% ± 3.1% 对第 19 版现装，+60 CR，分析线 a5a5a73）；原 1309 不再适用"}
r.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("old", old); print("new", new)
