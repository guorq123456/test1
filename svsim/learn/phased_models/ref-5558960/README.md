# 参考快照 ref-5558960（陪练台 Version 15 的 bot，2026-10-08）

`ref5558960`（`svsim/tools/arena.py` 的 VERSIONS）= `mcts:200+plan+learned+phased=ref-5558960+mull=default`：Version 15 的强档。

- 来源：提交 5558960（Version 15，05:51:56Z 发布）时 `svsim/learn/phased_models/` 顶层的 22 个文件，原样复制。共 11 个评估器：10 个按组合新拟的，加上借来的原版 ramp 镜像（ramp-ramp）。
- 起手：当时生效的是代码默认（`agents.mulligan.BY_DECK` 为空，连击妖用 D），所以串里写 `+mull=default`，把它钉住。以后代码默认再变，这个快照也不受影响。
- 用途：漂移检查，以及三版以后的对照。CR 标定的参照仍是尺子 `ruler20261008`（20bcfbe，1300 锚）。
- 只冻结了模型和起手，搜索和规则的代码仍是当前检出的（和尺子一样）。
- 核对：同种子 919191 打 8 局（elf-t 对 ramp-t、nemesis-t 对 elf-t、elf-t 对 pirate-t、elf-t 镜像各 2 局），`ref5558960` 和发布时的 `v2s` 逐步相同。
- .gitattributes 让这些文件检出时不转换换行。

文件 sha256：

```
d290e9853caf4fca623dfb64d61836fdd4829d822efe5744cd5e86e860e0cfdb  elf-t-elf-t-act.json
3354212a702799a1f7a72ca2198b21cc61fc38d7a79edb3a12f1a202c833070e  elf-t-elf-t-ended.json
7da583eef7c93c96501d781fc0c084c1c738dedcea1e06284bc997bfa3effb52  elf-t-nemesis-t-act.json
f3b4ebeebe0747be3664830d6f7394c5f67c048b32b70bc690815c27c1ecdaa1  elf-t-nemesis-t-ended.json
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
```
