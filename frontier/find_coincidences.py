"""Find pairs of OEIS sequences whose known terms agree on a long, information-rich stretch.

A "coincidence" is a pair (A, B) such that, after aligning offsets, the first K terms agree
exactly, the shared prefix carries real information (many distinct values, not a simple
progression), and the prefix is shared by only a handful of sequences (so it is not just
a famous sequence copied into many entries).
"""
import gzip, sys, collections, math, json

MIN_MATCH = 18        # minimum number of aligned equal terms
MAX_CLUSTER = 3       # ignore prefixes shared by more than this many sequences
SKIP_MAX = 3          # allow dropping up to this many leading terms of one sequence (offset/initial-term noise)

def load(path):
    seqs = {}
    with gzip.open(path, 'rt') as f:
        for line in f:
            if not line.startswith('A'):
                continue
            aid, rest = line.split(' ', 1)
            terms = [t for t in rest.strip().strip(',').split(',') if t]
            seqs[aid] = terms
    return seqs

def informative(ts):
    """Reject low-information prefixes: few distinct values, constant, linear, periodic, tiny."""
    if len(set(ts)) < 10:
        return False
    try:
        v = [int(t) for t in ts]
    except ValueError:
        return False
    if max(abs(x) for x in v) < 50:
        return False
    d = [b - a for a, b in zip(v, v[1:])]
    if len(set(d)) <= 2:
        return False
    dd = [b - a for a, b in zip(d, d[1:])]
    if len(set(dd)) <= 1:
        return False
    return True

def main():
    seqs = load(sys.argv[1])
    idx = collections.defaultdict(set)
    for aid, ts in seqs.items():
        for s in range(SKIP_MAX + 1):
            pre = ts[s:s + MIN_MATCH]
            if len(pre) == MIN_MATCH and informative(pre):
                idx[','.join(pre)].add(aid)
    pairs = {}
    for key, ids in idx.items():
        if 2 <= len(ids) <= MAX_CLUSTER:
            ids = sorted(ids)
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    pairs.setdefault((ids[i], ids[j]), key)
    out = []
    for (a, b), key in pairs.items():
        ta, tb = seqs[a], seqs[b]
        # longest exact agreement over any alignment with small skips
        best = 0
        for sa in range(SKIP_MAX + 1):
            for sb in range(SKIP_MAX + 1):
                n = 0
                while sa + n < len(ta) and sb + n < len(tb) and ta[sa + n] == tb[sb + n]:
                    n += 1
                if n > best:
                    best, align = n, (sa, sb)
        sa, sb = align
        # does one diverge after the shared stretch (both have more terms but differ)?
        diverge = sa + best < len(ta) and sb + best < len(tb)
        out.append(dict(a=a, b=b, match=best, align=align, len_a=len(ta), len_b=len(tb), diverge=diverge,
                        sample=','.join(ta[sa:sa + 12])))
    out.sort(key=lambda r: -r['match'])
    json.dump(out, sys.stdout)

main()
