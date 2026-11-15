"""Tournament lists against the bot's 7 frozen decks, both sides the hand-set cheap bot (mcts:100+plan) = the deck
search's own ruler. Evaluation only; external lists never enter search/self-play/training.
usage: python ruler_league.py REF.txt --out X.jsonl [--deals 6] [--workers 4] [--spec mcts:100+plan] [--opp-spec ...] [--report]
Seeds: BASE + (ref index * 7 + bot index) * 10 + k.  BASE 87210000 (this thread's bank, 2026-11-15).
Condition: 对手卡表已知（牌序、手牌未知）.
"""
import argparse, json, math, sys
from multiprocessing import Pool
from pathlib import Path
from pathlib import Path as _P
ROOT = str(_P(__file__).resolve().parents[5])
sys.path.insert(0, ROOT)
from svsim.tools import deckbuild as DB
BOT = ROOT + '/analysis/pilot/fields/bot-frozen7.txt'
BASE = 87210000
CL = {1:"精灵",2:"皇家护卫",3:"巫师",4:"龙族",5:"梦魇",6:"主教",7:"超越者"}
def craft(ids):
    from svsim.cards.pool import POOL
    return int(DB.craft_of_ids(ids))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('ref'); ap.add_argument('--out', required=True)
    ap.add_argument('--deals', type=int, default=6); ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--spec', default='mcts:100+plan'); ap.add_argument('--report', action='store_true')
    ap.add_argument('--base', type=int, default=BASE); ap.add_argument('--limit', type=int, default=0)
    a=ap.parse_args()
    ref=DB.read_seeds(a.ref); bot=DB.read_seeds(BOT)
    out=Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    rows=[json.loads(t) for t in out.read_text().splitlines() if t.strip()] if out.exists() else []
    if a.report:
        by={}
        for r in rows: by.setdefault(r['ref'],{}).setdefault(r['opp'],[]).append(r['score'])
        print(f"条件：对手卡表已知（牌序、手牌未知）；两边都是 {a.spec}；每对 {a.deals} 个发牌、两个座位")
        print(f"{'参照卡组':28s} " + " ".join(f"{l.split('/')[-1][:9]:>9}" for l,_ in bot) + "     全部")
        for rl,_ in ref:
            d=by.get(rl,{}); cells=[]; every=[]
            for ol,_ in bot:
                v=d.get(ol,[]); cells.append(100*sum(v)/len(v) if v else float('nan')); every+=v
            if not every: continue
            m=sum(every)/len(every); se=math.sqrt(sum((x-m)**2 for x in every)/max(1,len(every)-1)/len(every))
            print(f"{rl:28s} " + " ".join(f"{c:9.1f}" for c in cells) + f"   {100*m:5.1f} ± {196*se:4.1f}  (n={len(every)})")
        return
    done={(r['ref'],r['opp'],r['seed']) for r in rows}
    jobs=[]
    for k in range(a.deals):
        for i,(rl,rids) in enumerate(ref):
            for j,(ol,oids) in enumerate(bot):
                s=a.base+(i*len(bot)+j)*10+k
                if (rl,ol,s) not in done: jobs.append(((rl,ol),rids,oids,s,a.spec))
    if a.limit: jobs=jobs[:a.limit]
    print(f"{len(done)} done, {len(jobs)} to play", flush=True)
    import time; t0=time.time()
    with out.open('a') as fh, Pool(a.workers, initializer=DB._nice) as pool:
        for n,res in enumerate(pool.imap_unordered(DB.play_deal, jobs, chunksize=2),1):
            rl,ol=res['key']
            fh.write(json.dumps({'ref':rl,'opp':ol,'seed':res['seed'],'spec':a.spec,'points':res['points'],'score':sum(res['points'])/2}, ensure_ascii=False)+'\n'); fh.flush()
            if n%100==0: print(f"{n}/{len(jobs)} {time.time()-t0:.0f}s", flush=True)
    print(f"done {time.time()-t0:.0f}s")
main()
