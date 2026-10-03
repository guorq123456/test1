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
| OCC 月赛 2021.05 – 2024.11（同月的资格赛 A/B + Top 8 合并成一站；2024 年 4–8 月只有 Top 8） | Challonge | ✅ 已收录，类别 `official` |
| OCC Ultimate I – III（2023，8 人邀请赛） | Challonge | ✅ 已收录，类别 `official` |
| KARDS 世界赛 2023（128 人小组赛 + 淘汰赛）、2024、2025（决赛阶段） | Challonge | ✅ 已收录，类别 `official` |
| 2025 年 4 个扩展赛（Blood & Iron、United Front、Naval Warfare、Air Supremacy，各含 Top 8） | Challonge | ✅ 已收录，类别 `official` |
| 2026 年冬、春、夏、秋季赛（各含 Top 8） | Challonge | ✅ 已收录，类别 `official` |
| KARDS Open XV、XVI（2023） | Challonge | ✅ 已收录，类别 `open` |
| Pauper II | Challonge | 已抓取，类别为 `community`，默认不计入 |

`data/challonge_events.csv` 是 kards_esports 账号下的全部 139 个 Challonge 对阵表。

共 77 站、6927 场计分对局（Battlefy + start.gg 3866 场，Challonge 3061 场）；算上社区赛共 7655 场有效对局。
轮空、弃权/取消资格、双败、未录入结果的对局不计入；Challonge 上还会排除 `BYE`/`CPU` 等占位选手，
以及记成 0-0 的不战而胜。

## 模型

每站比赛结束后，用**截至当天**的全部对局拟合一次：

- P(i 胜 j) = σ(β_i − β_j)，一个系列赛（Bo3/Bo5）算一场；`--games` 改成按小局计
- 时间衰减：d 天前的对局权重为 0.5^(d / 365)
- 先验：β ~ N(0, 0.8²)，防止场次少的选手分数爆表
- ± 是拉普拉斯近似（逆 Hessian）给出的 1 个标准误
- BT 分 = 1500 + β × 400 / ln 10

半衰期和先验由 `evaluate.py` 挑出：用每站赛前的分数预测该站胜负，
样本外 log loss 0.677（抛硬币为 0.693），准确率约 57%。
（加入全部 Challonge 赛事后，网格最优是半衰期 365 天、先验 0.6，log loss 0.674；
默认的 0.8 只差 0.002，在误差范围内，所以保留默认。想用最优值就加 `--prior-sd 0.6`。）

## 文件

- `data/raw/` 平台原始数据（JSON）
- `data/matches.csv` 规整后的对局表；`valid=1` 的才参与计算，`category` 为 `open` / `open_special` / `official` / `community`
- `data/players.csv` 选手身份表：同一人在不同平台的账号按游戏内 ID 合并
- `data/aliases.csv`：`alias,canonical` 两列，手动把两个名字指向同一人（目前 9 条，都是 Challonge 名字的拼写变体，例如 `[CN]`、`·`、下划线、字母颠倒）。
- `data/overrides.csv`（可选）：`event,player,actual,note`，把某一站里某个账号的对局改记到实际上场的人名下（代打）
- `data/manual_matches.csv`：只在官方新闻里公布的结果（2021–2023 世界赛前 4 名线下总决赛，共 18 场），按已有账号录入，每行附出处
- `data/match_timeline.csv`（`python3 timeline.py` 生成，不到 1 秒）：原始数据里每一场对局的赛制、轮次、DQ 标记、比分、开放/进行/完成时间、用时与同轮中位数、批量录入数量、各自上一场的间隔。用来判断一场结果是不是真打的。注意 Challonge 的 `inactive` 只表示已结束比赛，不代表 DQ
  Challonge 名字里的 `#1234` 和结尾的括号备注（`Jking7 (CA)`、`老虎不发猫 (Tiger)`）会自动去掉再合并；括号里的昵称不参与合并
- `data/ratings_timeline.csv` 每站之后每位选手的分数、标准误、累计场次

## 补上官方赛事

官方赛事在 Challonge 上（例如 WC 2023 淘汰赛 `challonge.com/iwu8v1m9`）。

1. 在 challonge.com 注册并验证邮箱，到 <https://challonge.com/settings/developer> 生成 API v1 key
   （找不到的话，新版开发者门户在 <https://connect.challonge.com>）
2. 把 key 存成环境变量 `CHALLONGE_API_KEY`，不要写进代码或提交到仓库
3. 在 `data/challonge_events.csv` 里每行填一个对阵表：`url,title,category,event,stage`，`category` 填 `official`；
   `event`、`stage` 留空即可，`normalize.py` 会按标题自动归并（例如同月 OCC 的资格赛 A/B + Top 8 合成 "OCC 2022-11"）
4. 运行 `scrapers/challonge.py`，再依次跑 `normalize.py`、`bt.py`、`build_site.py`

每个赛事只用 1 次 API 请求，已下载的会跳过。免费账号每月限 500 次。

下载时 `scrapers/challonge.py` 会去掉报名表答案、邮箱哈希等个人信息字段，用邮箱当名字的选手改成 `Player <id>`；
在这之前下载的文件可以用 `python3 scrapers/challonge.py --scrub` 重新清理（不需要 API key）。
