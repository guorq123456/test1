"""Print a deck's cards with the simulator's script docstring (= implemented mechanics). usage: deck_mech.py HASH|label-in-file FILE"""
import sys, re
from pathlib import Path as _P
ROOT = str(_P(__file__).resolve().parents[5])
sys.path.insert(0, ROOT)
from svsim.cards import library  # noqa
from svsim.cards.pool import POOL
from svsim.cards import deckcode
from svsim.core.script import _SCRIPTS
from collections import Counter
def mech(h):
    f,c,ids=deckcode.decode_deck(h)
    cnt=Counter(ids)
    for i,n in sorted(cnt.items(), key=lambda x:(POOL[x[0]].cost,x[0])):
        cd=POOL[i]; s=_SCRIPTS.get(i); doc=(s.__doc__ or type(s).__doc__ or '').strip() if s else '(no script)'
        doc=re.sub(r'\s+',' ',doc)
        stats='' if cd.atk is None else f' {cd.atk}/{cd.life}'
        kw=str(cd.keywords).replace('Keyword.','') if cd.keywords else ''
        print(f"{n}× [{cd.cost}费{stats}] {cd.name_zh} / {cd.name} {'【新】' if cd.card_set==10010 else ''} {kw}\n     {doc[:420]}")
        # related tokens
        for r in cd.related or ():
            if r in POOL:
                rs=_SCRIPTS.get(r); rd=re.sub(r'\s+',' ',(rs.__doc__ or type(rs).__doc__ or '').strip()) if rs else ''
                print(f"       -> {POOL[r].name_zh} / {POOL[r].name} [{POOL[r].cost}费]: {rd[:300]}")
if len(sys.argv)==3:
    for line in open(sys.argv[2],encoding='utf-8'):
        if line.startswith(sys.argv[1]+'|'):
            print('#####', sys.argv[1]); mech(line.split('|')[1].strip())
else:
    mech(sys.argv[1])
