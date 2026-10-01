# Shared loader for box data produced by enum.c
import pickle, os
def load():
    pk='/tmp/claude-0/qu/explore/E3/box.pkl'
    if os.path.exists(pk):
        return pickle.load(open(pk,'rb'))
    recs=[]
    for r in range(2,7):
        for ln in open(f'/tmp/claude-0/qu/explore/E3/box_r{r}.txt'):
            x=list(map(int,ln.split())); k=x[1]
            recs.append((r,tuple(x[2:2+k]),x[2+k]))
    pickle.dump(recs,open(pk,'wb'))
    return recs
