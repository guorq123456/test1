"""Label external lists by nearest known archetype (>=25 shared cards), and write a combined report table.
usage: label_decks.py TARGET.txt REF1.txt[:names.tsv] ...   (names.tsv: label<TAB>archetype)
"""
import sys
from pathlib import Path as _P
ROOT = str(_P(__file__).resolve().parents[5])
sys.path.insert(0, ROOT)
from svsim.cards import library  # noqa
from svsim.cards.pool import POOL
from svsim.cards import deckcode
from collections import Counter
CRAFT2C={1:"精灵",2:"皇家护卫",3:"巫师",4:"龙族",5:"梦魇",6:"主教",7:"超越者"}
def read(path):
    out=[]
    for line in open(path,encoding='utf-8'):
        line=line.strip()
        if not line or line.startswith('#'): continue
        l,h=line.split('|')[0].strip(), line.split('|')[1].strip()
        f,c,ids=deckcode.decode_deck(h); out.append((l,c,ids,h))
    return out
def names(ids): return Counter(POOL[i].name for i in ids)
def ov(a,b): return sum(min(a[k],b[k]) for k in a)
tgt=read(sys.argv[1])
refs=[]; arch={}
for spec in sys.argv[2:]:
    p,_,n=spec.partition(':'); refs+=read(p)
    if n:
        for line in open(n,encoding='utf-8'):
            if '\t' in line: a,b=line.rstrip('\n').split('\t')[:2]; arch[a]=b
for l,c,ids,h in tgt:
    nn=names(ids); best=max(((ov(nn,names(r[2])),r[0]) for r in refs if r[1]==c), default=(0,'-'))
    new=sum(POOL[i].card_set==10010 for i in ids)
    print(f"{l}\t{CRAFT2C[c]}\t{new}\t{best[0]}\t{best[1]}\t{arch.get(best[1],'?')}")
