# summarise big_*.txt (r>=1000 family runs): points, A/B chain-top errors, k range
import sys,glob
for fn in sorted(glob.glob('big_*.txt')):
    n=eA=eB=0; ks=[]
    for line in open(fn):
        t=line.split()
        if t[0]=='r': continue
        k,eo,ee=int(t[0]),int(t[1]),int(t[2])
        iA=t.index('A'); iB=t.index('B')
        aA=(int(t[iA+1])!=eo or int(t[iA+2])!=ee); aB=(int(t[iB+1])!=eo or int(t[iB+2])!=ee)
        n+=1; eA+=aA; eB+=aB; ks.append(k)
        if aA or aB: print('  miss',fn,line.strip())
    print(fn,'points',n,'k range',min(ks),max(ks),'A-wrong',eA,'B-wrong',eB)
