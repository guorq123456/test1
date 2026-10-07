import json,re,sys,glob
from collections import Counter
R='/home/claude/sv/svsim/cards/'
A='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
pool={c['id']:c for c in json.load(open(R+'data/rotation.json'))}
doc={}
for f in glob.glob(R+'*.py'):
    s=open(f).read()
    names={m.group(1):int(m.group(2)) for m in re.finditer(r'^(\w+) = card\((\d+)\)',s,re.M)}
    for m in re.finditer(r'@register\((\w+)\.card_id\)\s*\nclass \w+\([^)]*\):\s*\n\s*"""(.*?)"""',s,re.S):
        if m.group(1) in names: doc[names[m.group(1)]]=' '.join(m.group(2).split())
def dec(t):
    n=0
    for ch in t:n=n*64+A.index(ch)
    return n
h=sys.argv[1].split('hash=')[-1]
p=h.split('.')
print('format',p[0],'class',p[1])
cnt=Counter(dec(t) for t in p[2:])
for i,c in sorted(cnt.items(),key=lambda x:(pool.get(x[0],{}).get('cost',99),x[0])):
    q=pool.get(i)
    if not q: print(c,i,'NOT IN POOL');continue
    st=f"{q['atk']}/{q['life']}" if q['type']=='follower' else q['type']
    print(f"{c}x [{q['cost']}] {q['zh']} / {q['name']} ({st}; {','.join(q['kw'])}; set {q['set']}) :: {doc.get(i,'(no script)')}")
    for r in q.get('related',[]):
        rq=pool.get(r)
        if rq and r in doc: print(f"     -> {rq['zh']} / {rq['name']} :: {doc[r]}")
print('total',sum(cnt.values()))
