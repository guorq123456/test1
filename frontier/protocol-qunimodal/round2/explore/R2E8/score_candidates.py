# Score candidate rules on ufast/ubig outputs (format "T6 F Bh1 Ubits", Ubits for b=1..T6+3).
# Candidates: C1 b<=T6 ; C2 b<=1+F ; H1 b<=Bh1. Reports instance errors and b-test errors.
import sys
tot=0; inst={'C1':0,'C2':0,'H1':0}; berr={'C1':0,'C2':0,'H1':0}; btests=0
for f in sys.argv[1:]:
    for o in open(f):
        T6,F,Bh,bits=o.split(); T6=int(T6);F=int(F);Bh=int(Bh); tot+=1; btests+=len(bits)
        for name,B in (('C1',T6),('C2',1+F),('H1',Bh)):
            e=sum(1 for b in range(1,len(bits)+1) if (b<=B)!=(bits[b-1]=='1'))
            berr[name]+=e; inst[name]+= (e>0)
print("files",sys.argv[1:] if len(sys.argv)<4 else len(sys.argv)-1,"instances",tot,"b-tests",btests)
for n in inst: print(n,"instance errors",inst[n],"b-test errors",berr[n])
