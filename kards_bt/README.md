# KARDS 赛事 Bradley–Terry 实力分

用 Bradley–Terry（BT）模型，从 KARDS 赛事的逐场对局里估计每位选手**随时间变化**的实力分（Elo 刻度，平均 1500）。

## 一键复现

```bash
pip install -r requirements.txt
python3 scrapers/battlefy.py   # 抓 Battlefy（已有的 data/raw 会跳过）
python3 scrapers/startgg.py    # 抓 start.gg
python3 scrapers/challonge.py  # 抓官方赛事（需要环境变量 CHALLONGE_API_KEY，赛事清单在 data/challonge_events.csv）
python3 normalize.py           # 合并成 data/matches.csv + data/players.csv
python3 evaluate.py            # （可选）样本外验证，挑半衰期和先验
python3 bt.py                  # 算出 data/ratings_timeline.csv
python3 build_site.py          # 生成交互页面 site/index.html
```

## 数据覆盖

| 赛事 | 平台 | 状态 |
|---|---|---|
| KARDS Open #1 – VII、Open: Singleton、Operation: Kards（2020.05 – 2021.06，983 Media） | Battlefy | ✅ 已收录 |
| KARDS Open VIII – XIV（2021.08 – 2022.11，983 Media） | start.gg | ✅ 已收录 |
| KARDS 世界赛 2021、2022（约 100 人，小组循环赛 + 双败淘汰赛；未公开列出） | start.gg | ✅ 已收录，类别 `official` |
| Weekday Skirmish、Blitz、Homebrew Brawl 等社区赛 | Battlefy / start.gg | 已抓取，类别为 `community`，默认不计入 |
| 官方 OCC 月赛、扩展赛、2023 年起的世界赛 | Challonge | ❌ 未收录：页面有 Cloudflare，API 需要 key；已知链接列在 `data/challonge_events.csv` |
| 2024、2025 世界赛，2023–2024 OCC，2025–26 扩展赛 | 未知 | ❌ 没找到公开的对阵表 |

共 18 站、3866 场有效对局。轮空、弃权/取消资格、双败、未录入结果的对局不计入。

## 模型

每站比赛结束后，用**截至当天**的全部对局拟合一次：

- P(i 胜 j) = σ(β_i − β_j)，一个系列赛（Bo3/Bo5）算一场；`--games` 改成按小局计
- 时间衰减：d 天前的对局权重为 0.5^(d / 365)
- 先验：β ~ N(0, 0.8²)，防止场次少的选手分数爆表
- ± 是拉普拉斯近似（逆 Hessian）给出的 1 个标准误
- BT 分 = 1500 + β × 400 / ln 10

半衰期和先验由 `evaluate.py` 挑出：用每站赛前的分数预测该站胜负，
样本外 log loss 0.660（抛硬币为 0.693），准确率约 59%。

## 文件

- `data/raw/` 平台原始数据（JSON）
- `data/matches.csv` 规整后的对局表；`valid=1` 的才参与计算，`category` 为 `open` / `open_special` / `official` / `community`
- `data/players.csv` 选手身份表：同一人在不同平台的账号按游戏内 ID 合并
- `data/aliases.csv`（可选，自己建）：`alias,canonical` 两列，手动把两个名字指向同一人
- `data/ratings_timeline.csv` 每站之后每位选手的分数、标准误、累计场次

## 补上官方赛事

官方赛事在 Challonge 上（例如 WC 2023 淘汰赛 `challonge.com/iwu8v1m9`）。

1. 在 challonge.com 注册并验证邮箱，到 <https://challonge.com/settings/developer> 生成 API v1 key
   （找不到的话，新版开发者门户在 <https://connect.challonge.com>）
2. 把 key 存成环境变量 `CHALLONGE_API_KEY`，不要写进代码或提交到仓库
3. 在 `data/challonge_events.csv` 里每行填一个赛事：`url,event,category,stage`，`category` 填 `official`
4. 运行 `scrapers/challonge.py`，再依次跑 `normalize.py`、`bt.py`、`build_site.py`

每个赛事只用 1 次 API 请求，已下载的会跳过。免费账号每月限 500 次。
