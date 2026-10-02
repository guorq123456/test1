# Near-miss diagnostics from descent counts nneg(b) (exact, s2big NNEG mode) on random structured instances.
# Checks two monotonicity relations that would imply S2:
#  (M2) nneg(b) >= nneg(b-2) for all b in (F+2, T6+2]      [implies S2(ii)]
#  (P1) nneg(b+1) <= nneg(b) when b-1-F odd, b>F             [implies S2(i)]
# Reports counts of instances breaking each relation, and minimal-slack near misses for S2 itself:
#  ii-slack = min over b'<=b-2 with nneg(b')>0 of nneg(b)   (0 would be an S2(ii) violation)
#  i-slack  = min over b with b-1-F odd, nneg(b)=0 of nneg(b+1) ... only meaningful if >0 → violation
import sys,subprocess,random,json
if sys.argv[1]=='file':   # instance lines from a file (only the part before '|' is used)
    fams=[sys.argv[2]]; lines=''.join(l.split('|')[0].strip()+'\n' for l in open(sys.argv[2]))
else:
    fams=sys.argv[1].split(','); seed=int(sys.argv[2]); n=int(sys.argv[3])
    lines=subprocess.run(['python3','gen_rand.py',fams[0],str(seed),str(n)],capture_output=True,text=True).stdout
    for f in fams[1:]:
        lines+=subprocess.run(['python3','gen_rand.py',f,str(seed),str(n)],capture_output=True,text=True).stdout
out=subprocess.run(['./s2big'],input=lines,capture_output=True,text=True,env={'NNEG':'1'}).stdout.strip().split('\n')
cM2=cP1=0; exM2=[];exP1=[]; best_ii=(10**9,None)
for o in out:
    rest=o.split('|')[1].split(); F,T6,Bs,shape,par=map(int,rest[:5]); nn=[int(x) for x in rest[6].strip(',').split(',')]
    N={F+1+j:v for j,v in enumerate(nn)}
    for b in range(1,F+1): N[b]=0
    bs=sorted(N)
    if any(N[b]<N[b-2] for b in bs if b-2 in N): cM2+=1; exM2.append(o) 
    if any(N[b+1]>N[b] for b in bs if b>F and (b-1-F)%2==1 and b+1 in N): cP1+=1; exP1.append(o)
    for b in bs:
        if any(N[bp]>0 for bp in bs if bp<=b-2):
            if N[b]<best_ii[0]: best_ii=(N[b],o)
print(json.dumps(dict(fams=fams,n=len(out),M2_breaks=cM2,P1_breaks=cP1,best_ii_slack=best_ii[0],best_ii=best_ii[1][:200] if best_ii[1] else None,exM2=[e[:200] for e in exM2[:3]],exP1=[e[:200] for e in exP1[:3]])))
