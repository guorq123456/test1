def load(r):
    out=[]
    for l in open(f'/tmp/claude-0/qu/explore/E5/data_r{r}.txt'):
        x=list(map(int,l.split())); k=x[1]; a=x[2:2+k]; m=x[2+k]
        out.append((a,m))
    return out
def uniset(m): return [b for b in range(1,61) if (m>>(b-1))&1]
