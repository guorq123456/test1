import sys, glob, re
from collections import Counter, defaultdict
sys.path.insert(0, sys.argv[1])
from svsim.cards import library, decks, deckcode  # noqa
from svsim.cards.pool import POOL
from svsim.core.script import has_script
V='/mnt/project-files/shadowverse/meta-research-2026-10-07/v2/'
lists=[]  # (source, archetype, ids)
for line in open(V+'jcs.txt'):
    line=line.strip()
    if not line or '|' not in line: continue
    player,grp,arch,h=line.split('|',3)
    lists.append(('JCS '+player, arch, h))
for f in sorted(glob.glob(V+'ps/in_*.txt')):
    arch=re.sub(r'.*/in_(.*)\.txt',r'\1',f)
    for line in open(f):
        line=line.strip()
        if '|' not in line: continue
        src,h=line.rsplit('|',1)
        lists.append((src, arch, h.split('hash=')[-1].split('&')[0]))
print('lists', len(lists))
by_arch=defaultdict(list)
missing_pool=Counter(); unimpl=Counter(); unimpl_lists=defaultdict(set)
per_arch=defaultdict(lambda: dict(n=0, ok=0, cards=Counter(), un=Counter(), miss=Counter()))
for src,arch,h in lists:
    try:
        fmt,craft,ids=deckcode.decode_deck(h)
    except Exception as e:
        print('DECODE FAIL',src,arch,e); continue
    a=per_arch[arch]; a['n']+=1
    bad=False
    for i in set(ids):
        a['cards'][i]+=1
        c=POOL.get(i)
        if c is None:
            missing_pool[i]+=1; a['miss'][i]+=1; bad=True; continue
        if c.has_ability and not has_script(i):
            unimpl[i]+=1; a['un'][i]+=1; unimpl_lists[i].add(src); bad=True
    if not bad: a['ok']+=1
def nm(i):
    c=POOL.get(i)
    return f"{c.name}" if c else f"?{i}"
print()
print('%-14s %5s %7s %8s %8s'%('archetype','lists','playable','unimpl','notpool'))
for arch,a in sorted(per_arch.items(), key=lambda x:-x[1]['n']):
    print('%-14s %5d %7d %8d %8d'%(arch,a['n'],a['ok'],len(a['un']),len(a['miss'])))
print()
print('UNIMPLEMENTED cards across all tournament lists (count of lists containing it):')
for i,n in unimpl.most_common():
    print(f"  {n:3d}  {i}  {nm(i)}  [{', '.join(sorted({a for a in per_arch if i in per_arch[a]['un']}))}]")
print('NOT IN POOL:')
for i,n in missing_pool.most_common():
    print(f"  {n:3d}  {i}  [{', '.join(sorted({a for a in per_arch if i in per_arch[a]['miss']}))}]")
# svsim built-in decks vs tournament cores
print()
for name,d in [('PIRATE_SWORD',decks.PIRATE_SWORD),('RAMP_DRAGON',decks.RAMP_DRAGON)]:
    ids={c.card_id:n for c,n in d.items()}
    print(name, sum(ids.values()), 'cards;', 'unimplemented:', [nm(i) for i in ids if POOL[i].has_ability and not has_script(i)])
for hname in ['COMBO_FOREST_HASH','FACE_DRAGON_HASH']:
    h=getattr(decks,hname,None)
    if h:
        fmt,craft,ids=deckcode.decode_deck(h)
        print(hname, len(ids), 'unimpl:', sorted({nm(i) for i in ids if i in POOL and POOL[i].has_ability and not has_script(i)}), 'notpool:', sorted({i for i in ids if i not in POOL}))
