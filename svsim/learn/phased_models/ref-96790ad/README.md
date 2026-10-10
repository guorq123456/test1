# 参考快照 ref-96790ad（连击妖镜像装 C3 后的强档，2026-10-08）

`ref96790ad`（`svsim/tools/arena.py` 的 VERSIONS）= `mcts:200+plan+learned+phased=ref-96790ad+mull=default`：跳费龙镜像、连击妖镜像都装了 C3 以后的强档。

- **来源：** 提交 96790ad 时 `svsim/learn/phased_models/` 顶层的 24 个文件，原样复制。
- **和 ref-a6fdf0a 的差别：** 只差 `elf-t-elf-t-{act,ended}.json` 两个文件。
  - 新的两个文件与 cand-c3-hpphase-elf-t-elf-t 的同名文件逐字节相同，extras 是 `["hand", "hpphase"]`。
  - 其余 22 个文件与 ref-a6fdf0a 逐字节相同。
- **门：** 分析线 d043630。连击妖镜像，对第 19 版现装，等算力（毫秒比 0.992），定长 300 对。A 得分 53.7% ± 3.5%（50.2～57.2），CR +35。条件：对手卡表已知（牌序、手牌未知）。
- **装机前后同种子核对：** 种子 8800 起，各 1 局。
  - 强档连击妖镜像变了，这就是装机本身。
  - 下面这几局逐步相同：强档跳费龙镜像、强档跳费龙对旗皇、普通档跳费龙镜像（普通档钉在 ref-5558960）。
- **起手：** 钉 `+mull=default`。只冻结了模型和起手，搜索和规则的代码仍是当前检出的。

文件 sha256：

```
706cf1368b776280980902d1744e4ca385b0e1338671899fb7194051b61987f7  elf-t-elf-t-act.json
f0bc7e4e42dd9c81533d5284f2be8f1f28d1f747170f5b7e0d52744158af9386  elf-t-elf-t-ended.json
ca6a4f2faa82ea504f194db699411af38d44b40cf4e315b15e32846de977ee86  elf-t-nemesis-t-act.json
e9a27705f12c7c521d47421e79d42243c99be039ac34b55edabcc8d95097c329  elf-t-nemesis-t-ended.json
df7e7bff1452d0eccf7e4f23c92c1ed596fa65cc77eee7e5c9c4dc16d38bc64e  elf-t-ramp-t-act.json
8be505d77b9c630631686f89c574c4977053daaa460779af1a797103ab567bb0  elf-t-ramp-t-ended.json
3ff16f2022a5839eca3731dfabbf2e507bbd46cd5fd814d384474aab7ce221b8  nemesis-t-elf-t-act.json
85a74b7ff825cacdcfcfd7379e49cd26eee29baf11f485cea829ba5436bc1b41  nemesis-t-elf-t-ended.json
daafbf1b6831148faf817e16780cbfc08b4230c4670fccbe892188d044ba5ca3  nemesis-t-ramp-t-act.json
a16ecfe405bfec08849a3d0c9d7db216d9e0d929eb33d8f54d02046c9a29b6a7  nemesis-t-ramp-t-ended.json
9500ec681feee9bc27a6105758b4d2e743e04d47322f54c9d9b2e42f97e635c1  pirate-t-elf-t-act.json
9142f45909e6f93dfa350c16b9cb71c600ec3c26028e86dbda42dd6b3e156af2  pirate-t-elf-t-ended.json
865a1a022449cbae35d396cf56a4b53bd7bb1666244e91df7b398f058e11a972  pirate-t-pirate-t-act.json
114e08c70989c30a689902999fc705289fd1e2a41ac2800c2991832d366ddb5e  pirate-t-pirate-t-ended.json
f6638159fa561712c03f29f3e0c51a9519e3a543227112887731fcca831cd0c2  ramp-ramp-act.json
97b0a8f2e747fe2509906c70595ecd702d9805ba2111e08eb52d3c8314bb100e  ramp-ramp-ended.json
9fea10f191afa715d7633a9bca77978b1325cabc84faafd03dd74220de50f865  ramp-t-elf-t-act.json
b2f24b13bd13d0711a3c531c7505a92e2b9d384e1d7cbb5ed64fba7e3dcd1b27  ramp-t-elf-t-ended.json
719ddf1233ad42406cf60dab06e0ea7465d8b12048c73beb2e62ae1d7c57ff69  ramp-t-nemesis-t-act.json
0e76127c561695699e24edd9bd32d940d20094a12f768b135078465795cd01ed  ramp-t-nemesis-t-ended.json
836a671948cf8386573bb58088c25355aa87c72922cd282fcb62840752b52b71  ramp-t-pirate-t-act.json
d575a8ad8d802bbfdf875eff165e3dd68462dbdf1dbc8a88d41d95f1e70dd23f  ramp-t-pirate-t-ended.json
d6067af776b82fb41de63f5c4d859ea1512642eaca706113fabdf77d6d427d81  ramp-t-ramp-t-act.json
dfca8b1c34cc65f6fd9309721f351a7f3eb4b990bd3dcfaafdc963d2705267b4  ramp-t-ramp-t-ended.json
```
