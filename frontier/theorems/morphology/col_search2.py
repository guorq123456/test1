import gzip
seqs = {}; names = {}
for line in gzip.open('/tmp/claude-0/oeis/stripped.gz', 'rt'):
    if line.startswith('A'):
        a, s = line.split(' ', 1); seqs[a] = ',' + s.strip().strip(',') + ','
for line in gzip.open('/tmp/claude-0/oeis/names.gz', 'rt'):
    if line.startswith('A'):
        a, nm = line.split(' ', 1); names[a] = nm.strip()
fam = [a for a, nm in names.items() if ('with every nonzero element less than or equal to some horizontal or vertical neighbor' in nm)
       or ('minimum value of corresponding elements and their' in nm and 'random 0..' in nm and 'sorted' not in nm)
       or ('interior element greater than both neighbors' in nm)]
print(len(fam), 'family members')
for a in sorted(fam):
    t = [int(v) for v in seqs[a].strip(',').split(',')]
    if 'T(n,k)' in names[a]: continue
    key = [v for v in t if v > 30][:7]
    if len(key) < 6: continue
    pat = ',' + ','.join(map(str, key)) + ','
    hits = [h for h, s in seqs.items() if pat in s and h != a]
    hits = [h for h in hits if 'T(n,k)' not in names[h]]
    if hits:
        print(a, names[a][:60], '->', [(h, names[h][:60]) for h in hits])
