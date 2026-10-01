# For each TM output file, reconstruct polys and count real roots with PARI polsturm (exact Sturm).
import sys, subprocess
from crt import parse_line
def run(files, out):
    polys = []
    for f in files:
        for line in open(f):
            k, m, c = parse_line(line)
            assert all(x > 0 for x in c), (k, m)
            polys.append((k, m, c))
    gpin = []
    for k, m, c in polys:
        # Pol takes coefficient vector from highest degree
        gpin.append('f=Pol([%s]); print(%d," ",%d," ",poldegree(f)," ",polsturm(f)," ",issquarefree(f));' % (','.join(str(x) for x in reversed(c)), k, m))
    open(out+'.gp', 'w').write('\n'.join(gpin) + '\nquit\n')
    r = subprocess.run(['gp', '-q', '-s', '2000000000', out+'.gp'], capture_output=True, text=True)
    open(out, 'w').write(r.stdout)
    if r.stderr: print(r.stderr[:2000])
if __name__ == '__main__':
    run(sys.argv[2:], sys.argv[1])
