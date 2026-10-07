import sys, glob, re
from collections import Counter
sys.path.insert(0, sys.argv[1])
from svsim.cards import library, decks, deckcode
from svsim.cards.pool import POOL
V='/mnt/project-files/shadowverse/meta-research-2026-10-07/v2/'
G={}
for line in open('/mnt/project-files/shadowverse/card-glossary.md'):
    if not line.startswith('| **'): continue
    cols=[c.strip() for c in line.strip().strip('|').split('|')]
    if len(cols)<4: continue
    G[cols[3]]=(cols[0].strip('*'), cols[1])
def label(i):
    c=POOL[i]; g=G.get(c.name)
    if g: return f"{g[0]}（{g[1]}）"
    st=f"{c.cost}费 {c.attack}/{c.defense}" if hasattr(c,'attack') else f"{c.cost}费"
    return f"{c.name}（{st}，无常用名）"
def load(archs):
    out=[]
    for line in open(V+'jcs.txt'):
        line=line.strip()
        if '|' not in line: continue
        player,grp,arch,h=line.split('|',3)
        if arch in archs: out.append(('JCS '+player, h))
    for f in glob.glob(V+'ps/in_*.txt'):
        arch=re.sub(r'.*/in_(.*)\.txt',r'\1',f)
        if arch not in archs: continue
        for line in open(f):
            if '|' not in line: continue
            src,h=line.strip().rsplit('|',1)
            if src.startswith('G8'): continue
            out.append((src, h.split('hash=')[-1].split('&')[0]))
    return out
out=[]
out.append("# 比赛卡表 → 模拟器导入清单（2026-10-07）\n")
out.append("来源：JCS 第 3 赛季 24 套 + 职业联赛（第 7 节后半、第 8 节前后半）卡表，官方哈希解码（meta-research-2026-10-07/v2/）。每套取“比赛卡表里出现次数最多的那一张完整 40 张”为标准版，哈希可直接喂给 `decks.from_hash`。牌名用对照表的常用名（费用身材）。\n")
out.append("覆盖检查（builder 分支 3d9e49f，`decks.unimplemented`）：144 套比赛卡表里 142 套的 40 张全部有脚本；唯二没有脚本的卡是 Galmieux, Ardor Manifest 和 Gilnelise, Voracity Manifest，只出现在 drag58 变体（非比赛主流）。所以缺的不是卡牌脚本，而是：卡组登记、组合回合的搜索支持、关键卡脚本的正确性核对、按对局的评估器。\n")
spec=[('连击妖（elf-t）',['elf'],decks.COMBO_FOREST),('机锋 / 宇宙鱼（nemesis-t）',['cut'],None),('跳费龙比赛版（ramp-t）',['dragon','ramp'],decks.RAMP_DRAGON),('旗皇比赛版（pirate-t）',['pirate'],decks.PIRATE_SWORD)]
for title,archs,builtin in spec:
    lists=load(archs)
    cnts=[(s,Counter(deckcode.decode_deck(h)[2]),h) for s,h in lists]
    key,n=Counter(tuple(sorted(c.items())) for _,c,_ in cnts).most_common(1)[0]
    std=Counter(dict(key))
    srcs=[s for s,c,_ in cnts if tuple(sorted(c.items()))==key]
    fmt,craft,ids=deckcode.decode_deck(cnts[0][2])
    h=deckcode.encode_deck(fmt,craft,sorted(std.elements()))
    out.append(f"\n## {title}\n")
    out.append(f"{len(lists)} 套比赛卡表；标准版 = {n} 套完全相同（{', '.join(srcs)}）。\n")
    out.append(f"哈希：`{h}`\n")
    out.append("标准版 40 张：\n")
    for i,k in sorted(std.items(), key=lambda x:(POOL[x[0]].cost,x[0])):
        out.append(f"- {k}× {label(i)}")
    allids=set().union(*[set(c) for _,c,_ in cnts])
    fixed={i for i in allids if all(c[i]==cnts[0][1][i] for _,c,_ in cnts)}
    free=sorted(allids-fixed, key=lambda i:POOL[i].cost)
    out.append(f"\n固定 {sum(cnts[0][1][i] for i in fixed)} 张，自由位（比赛卡表里的张数范围）：" + "；".join(f"{label(i)} {min(c[i] for _,c,_ in cnts)}–{max(c[i] for _,c,_ in cnts)}" for i in free) + "\n")
    if builtin:
        b=Counter({c.card_id:k for c,k in builtin.items()})
        plus={i:std[i]-b[i] for i in set(std)|set(b) if std[i]>b[i]}
        minus={i:b[i]-std[i] for i in set(std)|set(b) if b[i]>std[i]}
        out.append("与模拟器现有版本（Game8）的差别：比赛版多 " + "、".join(f"{label(i)} +{k}" for i,k in plus.items()) + "；少 " + "、".join(f"{label(i)} −{k}" for i,k in minus.items()) + "\n")
open('tournament-decks-2026-10-07.md','w').write('\n'.join(out))
print('\n'.join(out)[:6000])
