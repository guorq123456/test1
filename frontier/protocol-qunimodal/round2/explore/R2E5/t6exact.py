# candidate C0: "B* = T6" (established upper bound is attained) and "U = [1,T6]": count failures over all data (data,data2,data3)
import glob
tot=0;f1=0;f2=0
for f in glob.glob('data*/U_r*.txt'):
    for line in open(f):
        x=list(map(int,line.split())); r,s,n,k,F,T6=x[:6]; U=x[6:]
        tot+=1
        if max(U)!=T6: f1+=1
        if U!=list(range(1,T6+1)): f2+=1
print('instances',tot,'B*!=T6:',f1,'U!=[1,T6]:',f2)
