"""Aggregate ruler-league rows by archetype. usage: agg_ruler.py RULER.jsonl LABELS.tsv"""
import json, sys, math
from collections import defaultdict
rows=[json.loads(t) for t in open(sys.argv[1],encoding='utf-8') if t.strip()]
arch={}
for line in open(sys.argv[2],encoding='utf-8'):
    f=line.rstrip('\n').split('\t'); arch[f[0]]=f[5]
BOT=['bot/T1-SWORD-1','bot/T1-PORTAL-1','bot/T1-ABYSS-1','bot/T1-HAVEN-1','bot/T1-FOREST-1','bot/T3-DRAGON-1','bot/T3-RUNE-1']
BN={'bot/T1-SWORD-1':'皇家护卫','bot/T1-PORTAL-1':'超越者','bot/T1-ABYSS-1':'梦魇','bot/T1-HAVEN-1':'主教','bot/T1-FOREST-1':'精灵','bot/T3-DRAGON-1':'龙族','bot/T3-RUNE-1':'巫师'}
by=defaultdict(lambda: defaultdict(list)); per=defaultdict(list)
for r in rows:
    a=arch.get(r['ref'],r['ref']); by[a][r['opp']].append(r['score']); per[r['ref']].append(r['score'])
def ms(v):
    m=sum(v)/len(v); se=math.sqrt(sum((x-m)**2 for x in v)/max(1,len(v)-1)/len(v)); return 100*m,196*se
print("| 套路（副数） | " + " | ".join(f"对 bot {BN[b]}" for b in BOT) + " | 全部 ±95% | 局数 |")
print("|---|"+"---|"*(len(BOT)+2))
order=sorted(by, key=lambda a:-len({r['ref'] for r in rows if arch.get(r['ref'],r['ref'])==a}))
for a in order:
    n=len({r['ref'] for r in rows if arch.get(r['ref'],r['ref'])==a})
    cells=[]; every=[]
    for b in BOT:
        v=by[a][b]; cells.append(f"{100*sum(v)/len(v):.0f}" if v else "-"); every+=v
    m,e=ms(every)
    print(f"| {a}（{n}） | " + " | ".join(cells) + f" | {m:.1f} ± {e:.1f} | {2*len(every)} |")
print()
print("每副（全部 7 个对手平均）：")
for ref,v in sorted(per.items(), key=lambda x:-sum(x[1])/len(x[1])):
    m,e=ms(v); print(f"  {ref:34s} {arch.get(ref,'?'):14s} {m:5.1f} ± {e:4.1f}")
