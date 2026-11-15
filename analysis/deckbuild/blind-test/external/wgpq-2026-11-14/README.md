# WGP Qualifier 2026（2026-11-14 JST）职业卡表 vs bot —— 对照材料

只用于比对。这里的职业卡表永远不进搜索、自对弈卡池或训练数据（Salem 批准的「隔离训练」除外，那也只量不装）。

- `wgpq-vs-bot-2026-11-15.md` —— 报告（结论、差距三分、机制、「局部最优」判断、方案评价、下一步）
- `wgpq-2026-11-14.txt` —— WGP 资格赛 70 副（`wgpq/<职业>-<队>-<选手>-<第几套>|代码`）
- `ps1011-2026-11-11.txt` —— 职业联赛第 10 节 + 第 11 节前半 84 副（`label|代码|节|队|选手|职业|胜负`）
- `wgpq-labels.tsv` / `ps1011-names.tsv` / `ps10-names.tsv` —— 套路归类（最接近的已知卡表，≥25 张同名）
- `wgpq-ruler.txt`、`wgpq-ruler.jsonl` —— 尺子联赛：45 副去重 WGP 卡组 × bot 冻结 7 副，两边 mcts:100+plan，6 发牌 × 2 座位，种子 87210000 起
- `watch-elf.md` —— 手写 bot 拿职业连击精灵打 bot 卡组的 6 局逐回合记录（种子 87220000 起）
- 脚本（从仓库根目录运行，路径自动找）：`cmp_lists.py`（解码、分堆、和 bot 池子重合，`--dump` 打中文卡表）、`label_decks.py`（套路归类）、`ruler_league.py`（尺子联赛，`--report` 出表）、`watch_elf.py`（看局）、`deck_mech.py`（按脚本 docstring 读每张卡的机制）

条件：对手卡表已知（牌序、手牌未知）。
