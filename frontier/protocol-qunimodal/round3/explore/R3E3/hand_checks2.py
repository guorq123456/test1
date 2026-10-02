# Constants for the large-k hand proofs with threshold k >= 141 (Lemmas 12', 13' of proof_S2_r456.txt).
# Only binomial/trinomial coefficients with n <= 140 are evaluated exactly (tables); larger n use entropy bounds.
import mpmath as mp
from math import comb, log2, floor, ceil
mp.mp.dps=40
K0=141
def H(t): t=mp.mpf(t); return -(t*mp.log(t,2)+(1-t)*mp.log(1-t,2))
ok=True
def chk(name,cond):
    global ok
    print(("OK  " if cond else "FAIL"),name); ok&=bool(cond)
# ---------- Lemma 12' (r=4,5)
th=mp.mpf(9)/20
chk("1-2theta=1/10 > theta^5", 1-2*th>th**5)
lo=mp.mpf(9)/29-mp.mpf(5)/K0; h=H(lo)
print("m/k >= %s, H >= %s"%(mp.nstr(lo,8),mp.nstr(h,8)))
f4=h*K0-mp.log(K0+1,2)-mp.log(10,2)-(K0-1)/mp.mpf(2)
chk("r=4 at k=141: %s > 0, increasing"%mp.nstr(f4,6), f4>0 and h-mp.mpf(1)/2>1/((K0+1)*mp.log(2)))
phi=(1+mp.sqrt(5))/2
f5=h*K0-mp.log(10*(K0+1),2)-K0*mp.log(phi,2)
chk("r=5 at k=141: %s > 0, increasing"%mp.nstr(f5,6), f5>0 and h-mp.log(phi,2)>1/((K0+1)*mp.log(2)))
chk("r=5: V5(k)<=phi^k (k>=2)", mp.mpf('0.4703')+mp.mpf('0.7609')/phi**2<1)
# ---------- Lemma 13' (r=6)
L2=mp.mpf('0.395'); R0=L2/(1-L2)
kap=(1-R0)**2-(1+mp.mpf(1)/K0)/(mp.mpf('0.605')**2*K0)
chk("kappa_lb=%s > R0^7=%s"%(mp.nstr(kap,8),mp.nstr(R0**7,8)), kap>R0**7)
lam1=L2-mp.mpf(6)/K0
need=mp.log(1/kap,2)+mp.log(mp.mpf(1)/3+mp.mpf(2)**-100,2)
print("lambda in [%s, 0.395], need b1+b2 >= %s"%(mp.nstr(lam1,8),mp.nstr(need,8)))
def tri(s,x):
    return sum(comb(s,j)*comb(s-j,x-2*j) for j in range(0,x//2+1) if 0<=x-2*j<=s-j)
b1min={p: (log2(comb(p,int(floor(lam1*p))))-p*log2(3)/2) for p in range(0,K0)}
b2min={s: (log2(tri(s,int(ceil(lam1*s))))-s if s>0 else 0.0) for s in range(0,K0)}
c1=H(lam1-mp.mpf(1)/K0)-mp.log(3,2)/2
print("p>=141: b1 >= %s p - log2(p+1)"%mp.nstr(c1,8))
tau=mp.mpf('0.065')
P2=(tau-mp.mpf(1)/K0, tau); P1=(lam1-2*tau, L2-2*tau+mp.mpf(3)/K0)
verts=[(1-a-b,a,b) for b in P2 for a in P1]
H3=lambda v: -sum(t*mp.log(t,2) for t in v)
Hmin=min(H3(v) for v in verts)
prodmin=min(v[0]*v[1]*v[2] for v in verts)   # product is also minimized at a vertex? check on a grid below
grid=[(1-a-b,a,b) for b in [P2[0]+(P2[1]-P2[0])*i/20 for i in range(21)] for a in [P1[0]+(P1[1]-P1[0])*j/20 for j in range(21)]]
chk("grid entropy >= vertex min", min(H3(v) for v in grid)>=Hmin-mp.mpf(10)**-30)
pm=min(v[0]*v[1]*v[2] for v in grid)
# product pi0*pi1*pi2 is >= its min over box; use a safe lower bound: pi0>=min pi0, pi1>=min pi1, pi2>=min pi2
pl=max(v[0] for v in verts)*P1[1]*P2[1]   # UPPER bound of pi0*pi1*pi2 (the factor is decreasing in it)
print("s>=141: type entropy >= %s; pi0*pi1*pi2 <= %s"%(mp.nstr(Hmin,8),mp.nstr(pl,6)))
def b2asym(s):
    s=mp.mpf(s)
    corr=(mp.mpf(1)/12)*(1/(min(v[0] for v in verts)*s)+1/(P1[0]*s)+1/(P2[0]*s))/mp.log(2)
    return s*(Hmin-1)-mp.log(2*mp.pi,2)-mp.log(s,2)-mp.log(pl,2)/2-corr
def b1asym(p): return c1*p-mp.log(p+1,2)
chk("b1asym increasing for p>=141", c1>1/((K0+1)*mp.log(2)))
chk("b2asym increasing for s>=141 (Hmin-1 > 1/(141 ln2))", Hmin-1>1/(K0*mp.log(2)))
# three-term improvement: Tri_s(x2) >= M(j-1)+M(j)+M(j+1) >= M(j)(1+rm+rp), with ratio lower bounds over the box
pi0min=min(v[0] for v in verts); pi0max=max(v[0] for v in verts)
a1,b1_,c1_=P1[0],pi0max,P2[1]           # rp = n1(n1-1)/((n0+1)(n2+1)) >= (a s)(a s-1)/((b s+1)(c s+1))
S=mp.mpf(K0)
rp=(a1*a1/(b1_*c1_))*(1-1/(a1*S))/((1+1/(b1_*S))*(1+1/(c1_*S)))
a2,b2_,c2_=P1[1],pi0min,P2[0]           # rm = n0 n2/((n1+1)(n1+2)) >= (b s)(c s)/((a s+1)(a s+2))
rm=(b2_*c2_/(a2*a2))/((1+1/(a2*S))*(1+2/(a2*S)))
# second neighbours: M(j+2)/M(j+1) = (n1-2)(n1-3)/((n0+2)(n2+2)),  M(j-2)/M(j-1) = (n0-1)(n2-1)/((n1+3)(n1+4))
rp2=(a1*a1/(b1_*c1_))*(1-2/(a1*S))*(1-3/(a1*S))/((1+2/(b1_*S))*(1+2/(c1_*S)))
rm2=(b2_*c2_/(a2*a2))*(1-1/(b2_*S))*(1-1/(c2_*S))/((1+3/(a2*S))*(1+4/(a2*S)))
gain=mp.log(1+rp+rm+rp*rp2+rm*rm2,2)
print("five-term gain: rp>=%s rm>=%s rp2>=%s rm2>=%s gain=%s bits (all factors increasing in s)"%(mp.nstr(rp,6),mp.nstr(rm,6),mp.nstr(rp2,6),mp.nstr(rm2,6),mp.nstr(gain,6)))
_b2asym=b2asym
b2asym=lambda s: _b2asym(s)+gain
A=min(b1min[p]+b2min[s] for p in range(K0) for s in range(K0) if p+s>=K0)
B=float(b1asym(K0))+min(b2min.values())
C=min(b1min.values())+float(b2asym(K0))
Dd=float(b1asym(K0)+b2asym(K0))
print("case (p,s<=140): %.3f  (p>=141,s<=140): %.3f  (p<=140,s>=141): %.3f  (both>=141): %.3f"%(A,B,C,Dd))
chk("all cases >= need", min(A,B,C,Dd)>=float(need))
print("ALL OK" if ok else "SOME FAILED")
