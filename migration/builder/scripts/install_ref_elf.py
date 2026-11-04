"""After the elf-t C3 install commit: ref-<commit>/ (24 files, README with sha256), VERSIONS alias, test.
usage: install_ref_elf.py REPO_ROOT COMMIT7"""
import hashlib, shutil, sys
from pathlib import Path
root, c = Path(sys.argv[1]), sys.argv[2]
M = root / "svsim/learn/phased_models"; R = M / f"ref-{c}"; R.mkdir()
for f in sorted(M.glob("*.json")):
    shutil.copy(f, R / f.name)
P = M / "ref-a6fdf0a"
differ = sorted(f.name for f in R.glob("*.json") if f.read_bytes() != (P / f.name).read_bytes())
assert differ == ["elf-t-elf-t-act.json", "elf-t-elf-t-ended.json"], differ
sums = "\n".join(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}" for f in sorted(R.glob("*.json")))
(R / "README.md").write_text(f"""# 参考快照 ref-{c}（连击妖镜像装 C3 后的强档，2026-10-08）

`ref{c}`（`svsim/tools/arena.py` 的 VERSIONS）= `mcts:200+plan+learned+phased=ref-{c}+mull=default`：跳费龙镜像、连击妖镜像都装了 C3 以后的强档。

- **来源：** 提交 {c} 时 `svsim/learn/phased_models/` 顶层的 24 个文件，原样复制。
- **和 ref-a6fdf0a 的差别：** 只差 `elf-t-elf-t-{{act,ended}}.json` 两个文件。
  - 新的两个文件与 cand-c3-hpphase-elf-t-elf-t 的同名文件逐字节相同，extras 是 `["hand", "hpphase"]`。
  - 其余 22 个文件与 ref-a6fdf0a 逐字节相同。
- **门：** 分析线 d043630。连击妖镜像，对第 19 版现装，等算力（毫秒比 0.992），定长 300 对。A 得分 53.7% ± 3.5%（50.2～57.2），CR +35。条件：对手卡表已知（牌序、手牌未知）。
- **装机前后同种子核对：** 种子 8800 起，各 1 局。
  - 强档连击妖镜像变了，这就是装机本身。
  - 下面这几局逐步相同：强档跳费龙镜像、强档跳费龙对旗皇、普通档跳费龙镜像（普通档钉在 ref-5558960）。
- **起手：** 钉 `+mull=default`。只冻结了模型和起手，搜索和规则的代码仍是当前检出的。

文件 sha256：

```
{sums}
```
""", encoding="utf-8")
a = root / "svsim/tools/arena.py"; s = a.read_text(encoding="utf-8")
old = '''    "refa6fdf0a": "mcts:200+plan+learned+phased=ref-a6fdf0a+mull=default",'''
new = old + f'''
    # the reference after C3 went into the elf-t mirror too ({c}): the strong level's models in phased_models/ref-{c}
    "ref{c}": "mcts:200+plan+learned+phased=ref-{c}+mull=default",'''
assert s.count(old) == 1; a.write_text(s.replace(old, new), encoding="utf-8")
t = root / "tests/test_learn.py"; s = t.read_text(encoding="utf-8")
old = '''    ref = folder_of("ref-a6fdf0a")                 # after C3 went into the ramp-t mirror (a6fdf0a), the same way'''
new = f'''    ref = folder_of("ref-{c}")                 # after C3 went into the elf-t mirror ({c}), the same way
    assert VERSIONS["ref{c}"] == "mcts:200+plan+learned+phased=ref-{c}+mull=default" and len(load(ref)) == 24
    sums = dict(line.split()[::-1] for line in (ref / "README.md").read_text(encoding="utf-8").splitlines()
                if line.endswith(".json") and len(line) > 64)
    assert len(sums) == 24 and all(hashlib.sha256((ref / n).read_bytes()).hexdigest() == d for n, d in sums.items())
''' + old
assert s.count(old) == 1; t.write_text(s.replace(old, new), encoding="utf-8")
print(R, differ)
