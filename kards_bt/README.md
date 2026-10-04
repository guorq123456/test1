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
python3 placements.py          # 每人每站的名次 data/placements.csv（网页提示框用）
python3 build_site.py          # 生成交互页面 site/index.html
```

## 数据覆盖

| 赛事 | 平台 | 状态 |
|---|---|---|
| KARDS Open #1 – VII、Open: Singleton、Operation: Kards（2020.05 – 2021.06，983 Media） | Battlefy | 已抓取，类别 `open`，默认不计入 |
| KARDS Open VIII – XIV（2021.08 – 2022.11，983 Media） | start.gg | 已抓取，类别 `open`，默认不计入 |
| KARDS 世界赛 2021、2022（约 100 人，小组循环赛 + 双败淘汰赛；未公开列出） | start.gg | ✅ 已收录，类别 `official` |
| Weekday Skirmish、Blitz、Homebrew Brawl 等社区赛 | Battlefy / start.gg | 已抓取，类别为 `community`，默认不计入 |
| OCC 月赛 2021.05 – 2024.11（同月的资格赛 A/B + Top 8 合并成一站；2024 年 4–8 月只有 Top 8） | Challonge | ✅ 已收录，类别 `official` |
| OCC Ultimate I – III（2023，8 人邀请赛） | Challonge | ✅ 已收录，类别 `official` |
| KARDS 世界赛 2023（128 人小组赛 + 32 强双败）、2024（16 强单败；128 人瑞士轮在 Battlefy，未公开列出）、2025（16 人双败） | Challonge + Battlefy | ✅ 已收录，类别 `official` |
| 2021–2023 世界赛前 4 名线下总决赛（18 场） | 官方新闻 | ✅ 人工补录（`data/manual_matches.csv`） |
| 2025 年 4 个扩展赛（Blood & Iron、United Front、Naval Warfare、Air Supremacy，各含 Top 8） | Challonge | ✅ 已收录，类别 `official` |
| 2026 年冬、春、夏、秋季赛（各含 Top 8） | Challonge | ✅ 已收录，类别 `official` |
| KARDS Open XV、XVI（2023） | Challonge | 已抓取，类别 `open`，默认不计入 |
| Pauper II | Challonge | 已抓取，类别为 `community`，默认不计入 |

`data/challonge_events.csv` 是 kards_esports 账号下的全部 139 个 Challonge 对阵表。

默认只用官方赛事（`category=official`）：59 站、3341 场计分对局（含 18 场人工补录的总决赛）。
KARDS Open 没有报名门槛、不在电竞计划内，新人和弱选手多，单独作为噪音来源检验过（`open_exp.py`，结果在 `data/open_exp_results.txt`）：
把 Open 降权到 0.5 对官方对局的预测最好，完全去掉与不降权差不多；按项目决定完全去掉，换来只反映官方赛事的平滑走势，代价是 2021 年 5 月之前没有分数。
`python3 bt.py --categories open,open_special,official --open-weight 0.5` 可以加回 Open。

**没打的比赛不算**（`phantoms.py`，每场单独判断，整场作废、对手的胜场一起去掉）：
- 轮空和 `BYE`/`CPU` 占位选手、平台自己的判负标记（Challonge `forfeited`、start.gg `DQ`、Battlefy 双败）、0-0 的不战而胜
- Battlefy 只有一方签到、正好 10 分钟后的自动 2-0（缺席判负，平台不打标记）
- Challonge 上被主办方标 `(DQ)`/`(dropped)` 的选手：标记之后录入的 0 分负局，以及标记时被改写成 0-3 的旧结果（真实胜负已经丢失）
- start.gg 上只记胜负、没有比分的结果（WC 2022 的缺席判负写法），以及管理员几秒内批量录入的缺席选手 0 分负局（WC 2021）
- 瑞士轮里快到不可能打完、而且输家此后再也没真打过的 0 分负局

规则刻意保守：DQ 之前真打的比赛保留（Battlefy 把 DQ 标在选手最后一场，即使那场真打过，也会恢复）；
瑞士轮和循环赛不按负场数判断；**只要双方都在场、比分正常，录入再快也算真实对局**（淘汰赛常提前约战）。
清洗后有 457 场原本计分的对局作废，115 场被误删的真实对局恢复。

## 模型

每站比赛结束后、以及每月 1 日，用**截至当时**的全部对局拟合一次（月初快照让网页横轴按时间显示两站之间的衰减）：

- P(i 胜 j) = σ(β_i − β_j)，一个系列赛（Bo3/Bo5）算一场；`--games` 改成按小局计
- 时间衰减：d 天前的对局权重为 0.5^(d / 240)
- 先验：β ~ N(0, 0.6²)，防止场次少的选手分数爆表
- 天梯直邀修正（`invites.py`）：OCC 有资格赛数据的月份里，没打资格赛就进 8 强的选手是天梯直邀。直邀和资格赛胜出一样难，所以给每个直邀选手记上当月资格赛晋级者的中位战绩（对手设为晋级者在资格赛里对手的平均赛前水平），没有可调参数，日期记在 8 强开赛时。这些虚拟战绩按 120 天半衰期衰减，之后由真实比赛接替，不会让多年前的直邀撑起现在的排名。实验里它把直邀选手在 8 强被低估的程度从 +0.12 降到 +0.06，整体预测不变差（`experiments.py`）
- ± 是拉普拉斯近似（逆 Hessian）给出的 1 个标准误
- BT 分 = 1500 + β × 400 / ln 10

半衰期和先验由 `evaluate.py` 挑出：用每站赛前的分数预测该站胜负，
只用官方赛事时，3219 场样本外对局上 log loss 0.687（抛硬币为 0.693），准确率约 54%：官方赛事选手水平接近，本来就难预测。
半衰期 240 天与 365 天相同（0.6907），120 天更差（0.6921）；先验 0.4–0.6 都比 0.8 好（0.687 vs 0.691），取 0.6。
（含 Open 数据时为 0.674 / 58%，主要因为 Open 里强弱悬殊的对局容易猜。）赛事分级加权已检验：数据不支持（越重要的比赛结果反而越接近五五开），不采纳。

`bt.py` 每个 CPU 核算一段快照，并从上一站的解出发继续拟合，全量重算约 3 秒。

## 文件

- `data/raw/` 平台原始数据（JSON）
- `data/matches.csv` 规整后的对局表；`valid=1` 的才参与计算，`category` 为 `open` / `open_special` / `official` / `community`
- `data/players.csv` 选手身份表：同一人在不同平台的账号按游戏内 ID 合并
- `data/aliases.csv`：`alias,canonical` 两列，手动把两个名字指向同一人（目前 9 条，都是 Challonge 名字的拼写变体，例如 `[CN]`、`·`、下划线、字母颠倒）。
- `data/overrides.csv`（可选）：`event,player,actual,note`，把某一站里某个账号的对局改记到实际上场的人名下（代打）
- `data/manual_matches.csv`：只在官方新闻里公布的结果（2021–2023 世界赛前 4 名线下总决赛，共 18 场），按已有账号录入，每行附出处
- `data/match_timeline.csv`（`python3 timeline.py` 生成，不到 1 秒）：原始数据里每一场对局的赛制、轮次、DQ 标记、比分、开放/进行/完成时间、用时与同轮中位数、批量录入数量、各自上一场的间隔。用来判断一场结果是不是真打的。注意 Challonge 的 `inactive` 只表示已结束比赛，不代表 DQ
  Challonge 名字里的 `#1234` 和结尾的括号备注（`Jking7 (CA)`、`老虎不发猫 (Tiger)`）会自动去掉再合并；括号里的昵称不参与合并
- `data/ratings_timeline.csv` 每站之后（`event` 为空的行是月初快照）每位选手的分数、标准误、累计场次
- `data/placements.csv` 每人每站的最终名次：Challonge 用官方 final_rank，其他淘汰赛按出局轮次推算（同轮出局并列，如“第 5–8 名”），没打进淘汰赛的写阶段战绩（如“瑞士轮 4-2”）

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
