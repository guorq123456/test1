import json,sys
from collections import Counter
R='/home/claude/sv/svsim/cards/data/'
pool={c['id']:c for c in json.load(open(R+'unlimited.json'))}
pool.update({c['id']:c for c in json.load(open(R+'rotation.json'))})
rot={c['id'] for c in json.load(open(R+'rotation.json'))}
A='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
def dec(t):
    n=0
    for ch in t:n=n*64+A.index(ch)
    return n
def cnt(h):
    h=h.split('hash=')[-1].split('&')[0]
    return Counter(dec(t) for t in h.split('.')[2:])
def name(i):
    q=pool.get(i)
    if not q: return (99,f'?{i}')
    return (q['cost'], f"[{q['cost']}] {q['zh']} / {q['name']}"+('' if i in rot else ' (ROTATED)'))
# args: file with lines label|hash
lists=[l.rstrip('\n').split('|') for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
cs=[(lab,cnt(h)) for lab,h in lists]
ids=set().union(*[c.keys() for _,c in cs])
rows=sorted(ids,key=lambda i:(name(i)[0],name(i)[1]))
labs=[l for l,_ in cs]
print('| card | '+' | '.join(labs)+' |')
print('|'+'---|'*(len(labs)+1))
core=[];
for i in rows:
    v=[c.get(i,0) for _,c in cs]
    if len(set(v))==1: core.append(f"{name(i)[1]} x{v[0]}"); continue
    print('| '+name(i)[1]+' | '+' | '.join(str(x) if x else '·' for x in v)+' |')
print('\nShared by all lists (same count): '+'; '.join(core))
