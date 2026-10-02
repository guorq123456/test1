from cert import Inst
r=5; KMAX=12; fails=0; tot=0
def ms(n,k):
    if n==1: yield (k,); return
    for c in range(k+1):
        for rest in ms(n-1,k-c): yield (c,)+rest
for k in range(1,KMAX+1):
    for cnt in ms(r-1,k):
        rho=[]
        for i,c in enumerate(cnt): rho+=[i+1]*c
        s=Inst(r,rho); tot+=1
        if not s.TP() or s.EO(s.mu_inf()-6): fails+=1
print("python shifted: checked",tot,"fails",fails)
