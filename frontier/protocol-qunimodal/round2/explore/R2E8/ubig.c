// Exact U computation with 256-bit two's-complement integers (4 x uint64 limbs).
// Valid when prod a_i < 2^250 (all |A_j|,|g_i| <= prod a_i). Caller checks the bound (printed flag).
// stdin: "r k a1..ak" ; stdout: "T6 F Bh1 Ubits" (Ubits for b=1..T6+3), same format as ufast.
// Bh1 = rule H1 prediction (T6-2 if tau_s<=-2 and s>=2mu else T6).
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
typedef struct { uint64_t w[4]; } W;
static inline W add(W a, W b){ W c; unsigned __int128 t=0; for(int i=0;i<4;i++){ t+= (unsigned __int128)a.w[i]+b.w[i]; c.w[i]=(uint64_t)t; t>>=64;} return c; }
static inline W neg(W a){ W c; for(int i=0;i<4;i++) c.w[i]=~a.w[i]; W one={{1,0,0,0}}; return add(c,one); }
static inline W sub(W a, W b){ return add(a,neg(b)); }
static inline int lt(W a, W b){ // signed a<b
  int sa=(int)(a.w[3]>>63), sb=(int)(b.w[3]>>63);
  if(sa!=sb) return sa>sb;
  for(int i=3;i>=0;i--){ if(a.w[i]!=b.w[i]) return a.w[i]<b.w[i]; }
  return 0; }
static inline int isneg_small(W a, long long *v){ // returns small value if fits
  return 0; }
static W A[1<<13], d[1<<13], g[1<<14];
static W Z;
int main(void){
  int r,k; int a[64];
  while(scanf("%d %d",&r,&k)==2){
    double lg=0;
    for(int i=0;i<k;i++){ scanf("%d",&a[i]); lg+=log2((double)a[i]); }
    if(lg>248){ printf("OVERFLOW\n"); continue; }
    int deg=0; memset(&A[0],0,sizeof(W)); A[0].w[0]=1;
    for(int i=0;i<k;i++){ int Aa=a[i], nd=deg+Aa-1; W s=Z;
      for(int t=0;t<=nd;t++){ if(t<=deg) s=add(s,A[t]); if(t-Aa>=0&&t-Aa<=deg) s=sub(s,A[t-Aa]); d[t]=s; }
      deg=nd; memcpy(A,d,sizeof(W)*(deg+1)); }
    int D=deg, F=0; for(int i=0;i<k;i++) F+=a[i]/r;
    int bmax0=1; (void)bmax0;
    // g_i = sum_{j<=i, j=i mod r} B_j, B=A(1-q); tail g_i (i>=D+1) is tau_{i mod r}
    int Lt=D+2+r; 
    for(int i=0;i<Lt;i++){ W v=Z; if(i<=D) v=A[i]; if(i>=1 && i-1<=D) v=sub(v,A[i-1]); g[i]= (i>=r)? add(v,g[i-r]) : v; }
    W tauW[64]; for(int i=D+1;i<D+1+r;i++) tauW[i%r]=g[i];
    int mu=0; for(int j=1;j<r;j++) if(lt(Z,tauW[j])) mu=j;
    int num=D+1-2*mu; int T6=1+(num>=0? num/r : -((-num+r-1)/r));
    int s=(D+1)%r; W m2=neg((W){{2,0,0,0}});
    int Bh1=( !lt(m2,tauW[s]) && s>=2*mu)? T6-2 : T6;
    int bmax=T6+3; int Nmax=D+r*(bmax-1); int L=Nmax/2+2; if(L<Lt) L=Lt;
    for(int i=0;i<L;i++){ W v=Z; if(i<=D) v=A[i]; if(i>=1 && i-1<=D) v=sub(v,A[i-1]); g[i]= (i>=r)? add(v,g[i-r]) : v; }
    printf("%d %d %d ",T6,F,Bh1);
    for(int b=1;b<=bmax;b++){ int N=D+r*(b-1), rb=r*b, ok=1;
      for(int i=1;i<=N/2;i++){ W cc=(i>=rb)?g[i-rb]:Z; if(lt(g[i],cc)){ok=0;break;} }
      putchar(ok?'1':'0'); }
    putchar('\n');
  }
  return 0;
}
