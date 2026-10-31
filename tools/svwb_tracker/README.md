# svwb_tracker：从《影之诗：巅峰对决》客户端自己写的面包屑文件整理真实对局

只读游戏写在硬盘上的崩溃上报「面包屑」（`ShadowverseWB_Data\Persistent\bt\bt-breadcrumbs-0/-1`），不读内存、不截屏、不碰游戏进程、不发网络包。所有数据只留在本机。

- `svwb_tracker.py parse --raw RAW --out OUT [--decks decks.txt]`：把存档程序攒下的 `RAW\*.jsonl` 切成一局一局，输出
  `games.jsonl`（完整记录）、`games.csv`（「影之诗战绩本」页面可直接导入）、`review.md`（每局每一手）、`summary.txt`。
- `cards_zh.json`：卡牌编号 → 中文名、职业、费用（从模拟器卡表导出，1069 张）。
- `archetypes.json`：对手套路参照表（职业联赛第 10 节卡表 + 换包前比赛卡表），只用来给对手套路贴标签；`build_archetypes.py` 重建它。
- 面包屑只保留最近几分钟，所以要有一个后台存档程序持续把新条目追加到 `RAW\breadcrumbs-YYYY-MM-DD.jsonl`（一行一条原始 JSON）。Salem 电脑上是 `C:\claude\svwb-tracker\archiver.ps1`。

格式依据 2026-10-31 的 1.10.0 版客户端；调试字段以后可能改。Salem 的对局数据永远不进任何搜索、自对弈和训练。
