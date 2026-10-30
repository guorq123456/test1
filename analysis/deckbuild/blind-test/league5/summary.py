"""Group-level summary of a metric-5 league from its league-deals.jsonl: each group against all others, every pair of
groups, and each deck; standard errors over deck pairs (each pair's deals averaged first)."""
import json, sys, math, collections
rows=[json.loads(l) for l in open(sys.argv[1])]
G=lambda lab: lab.split('/',1)[0]
pair=collections.defaultdict(list)       # (deckA, deckB) -> scores from A's view
for r in rows:
    pair[(r['a'],r['b'])].append(r['score']); pair[(r['b'],r['a'])].append(1-r['score'])
groups=sorted({G(a) for a,_ in pair}, key=lambda g: ['bot','control','g1','g2','g3','p2-g1','p2-g2','p2-g3'].index(g))
def stat(sel):
    means=[sum(v)/len(v) for k,v in pair.items() if sel(k)]
    m=sum(means)/len(means); se=(sum((x-m)**2 for x in means)/(len(means)-1)/len(means))**.5
    return m, se, len(means)
print("每组对其他所有组：")
for g in groups:
    m,se,n=stat(lambda k: G(k[0])==g)
    print(f"  {g:7s} {100*m:5.1f} ± {100*se:.1f}")
print("两两（行对列，行方得分）：")
print("        "+" ".join(f"{g:>7s}" for g in groups))
for g in groups:
    cells=[]
    for h in groups:
        if g==h: cells.append("    -  "); continue
        m,se,n=stat(lambda k: G(k[0])==g and G(k[1])==h)
        cells.append(f"{100*m:5.1f}  ")
    print(f"{g:7s} "+" ".join(cells))
print("bot 对各组（± 按卡组对算的标准误）：")
for h in groups:
    if h=='bot': continue
    m,se,n=stat(lambda k: G(k[0])=='bot' and G(k[1])==h)
    print(f"  bot vs {h}: {100*m:.1f} ± {100*se:.1f}")
print("每组各职业那副对其他组的平均：")
for g in groups:
    out=[]
    for a in sorted({k[0] for k in pair if G(k[0])==g}):
        m,se,n=stat(lambda k: k[0]==a)
        out.append(f"{a.split('/',1)[1]} {100*m:.0f}")
    print(f"  {g}: "+"; ".join(out))
