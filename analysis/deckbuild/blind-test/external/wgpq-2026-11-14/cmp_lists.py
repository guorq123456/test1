"""Compare external tournament lists with the bot's frozen decks.
usage: python cmp_lists.py REF.txt [--bot BOTFILE] [--glossary G.md] [--dump]
REF lines: label|hash  (label contains class name e.g. FOREST)
"""
import sys, re, argparse
from collections import Counter, defaultdict
from pathlib import Path as _P
ROOT = str(_P(__file__).resolve().parents[5])
sys.path.insert(0, ROOT)
from svsim.cards import library  # noqa
from svsim.cards.pool import POOL
from svsim.cards import deckcode

CLASSES = ("FOREST","SWORD","RUNE","DRAGON","ABYSS","HAVEN","PORTAL")
ZH = dict(zip(CLASSES, ("精灵","皇家护卫","巫师","龙族","梦魇","主教","超越者")))
JP2C = {"エルフ":"FOREST","ロイヤル":"SWORD","ウィッチ":"RUNE","ドラゴン":"DRAGON","ナイトメア":"ABYSS","ビショップ":"HAVEN","ネメシス":"PORTAL"}
CRAFT2C = {1:"FOREST",2:"SWORD",3:"RUNE",4:"DRAGON",5:"ABYSS",6:"HAVEN",7:"PORTAL"}

def read(path):
    out=[]
    for line in open(path, encoding='utf-8'):
        line=line.strip()
        if not line or line.startswith('#'): continue
        parts=line.split('|')
        label, h = parts[0].strip(), parts[1].strip()
        f,c,ids = deckcode.decode_deck(h)
        out.append((label, c, ids, h))
    return out

def load_glossary(path):
    m={}
    if not path: return m
    for line in open(path, encoding='utf-8'):
        if not line.startswith('|') or '---' in line: continue
        cells=[x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells)<3 or cells[0]=='常用名': continue
        common=cells[0].strip('*'); full=cells[2]
        if full and full!=common: m[full]=common
    return m

def names(ids): return Counter(POOL[i].name for i in ids)
def overlap(a,b): return sum(min(a[k],b[k]) for k in a)
def new10(ids): return sum(POOL[i].card_set==10010 for i in ids)

def show(ids, gl):
    cnt=Counter(ids)
    rows=[]
    for i,n in sorted(cnt.items(), key=lambda x:(POOL[x[0]].cost, x[0])):
        c=POOL[i]; zh=c.name_zh; short=gl.get(zh, zh.split('·')[-1] if '·' in zh else zh)
        tag='【新】' if c.card_set==10010 else ''
        rows.append(f"{n}× {short}（{c.cost}费{'' if c.atk is None else f' {c.atk}/{c.life}'}，{c.name}）{tag}")
    return rows

def clusters(decks, thr=25):
    groups=[[d] for d in decks]; merged=True
    while merged:
        merged=False
        for i in range(len(groups)):
            for j in range(i+1,len(groups)):
                if any(overlap(names(a[2]),names(b[2]))>=thr for a in groups[i] for b in groups[j]):
                    groups[i]+=groups.pop(j); merged=True; break
            if merged: break
    return sorted(groups,key=len,reverse=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('ref'); ap.add_argument('--bot', default=ROOT + '/svsim/ui/bot_decks.txt')
    ap.add_argument('--glossary', default=ROOT + '/analysis/card-glossary.md'); ap.add_argument('--dump', action='store_true')
    a=ap.parse_args()
    gl=load_glossary(a.glossary)
    ref=read(a.ref)
    bot=[(l,c,ids,h) for l,c,ids,h in read(a.bot)]
    bad=[(l,len(ids)) for l,c,ids,h in ref if len(ids)!=40 or any(i not in POOL for i in ids)]
    print(f"参照 {len(ref)} 副；不合法/不满 40 张：{bad}")
    byc=defaultdict(list)
    for d in ref: byc[CRAFT2C[d[1]]].append(d)
    print("\n== 每职业副数、平均新卡、分堆（两副共有 ≥25 张算一堆）")
    for c in CLASSES:
        ds=byc.get(c,[])
        if not ds: print(f"{ZH[c]}: 0"); continue
        cl=clusters(ds)
        print(f"{ZH[c]}: {len(ds)} 副, 平均新卡 {sum(new10(d[2]) for d in ds)/len(ds):.1f}; 堆: " + " | ".join(f"{len(k)}副[" + " ".join(d[0].split('/')[-1] for d in k) + "]" for k in cl))
        # core: cards in all decks of the largest cluster
        big=cl[0]
        core=None
        for d in big:
            n=names(d[2]); core = n if core is None else Counter({k:min(v,core[k]) for k,v in n.items() if k in core})
        print(f"   最大堆共同核心 {sum(core.values())} 张")
    print("\n== 和 bot 冻结卡组的重合（按卡名，同名按较少份数；满分 40）")
    for c in CLASSES:
        ds=byc.get(c,[]); bots=[b for b in bot if CRAFT2C[b[1]]==c]
        if not ds: continue
        for b in bots:
            ovs=[overlap(names(d[2]),names(b[2])) for d in ds]
            print(f"{ZH[c]} {b[0]:>12}: 平均 {sum(ovs)/len(ovs):4.1f}, 最大 {max(ovs)}, 最小 {min(ovs)}; bot 新卡 {new10(b[2])}, 参照新卡 {sum(new10(d[2]) for d in ds)/len(ds):.1f}")
    if a.dump:
        print("\n== 卡表明细")
        for c in CLASSES:
            for l,cc,ids,h in byc.get(c,[]):
                print(f"\n### {l}  新卡 {new10(ids)}\n" + "\n".join("- "+r for r in show(ids,gl)) + f"\n`{h}`")
main()
