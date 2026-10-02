# cross-check s2enum2 (exhaustive, int128) against s2big (512-bit) on full small configs: gap and violation counts
import itertools,subprocess
for r,k,vmax in [(10,5,20),(12,6,16),(7,6,15),(30,4,40)]:
    vals=[v for v in range(1,vmax+1) if v%r]
    L=[a for a in itertools.combinations_with_replacement(vals,k) if sum(1 for v in a if 2<=v%r<=r-2)>=3]
    out=subprocess.run(['./s2big'],input=''.join(f"{r} {k} {' '.join(map(str,a))}\n" for a in L),capture_output=True,text=True).stdout.strip().split('\n')
    gap=sum(1 for o in out if o.split('|')[1].split()[3]=='1'); viol=sum('VIOL' in o for o in out)
    e=subprocess.run(['./s2enum2',str(r),str(k),'1',str(vmax),'3','0'],capture_output=True,text=True).stdout
    print(r,k,vmax,'s2big inst',len(out),'gap',gap,'viol',viol,'|',[l for l in e.split('\n') if l.startswith('DONE')][0])
