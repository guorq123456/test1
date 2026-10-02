# Numerical verification of the constants used in the large-k hand proofs (proof_S2_r456.txt, Lemmas 12, 13).
import mpmath as mp
from math import comb, log2, floor, ceil
mp.mp.dps=40
def H(t): t=mp.mpf(t); return -(t*mp.log(t,2)+(1-t)*mp.log(1-t,2))
ok=True
def chk(name,cond):
    global ok
    print(("OK  " if cond else "FAIL"),name); ok&=bool(cond)
# ---- Lemma 12: r in {4,5}, k >= 401, theta = 9/20
th=mp.mpf(9)/20
chk("1-2theta=0.1 > theta^5", 1-2*th > th**5)
lo=mp.mpf(9)/29-mp.mpf(5)/401
chk("H(9/29-5/401) >= 0.8785  [%s]"%mp.nstr(H(lo),8), H(lo)>=mp.mpf('0.8785'))
f4=lambda k: mp.mpf('0.8785')*k-mp.log(k+1,2)-mp.log(10,2)-(k-1)/mp.mpf(2)
chk("r=4: f4(401)>0 and f4 increasing (0.3785 > 1/(402 ln2))", f4(401)>0 and mp.mpf('0.3785')>1/(402*mp.log(2)))
phi=(1+mp.sqrt(5))/2
V5=lambda k: (mp.mpf(2)/5)*(2*mp.sin(mp.pi/5)*phi**k+2*mp.sin(2*mp.pi/5))
chk("r=5: V5(k) <= phi^k for k>=2 (0.4703+0.7609/phi^2<1)", mp.mpf('0.4703')+mp.mpf('0.7609')/phi**2<1 and V5(2)<=phi**2)
f5=lambda k: mp.mpf('0.8785')*k-mp.log(k+1,2)-mp.log(10,2)-k*mp.log(phi,2)
chk("r=5: f5(401)>0 and increasing", f5(401)>0 and (mp.mpf('0.8785')-mp.log(phi,2))>1/(402*mp.log(2)))
# ---- Lemma 13: r = 6, k >= 601
L2=mp.mpf('0.395'); R0=L2/(1-L2)
kap=(1-R0)**2-(1+mp.mpf(1)/601)/(mp.mpf('0.605')**2*601)
chk("R0=%s, kappa_lb=%s >= 0.11592"%(mp.nstr(R0,8),mp.nstr(kap,8)), kap>=mp.mpf('0.11592'))
chk("R0^7=%s < 0.11592"%mp.nstr(R0**7,6), R0**7<mp.mpf('0.11592'))
chk("0.395k-6 >= 0.385k for k>=601", mp.mpf('0.395')*601-6>=mp.mpf('0.385')*601)
need=mp.log(1/mp.mpf('0.11592'),2)+mp.log(mp.mpf(1)/3+mp.mpf(2)**-400,2)
print("need b1+b2 >=",mp.nstr(need,8))
# b1 for p>=300: H(x1/p) >= H(0.385-1/300)
h1=H(mp.mpf('0.385')-mp.mpf(1)/300); c1=h1-mp.log(3,2)/2
print("p>=300: b1 >= %s p - log2(p+1)"%mp.nstr(c1,8))
# b2 for s>=300: vertices of the type box
best=None
for s_ in [300]:
    pass
verts=[]
for p2 in (mp.mpf('0.07')-mp.mpf(1)/300, mp.mpf('0.07')):
    for p1 in (mp.mpf('0.245'), mp.mpf('0.255')+mp.mpf(3)/300):
        p0=1-p1-p2; verts.append((p0,p1,p2))
H3=lambda v: -sum(t*mp.log(t,2) for t in v)
Hmin=min(H3(v) for v in verts)
print("s>=300: multinomial type entropy >= %s (vertices %s)"%(mp.nstr(Hmin,8),[tuple(mp.nstr(t,5) for t in v) for v in verts]))
# exact tables for p<300, s<300
def tri(s,x):
    # coefficient of q^x in (1+q+q^2)^s
    return sum(comb(s,j)*comb(s-j,x-2*j) for j in range(0,x//2+1) if x-2*j<=s-j)
b1min={p: log2(comb(p,int(floor(0.385*p))))-p*log2(3)/2 for p in range(0,300)}
b2min={}
for s in range(0,300):
    x2=int(ceil(mp.mpf('0.385')*s))
    b2min[s]=log2(tri(s,x2))-s if s>0 else 0.0
m1=min(b1min.values()); m2=min(b2min.values())
print("min_{p<300} b1min = %.4f   min_{s<300} b2min = %.4f"%(m1,m2))
# case p<300, s>=302 ; case s<300, p>=302 ; case both >=300  (k>=601)
def b1_big(p): return float(c1)*p-log2(p+1)
def b2_big(s): return float(Hmin-1)*s-2*log2(s+1)
c_a=min(m1+b2_big(s) for s in range(302,3000)); c_b=min(m2+b1_big(p) for p in range(302,3000))
c_c=min(b1_big(p)+b2_big(s) for p in range(300,1000,7) for s in range(300,1000,7))
print("case p<300: %.3f  case s<300: %.3f  case both>=300: %.3f"%(c_a,c_b,c_c))
chk("all cases >= need", min(c_a,c_b,c_c)>=float(need) and float(c1)>0 and float(Hmin)>1)
chk("b1_big, b2_big increasing beyond 300", float(c1)>1/(301*0.6931) and float(Hmin-1)>2/(301*0.6931))
print("ALL OK" if ok else "SOME FAILED")
