import gzip, re
seqs = {}
for line in gzip.open('/tmp/claude-0/oeis/stripped.gz', 'rt'):
    if not line.startswith('A'): continue
    a, s = line.split(' ', 1)
    t = s.strip().strip(',')
    seqs[a] = ',' + t + ','
names = {}
for line in gzip.open('/tmp/claude-0/oeis/names.gz', 'rt'):
    if line.startswith('A'):
        a, nm = line.split(' ', 1); names[a] = nm.strip()
def terms(a): return [int(v) for v in seqs[a].strip(',').split(',')]
def antidiag_col(a, m, nmax=12):
    s = terms(a); out = []
    for n in range(1, nmax+1):
        d = n + m - 1; idx = (d-1)*d//2 + (n-1)
        if idx < len(s): out.append(s[idx])
    return out
tabs = {'A202889':'nonzero 0..2','A203101':'nonzero 0..3','A203191':'nonzero 0..4','A203057':'nonzero 0..5','A203066':'nonzero 0..6','A202916':'nonzero 0..7',
        'A217457':'min hv 0..2','A218181':'min hv 0..3','A217645':'min hva 0..2','A218651':'min hva 0..3','A217547':'min hvda 0..2','A218056':'min hvda 0..3',
        'A217637':'min hv 0..1','A218084':'min hva 0..1','A217982':'min hvda 0..1','A200886':'nopeak','A200871':'nopeakvalley'}
for t, desc in tabs.items():
    for m in range(1, 5):
        col = antidiag_col(t, m)
        # use terms from index 3 on (skip small trivial values), need >= 6 terms
        key = col[2:9]
        if len(key) < 6 or max(key) < 50: continue
        pat = ',' + ','.join(map(str, key)) + ','
        hits = [a for a, s in seqs.items() if pat in s and a != t]
        print(t, desc, 'col', m, key[:4], '->', [(h, names.get(h,'')[:70]) for h in hits][:8])
