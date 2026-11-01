# svwb_tracker：从《影之诗：巅峰对决》客户端自己写的面包屑文件整理真实对局

只读游戏写在硬盘上的崩溃上报「面包屑」（`ShadowverseWB_Data\Persistent\bt\bt-breadcrumbs-0/-1`），再加结算页的截图（Salem 10-31 同意的，只在游戏窗口在前台时拍）。不读内存、不碰游戏进程、不发网络包。所有数据只留在本机。

- `svwb_tracker.py parse --raw RAW --out OUT [--decks decks.txt] [--rank shots\rank.jsonl]`：把存档程序攒下的 `RAW\*.jsonl` 切成一局一局，输出
  `games.jsonl`（完整记录）、`games.csv`（「影之诗战绩本」页面可直接导入）、`review.md`（每局每一手）、`summary.txt`。
  给了 `--rank` 就把截图读出的段位/分组/积分填进表里；没截到的局按前后两张截图和每局加分推算，备注里写明是直读还是推算。
- `rank_reader.py`（只能在 Windows 上跑，要 Pillow + winocr，用普通 `python` 不要 `-I`）：把 `shots\result-*.png` 结算页读成 `shots\rank.jsonl`，
  一行一局：段位、等级、积分、离下一级、本局加减分、分组。段位不在硬盘上的任何文件里，只能这样读。
- 标准流程（Salem 电脑上）：先 `rank_reader.py`，再 `parse --raw C:\claude\svwb-tracker\raw --out C:\claude\svwb-tracker\out --season 第10弹 --decks C:\claude\svwb-tracker\decks.txt --rank C:\claude\svwb-tracker\shots\rank.jsonl`。
- `cards_zh.json`：卡牌编号 → 中文名、职业、费用（从模拟器卡表导出，1069 张）。
- `archetypes.json`：对手套路参照表（职业联赛第 10 节卡表 + 换包前比赛卡表），只用来给对手套路贴标签；`build_archetypes.py` 重建它。
- 面包屑只保留最近几分钟，所以要有一个后台存档程序持续把新条目追加到 `RAW\breadcrumbs-YYYY-MM-DD.jsonl`（一行一条原始 JSON），并在结果出来后 2.6/3.3/3.9/8 秒各拍一张结算页（前台不是游戏就不拍）。Salem 电脑上是 `C:\claude\svwb-tracker\archiver.ps1`。

格式依据 2026-10-31 的 1.10.0 版客户端；调试字段以后可能改。Salem 的对局数据永远不进任何搜索、自对弈和训练。
