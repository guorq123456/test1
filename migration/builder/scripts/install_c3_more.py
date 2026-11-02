"""C3 (hpphase) into more pairings after a6fdf0a: usage install_c3_more.py REPO_ROOT [--elf] [--ramp-ramp]
--elf: elf-t mirror (analysis d043630, 53.7% +- 3.5, +35 CR), extras hand,hpphase.
--ramp-ramp: the original Ramp mirror (off by default; only once its gate, bank 63900000, has passed), extras hpphase."""
import hashlib, json, shutil, sys
from pathlib import Path
root = Path(sys.argv[1]); flags = set(sys.argv[2:]); assert flags and flags <= {"--elf", "--ramp-ramp"}, flags
M = root / "svsim/learn/phased_models"; t = root / "tests/test_learn.py"; s = t.read_text(encoding="utf-8")
r = root / "svsim/ui/ratings.json"; d = json.loads(r.read_text(encoding="utf-8"))
def swap(pairing, folder, extras):
    global s
    old = {n: hashlib.sha256((M / n).read_bytes()).hexdigest() for n in (f"{pairing}-act.json", f"{pairing}-ended.json")}
    for n in old:
        shutil.copy(M / folder / n, M / n)
    new = {n: hashlib.sha256((M / n).read_bytes()).hexdigest() for n in old}
    assert all(json.loads((M / n).read_text())["extras"] == list(extras) for n in new)
    for n in old:
        a, b = f'"{n}": "{old[n]}",', f'"{n}": "{new[n]}",'
        assert s.count(a) == 1, n; s = s.replace(a, b)
    print(pairing, "old", old, "new", new)
    return old
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]; s = s.replace(a, b)
doc_end = '''    ramp-t mirror (analysis a5a5a73: 56.3% over the installed, +60 CR) that pairing's pair is cand-c3-hpphase-ramp-t-ramp-t's."""'''
extra_doc = []
if "--elf" in flags:
    swap("elf-t-elf-t", "cand-c3-hpphase-elf-t-elf-t", ("hand", "hpphase"))
    rep('''("elf-t-elf-t", "cand-c2-hand-elf-t-elf-t"),''', '''("elf-t-elf-t", "cand-c3-hpphase-elf-t-elf-t"),''')
    rep('''("elf-t", "elf-t", ("elf-t", "elf-t"), ("hand",)),''', '''("elf-t", "elf-t", ("elf-t", "elf-t"), ("hand", "hpphase")),''')
    extra_doc.append("the elf-t mirror's (d043630: 53.7%, +35 CR) is cand-c3-hpphase-elf-t-elf-t's")
    d["tiers"]["strong"]["decks"]["elf-t"] = {"cr": None, "ci": None, "games": 0, "measured_vs": None,
        "note": "待重标：连击妖镜像装了 C3（hand 之上加 hpphase：双方 HP × 回合段；门 53.7% ± 3.5% 对第 19 版现装，+35 CR，分析线 d043630）；原 1348 不再适用"}
if "--ramp-ramp" in flags:
    old = swap("ramp-ramp", "cand-c3-hpphase-ramp-ramp", ("hpphase",))
    rep('''                            ("elf-t-nemesis-t", "cand-c2-hand-elf-t-nemesis-t")):''',
        '''                            ("elf-t-nemesis-t", "cand-c2-hand-elf-t-nemesis-t"), ("ramp-ramp", "cand-c3-hpphase-ramp-ramp")):''')
    rep('''                                      ("ramp", "ramp", ("ramp", "ramp"), ())):''',
        '''                                      ("ramp", "ramp", ("ramp", "ramp"), ("hpphase",))):''')
    rep('''    before = {n: d for n, d in pins.items() if not n.startswith(("ramp-t-ramp-t", "elf-t-elf-t", "elf-t-nemesis-t"))}''',
        '''    before = {n: d for n, d in pins.items() if not n.startswith(("ramp-t-ramp-t", "elf-t-elf-t", "elf-t-nemesis-t",
                                                                 "ramp-ramp"))}
    before.update({"ramp-ramp-act.json": "%s",
                   "ramp-ramp-ended.json": "%s"})''' % (old["ramp-ramp-act.json"], old["ramp-ramp-ended.json"]))
    extra_doc.append("the original Ramp mirror's (ramp-ramp, the Game8 deck) is cand-c3-hpphase-ramp-ramp's")
rep(doc_end, doc_end[:-3] + "; " + "; ".join(extra_doc) + '."""')
t.write_text(s, encoding="utf-8")
r.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
