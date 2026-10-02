# Check ubig output for the base family: U must equal [1,Bh1] exactly (Bh1 = rule H1 prediction).
# Reports count, number of instances where U is not exactly [1,Bh1] (and the weaker failure U not containing [1,Bh1]).
import sys
n=0; notexact=0; notcontain=0; ex=[]
for f in sys.argv[1:]:
    rin=f.replace('_out','_in')
    for l,o in zip(open(rin),open(f)):
        T6,F,Bh,bits=o.split(); Bh=int(Bh); n+=1
        want='1'*Bh+'0'*(len(bits)-Bh) if Bh>=0 else '0'*len(bits)
        if bits!=want: notexact+=1; ex.append((l.strip(),o.strip()))
        if '0' in bits[:max(Bh,0)]: notcontain+=1
print("instances",n,"U != [1,B*]:",notexact,"U missing part of [1,B*]:",notcontain); print(ex[:10])
