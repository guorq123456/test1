# 第 3 期：特殊期（职业联赛战队卡组）

写于 2026-11-24（主持方，按 Salem 的裁定 S27）。这一期的规定优先于 rules.md、submit.md 里卡组期的一般写法；没写到的照一般写法。

## 一、这一期做什么

- 这一期是**卡组期**，但新卡组只能来自一处：职业联赛 Premier Series 26-27 **第 11 节后半（11/18 JST）**的四个队。你挑**一个队**，交这个队**七个职业的七副卡表**，每副 40 张**一张不改**（卡组代码照抄下面第四节或 decklists.md「第 11 节后半」一节；同样 40 张、顺序不同的代码也算）。
- 打法**你自己写**。这一期最想看的是：同一副职业选手的卡表，你能不能把它打好。
- 挑哪个队由你自己判断。

## 二、怎么交

1. **先交「选队」**。一个提交目录，里面只要 `submission.json`（别的文件不用放）：

   ```json
   {"type": "选队", "team": "Crazy Raccoon"}
   ```

   `team` 照抄第四节的队名（四个之一）。主持方收提交时按收到的顺序处理，先到先得：
   - 每队最多 2 个选手。
   - 同一张卡表池子里最多 2 个成员（rules.md 的老规矩）。有的卡表两个队都用（レバンガ北海道和 REJECT 的精灵是同一张），有的卡表池子里可能已经有成员用着，所以有的队可能 1 个人选了就满。
   - 选得上的条件是：这个队七张卡表，算上已经有的成员和已经选了带同一张卡表的队的选手，每张都还放得下你。所以一旦选上，你那七副一定放得进池子。
   - 选不上，回执会写是哪个职业的卡表放不下，换一个队再交「选队」。
   - **选上了不能换，一期只选一次**。所以先想清楚再交，交得早，选择余地大。
2. **选上以后，七个职业各交一副「新卡组」**，格式和平时一样（submit.md 第一节），`deck` 就是你那个队这个职业的卡表。不是你那个队的、改过牌的，都拒收。七个职业都要交（S5）。
3. 其余照常：回执、`receipts\状态.md`（会写你选的是哪个队）、截止时刻、收提交排队。

## 三、怎么评

- 这些成员和平时卡组期的新卡组一样入池，打天梯、算 CR，以后的策略期可以改打法。
- 另外，第 3 期收尾以后，主持方在冻结的池子上给每个选手的这七个成员各评一次（评估器的验收口径：5 个重复，每个 1200 局），同时用同样的方法评七个基线成员。拿你的成员和**同职业的基线成员**比相对 CR：
  - **过关**：比基线强（差值的 95% 区间整个在 0 以上）。
  - **良好**：比基线高 200 以上。
