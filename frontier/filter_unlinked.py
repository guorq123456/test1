"""Keep only coincidence pairs where neither OEIS entry mentions the other anywhere in its text."""
import json, re, os, sys
ROOT = '/tmp/claude-0/oeis/oeisdata/seq'
def entry(a):
    with open(f'{ROOT}/{a[:4]}/{a}.seq', encoding='utf-8', errors='replace') as f:
        return f.read()
def field(txt, tag):
    return [l[11:] for l in txt.splitlines() if l.startswith(tag)]
pairs = json.load(open(sys.argv[1]))
keep = []
for r in pairs:
    if r['diverge']:
        continue
    ta, tb = entry(r['a']), entry(r['b'])
    if r['b'] in ta or r['a'] in tb:
        continue
    ka = ''.join(field(ta, '%K')); kb = ''.join(field(tb, '%K'))
    if any(w in ka + kb for w in ('dead', 'dupe', 'uned', 'probation')):
        continue
    r['name_a'] = ' '.join(field(ta, '%N')); r['name_b'] = ' '.join(field(tb, '%N'))
    r['kw_a'] = ka; r['kw_b'] = kb
    r['auth_a'] = ' '.join(field(ta, '%A')); r['auth_b'] = ' '.join(field(tb, '%A'))
    keep.append(r)
json.dump(keep, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print(len(keep), 'unlinked, non-diverging pairs')
