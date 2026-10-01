import sys
def poly(r,a,b):
    c=[1]
    for A in a:
        n=[0]*(len(c)+A-1)
        for i,v in enumerate(c):
            for j in range(A): n[i+j]+=v
        c=n
    n=[0]*(len(c)+r*(b-1))
    for i,v in enumerate(c):
        for y in range(b): n[i+r*y]+=v
    return n
def unimodal(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
if __name__=='__main__':
    for line in sys.stdin:
        x=list(map(int,line.split())); r,k=x[0],x[1]; a=x[2:2+k]; b=x[2+k]
        print(1 if unimodal(poly(r,a,b)) else 0)