- 评测要跑好几个小时，结果放进你自己的 `receipts\`。

## 四、四个队的卡表

### MURASH GAMING

| 职业 | decklists.md 里的名字 | 卡组代码 |
|---|---|---|
| 精灵 | ps11b/FOREST-MRG-Spicies | `1.1.e4Gg.e4Gg.e4Gg.e6x8.e6x8.e6x8.eVLe.eVLe.eVLe.etGk.etGk.etGk.etl-.etl-.etl-.etm8.fFRw.fFRw.fFRw.fGAU.fGAU.fGAU.fGAe.fds6.fds6.fds6.fe5k.fe5k.fe5k.feLM.feLM.feLM.feOU.feOU.feOU.fea-.fea-.fea-.fzqM.fzqM` |
| 皇家护卫 | ps11b/SWORD-MRG-Toby | `1.2.cEZs.cEZs.cEZs.eXnk.eXnk.eXnk.eXnu.eXnu.eXnu.evi-.evi-.evi-.ewCE.ewCE.ewCE.ewCO.ewCO.ewCO.fDkE.fIck.fIck.fIck.fIcu.f-LA.f-LA.g2is.g2is.g2is.g2yU.g2yU.g2yU.g3C6.g3C6.g3C6.g3FE.g3FE.g3FE.g3Rk.g3Rk.g3Rk` |
| 巫师 | ps11b/RUNE-MRG-Toby | `1.3.cH3E.cH3E.eB7k.eB7k.eB7k.eBKO.eBKO.eBKO.eBpe.eBpe.eBpe.fDXk.fDXk.fKK6.fKK6.fKNE.fKNE.fKNE.fKZk.fKZk.fKZk.fKcs.fKcs.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-.fL2-.fL2-.fL38.fL38.fL38.fink.fink.fink.fjTe.fjTe` |
| 龙族 | ps11b/DRAGON-MRG-Spicies | `1.4.e3ls.e3ls.e3ls.ebxM.ebxM.ebxM.e-M0.fDE-.fDE-.fDXk.fDXk.fDXk.flAs.flAs.flAs.flD-.flD-.flD-.flQU.flQU.flQU.flg6.flg6.flg6.fljE.fljE.fljE.flvk.flvk.flvk.g7bM.g7bM.g7bM.g7r8.g7r8.g7r8.g87k.g8KO.g8KO.g8KO` |
| 梦魇 | ps11b/ABYSS-MRG-glory | `1.5.eFzG.eFzG.f0oG.f0oG.f0oG.f11k.f11k.f11k.f1KU.f1KU.f1KU.f1W-.f1W-.f1W-.f1X8.f1X8.f1X8.fPCm.fPCm.fPCm.fPxU.fndG.fndG.fndG.fnsk.fnsk.fnsk.foL-.foL-.foL-.foM8.foM8.foM8.f-3-.f-3-.gAmU.gAmU.gAme.gAme.gAme` |
| 主教 | ps11b/HAVEN-MRG-glory | `1.6.cOMQ.cOMQ.cOMQ.cOc2.cOc2.cOc2.fRes.fRes.fRes.fRf0.fRf0.fS86.fS86.fS86.fSNu.fSNu.fSNu.fqJ8.fqJ8.fqJ8.fzqM.fzqM.fzqM.f-3-.f-3-.gCTs.gCjU.gCjU.gCmc.gCmc.gCmc.gCz6.gCz6.gCz6.gD0E.gD0E.gD0E.gDCk.gDCk.gDCk` |
| 超越者 | ps11b/PORTAL-MRG-glory | `1.7.cR2I.cR2I.cR2I.eLN-.eLN-.eLae.eLae.eShA.er5g.er5g.fDkE.fUp-.fUp-.ftEe.ftEe.ftEe.fzqM.f-LA.f-LA.f-LA.gEw6.gEw6.gEw6.gF9k.gF9k.gF9k.gFCs.gFCs.gFPM.gFPM.gFPM.gFSU.gFSU.gFSU.gFe-.gFe-.gFe-.gFf8.gFf8.gFf8` |

### レバンガ北海道

| 职业 | decklists.md 里的名字 | 卡组代码 |
|---|---|---|
| 精灵 | ps11b/FOREST-LVH-Era53 | `1.1.e4Gg.e4Gg.e4Gg.e6x8.e6x8.e6x8.eUsO.eVLe.eVLe.eVLe.etGk.etGk.etGk.etl-.etl-.etl-.etm8.fFRw.fFRw.fFRw.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.feLM.feLM.feLM.feOU.feOU.feOU.fea-.fea-.fea-.fzqM.fzqM` |
| 皇家护卫 | ps11b/SWORD-LVH-Era53 | `1.2.cEZs.cEZs.cEZs.eXnk.eXnk.eXnu.eXnu.evi-.evi-.evi-.evyc.ewCE.ewCE.ewCE.ewCO.ewCO.ewCO.fIck.fIck.fIck.fIcu.fIcu.f-LA.f-LA.f-LA.g2is.g2is.g2is.g2yU.g2yU.g2yU.g3C6.g3C6.g3C6.g3FE.g3FE.g3FE.g3Rk.g3Rk.g3Rk` |
| 巫师 | ps11b/RUNE-LVH-rikka | `1.3.cH3E.cH3E.cH3E.cfTu.cfTu.cfTu.e4Gg.e4Gg.e4Gg.fDXk.fDXk.fDXk.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-.fL2-.fL2-.fikc.fikc.fikc.fink.fi-E.fi-E.fi-E.fj1M.fj1M.fj1M.fjDs.fjDs.fjDs.fjG-.fjG-.fjG-.fjTU.fjTU.fjTU` |
| 龙族 | ps11b/DRAGON-LVH-Era53 | `1.4.cJl6.cJl6.cJl6.e4IE.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.e_4k.e_4k.e_4k.fDkE.fDkE.fDkE.fNVO.fNVO.fNVO.flvu.flvu.flvu.fzqM.fzqM.fzqM.f-3-.f-3-.g7bM.g7bM.g7bM.g84c.g84c.g84c.g8KE.g8KE` |
| 梦魇 | ps11b/ABYSS-LVH-だーよね | `1.5.eFzG.eFzG.f0oG.f0oG.f0oG.f11k.f11k.f11k.f1KU.f1KU.f1W-.f1W-.f1W-.f1X8.f1X8.f1X8.fPCm.fPCm.fPxe.fndG.fndG.fndG.fnsk.fnsk.fnsk.foL-.foL-.foL-.foM8.foM8.foM8.f-3-.f-3-.f-3-.gAmU.gAmU.gAmU.gAme.gAme.gAme` |
| 主教 | ps11b/HAVEN-LVH-rikka | `1.6.cOMQ.cOMQ.cOc2.cOc2.cOc2.fRes.fRes.fRes.fRf0.fRf0.fS86.fS86.fS86.fS9g.fSNu.fSNu.fSNu.fqJ8.fqJ8.fqJ8.fzqM.fzqM.fzqM.f-3-.f-3-.gCjU.gCjU.gCjU.gCmc.gCmc.gCmc.gCz6.gCz6.gCz6.gD0E.gD0E.gD0E.gDCk.gDCk.gDCk` |
| 超越者 | ps11b/PORTAL-LVH-だーよね | `1.7.cR2I.cR2I.cR2I.eLN-.eLN-.eLae.eShA.er5g.er5g.er5g.fDkE.fUp-.fUp-.ftEe.ftEe.ftEe.fzqM.f-LA.f-LA.f-LA.gEw6.gEw6.gEw6.gF9k.gF9k.gF9k.gFCs.gFCs.gFPM.gFPM.gFPM.gFSU.gFSU.gFSU.gFe-.gFe-.gFe-.gFf8.gFf8.gFf8` |

### REJECT

| 职业 | decklists.md 里的名字 | 卡组代码 |
|---|---|---|
| 精灵 | ps11b/FOREST-RC-あぐのむ | `1.1.e4Gg.e4Gg.e4Gg.e6x8.e6x8.e6x8.eUsO.eVLe.eVLe.eVLe.etGk.etGk.etGk.etl-.etl-.etl-.etm8.fFRw.fFRw.fFRw.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.feLM.feLM.feLM.feOU.feOU.feOU.fea-.fea-.fea-.fzqM.fzqM` |
| 皇家护卫 | ps11b/SWORD-RC-たばた | `1.2.cEZs.cEZs.cEZs.eXnk.eXnk.eXnk.eXnu.evi-.evi-.evi-.ewCE.ewCE.ewCE.ewCO.ewCO.ewCO.fDkE.fIck.fIck.fIck.fIcu.fh1O.f-LA.f-LA.f-LA.g2is.g2is.g2is.g2yU.g2yU.g2yU.g3C6.g3C6.g3C6.g3FE.g3FE.g3FE.g3Rk.g3Rk.g3Rk` |
| 巫师 | ps11b/RUNE-RC-拓海 | `1.3.eB7k.eB7k.eB7k.eBKO.eBKO.eBKO.eBpe.eBpe.eBpe.fDXk.fKK6.fKK6.fKK6.fKNE.fKNE.fKNE.fKZk.fKZk.fKZk.fKcs.fKcs.fKcs.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.fL2-.fL2-.fL2-.fL38.fL38.fL38.fink.fink.fink.fjTe.fjTe.fjTe` |
| 龙族 | ps11b/DRAGON-RC-たばた | `1.4.cJl6.cJl6.cJl6.e4IE.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-uE.e_4k.e_4k.e_4k.fDkE.fDkE.fNVO.fNVO.fNVO.flvu.flvu.flvu.fzqM.fzqM.fzqM.f-3-.f-3-.f-3-.g7bM.g7bM.g84c.g84c.g84c.g8KE` |
| 梦魇 | ps11b/ABYSS-RC-たばた | `1.5.cM8E.cM8E.e3ls.e3ls.f0oG.f0oG.f11k.f11k.f11k.f1KU.f1KU.f1W-.f1W-.f1W-.f1X8.f1X8.f1X8.fPCm.fPCm.fPCm.fndG.fndG.fndG.fnsk.fnsk.foL-.foL-.foL-.foM8.foM8.foM8.f-3-.f-3-.f-3-.gA1c.gAmU.gAmU.gAme.gAme.gAme` |
| 主教 | ps11b/HAVEN-RC-拓海 | `1.6.cOMQ.cOMQ.cOMQ.cOc2.cOc2.cOc2.fRes.fRes.fRes.fRf0.fRf0.fS86.fS86.fS86.fSNu.fSNu.fSNu.fqJ8.fqJ8.fqJ8.fzqM.fzqM.f-3-.f-3-.f-3-.gCTs.gCjU.gCjU.gCmc.gCmc.gCmc.gCz6.gCz6.gCz6.gD0E.gD0E.gD0E.gDCk.gDCk.gDCk` |
| 超越者 | ps11b/PORTAL-RC-あぐのむ | `1.7.cR2I.cR2I.eLN-.eLN-.eLN-.eLae.eLae.er5g.er5g.fDkE.fUp-.fUp-.ftEe.ftEe.ftEe.fzqM.fzqM.f-LA.f-LA.f-LA.gEw6.gEw6.gEw6.gF9k.gF9k.gF9k.gFCs.gFCs.gFPM.gFPM.gFPM.gFSU.gFSU.gFSU.gFe-.gFe-.gFe-.gFf8.gFf8.gFf8` |

### Crazy Raccoon

| 职业 | decklists.md 里的名字 | 卡组代码 |
|---|---|---|
| 精灵 | ps11b/FOREST-CR-空白 | `1.1.e4Gg.e4Gg.e4Gg.e6x8.e6x8.e6x8.eVLe.eVLe.eVLe.etGk.etGk.etGk.etl-.etl-.etl-.etm8.fFRw.fFRw.fFRw.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.feLM.feLM.feLM.feOU.feOU.feOU.fea-.fea-.fea-.fzqM.fzqM.fzqM` |
| 皇家护卫 | ps11b/SWORD-CR-ふえた | `1.2.cEZs.cEZs.cEZs.e9Ak.e9Ak.e9Ak.e9NO.e9NO.eXnu.eXnu.eXnu.evi-.evi-.evi-.fIQE.fIQE.fIQE.fIcu.fIcu.fgIM.fgIM.fgIM.fgX-.fgX-.fgX-.fgb6.fgb6.fgnc.fgnc.fgnc.fgqk.fgqk.fgqk.fh1E.fh1E.fh1E.fh1O.g3Ru.g3Ru.g3Ru` |
| 巫师 | ps11b/RUNE-CR-Atom | `1.3.cH1g.cH1g.cH1g.cH3E.cfTu.cfTu.cfTu.eBpe.eBpe.eBpe.ey9E.ey9E.ey9E.eyCM.eyCM.eyCM.fKcs.fKcs.fKcs.fKpM.fKpM.fKpM.fKsU.fKsU.fKsU.g5Ok.g5Ok.g5Ok.g5Rs.g5Rs.g5Rs.g5hU.g5hU.g5hU.g5t-.g5t-.g5t-.g5u8.g5u8.g5u8` |
| 龙族 | ps11b/DRAGON-CR-ふえた | `1.4.e3ls.e3ls.e3ls.ebxM.ebxM.ebxM.e-M0.e-M0.fDE-.fDE-.fDXk.fDXk.fDXk.flAs.flAs.flAs.flD-.flD-.flD-.flQU.flQU.flQU.flg6.flg6.flg6.fljE.fljE.fljE.flvk.flvk.flvk.g7bM.g7bM.g7bM.g7r8.g7r8.g7r8.g8KO.g8KO.g8KO` |
| 梦魇 | ps11b/ABYSS-CR-空白 | `1.5.eFzG.f0oG.f0oG.f0oG.f11k.f11k.f11k.f1KU.f1KU.f1W-.f1W-.f1W-.f1X8.f1X8.f1X8.fPCm.fPCm.fPCm.fPxU.fndG.fndG.fndG.fnsk.fnsk.fnsk.foL-.foL-.foL-.foM8.foM8.foM8.f-3-.f-3-.f-3-.gAmU.gAmU.gAmU.gAme.gAme.gAme` |
| 主教 | ps11b/HAVEN-CR-Atom | `1.6.cOMQ.cOMQ.cOc2.cOc2.cOc2.fRes.fRes.fRes.fRf0.fRf0.fS86.fS86.fS86.fSNu.fSNu.fSNu.fqJ8.fqJ8.fqJ8.fzqM.fzqM.fzqM.f-3-.f-3-.f-3-.gCTs.gCjU.gCjU.gCmc.gCmc.gCmc.gCz6.gCz6.gCz6.gD0E.gD0E.gD0E.gDCk.gDCk.gDCk` |
| 超越者 | ps11b/PORTAL-CR-ふえた | `1.7.cR2I.cR2I.cR2I.eLN-.eLN-.eLN-.er5g.er5g.fDkE.fUp-.ftEe.ftEe.ftEe.fzqM.fzqM.fzqM.f-3-.f-LA.f-LA.f-LA.gEw6.gEw6.gEw6.gF9k.gF9k.gF9k.gFCs.gFCs.gFPM.gFPM.gFPM.gFSU.gFSU.gFSU.gFe-.gFe-.gFe-.gFf8.gFf8.gFf8` |
卡表来源：shadowverse-vision.com/decks（汇总官方卡表文章），2026-11-24 抓取。每副的卡名（中文）在 decklists.md「职业联赛 26-27 第 11 节后半」一节。

## 五、建议（不是规定）

- 先自己推理这副卡表怎么运转：它靠什么赢，关键牌在第几回合、什么条件下打出去，对不同职业先手后手怎么打，换牌留什么，什么时候转去打脸、什么时候先解场。把推出来的东西挑最关键的几处手写进打法，比如换牌、关键牌的时机、要留着的资源、斩杀判断，再在练习场里用同一批局（`--same-as`）和默认打法比，确认真的更好。
- 七个职业未必都有时间深挖，先做你最有把握的几个；其余的用默认打法交也合格，只是不一定过得了关。
- 时间：这一期工作时间 12 小时，练习场每人最多 6 万局。
