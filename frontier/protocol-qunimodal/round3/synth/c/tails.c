// Exact check of the class-pair structure for P = prod[a_i]_q [b]_{q^r}.
// Fixed-width two's complement multi-limb integers (W limbs of 64 bits).
// Usage: s2check W r a1 a2 ... ak     (reads from argv)   prints summary.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
typedef unsigned __int128 u128;
static int W;
static inline void bn_add(uint64_t *z,const uint64_t *x,const uint64_t *y){u128 c=0;for(int i=0;i<W;i++){c+=(u128)x[i]+y[i];z[i]=(uint64_t)c;c>>=64;}}
static inline void bn_sub(uint64_t *z,const uint64_t *x,const uint64_t *y){u128 b=0;for(int i=0;i<W;i++){u128 t=(u128)x[i]-y[i]-b;z[i]=(uint64_t)t;b=(t>>64)?1:0;}}
static inline int bn_neg(const uint64_t *x){return (x[W-1]>>63)&1;}
static inline int bn_iszero(const uint64_t *x){for(int i=0;i<W;i++) if(x[i]) return 0; return 1;}
static inline int bn_sgn(const uint64_t *x){ if(bn_neg(x)) return -1; return bn_iszero(x)?0:1;}
static double bn_todouble(const uint64_t *x){ // signed
  uint64_t t[64]; int neg=bn_neg(x); if(neg){uint64_t z[64];memset(z,0,8*W);bn_sub(t,z,x);} else memcpy(t,x,8*W);
  double v=0; for(int i=W-1;i>=0;i--) v=v*18446744073709551616.0+(double)t[i]; return neg?-v:v;}
// log2 |x| approx
static double bn_log2(const uint64_t *x){ uint64_t t[64]; int neg=bn_neg(x); if(neg){uint64_t z[64];memset(z,0,8*W);bn_sub(t,z,x);} else memcpy(t,x,8*W);
  int i=W-1; while(i>=0&&t[i]==0) i--; if(i<0) return -1e300; double v=(double)t[i]; if(i>0) v+= (double)t[i-1]/18446744073709551616.0; return log2(v)+64.0*i;}
#define AT(arr,j) ((arr)+(size_t)(j)*W)

static double slog2(const uint64_t *x){ return bn_log2(x); }
int main(int argc,char**argv){
  W=atoi(argv[1]); int r=atoi(argv[2]); int k=argc-3; int *a=malloc(sizeof(int)*k); long D=0; long F=0;
  for(int i=0;i<k;i++){a[i]=atoi(argv[3+i]); D+=a[i]-1; F+=a[i]/r; if(a[i]%r==0){printf("RDIV\n");return 0;}}
  long X=(D+1)/2;
  uint64_t *al=calloc((size_t)(X+1)*W,8), *pre=calloc((size_t)(X+2)*W,8);
  AT(al,0)[0]=1; long len=1;
  for(int i=0;i<k;i++){ int ai=a[i]; if(ai<=1) continue;
    long nlen=len+ai-1; if(nlen>X+1) nlen=X+1;
    memset(AT(pre,0),0,8*W);
    for(long j=0;j<nlen;j++){ if(j<len) bn_add(AT(pre,j+1),AT(pre,j),AT(al,j)); else memcpy(AT(pre,j+1),AT(pre,j),8*W);}
    for(long j=0;j<nlen;j++){ long lo=j-ai+1; if(lo<0) lo=0; bn_sub(AT(al,j),AT(pre,j+1),AT(pre,lo)); }
    len=nlen; }
  uint64_t *dl=calloc((size_t)(X+1)*W,8);
  memcpy(AT(dl,0),AT(al,0),8*W);
  for(long x=1;x<=X;x++) bn_sub(AT(dl,x),AT(al,x),AT(al,x-1));
  free(pre);
  if(bn_neg(AT(al,X))){printf("OVERFLOW\n");return 1;}
  uint64_t *zero=calloc(W,8);
  int maxL=(int)(2*(D+1)/r+12);
  // per pair: E suffix sums, |A|, a_n (via T), n*, beta, j0
  uint64_t *E=calloc((size_t)(maxL+8)*W,8), *T=calloc((size_t)(maxL+8)*W,8), *Aabs=calloc(W,8), *t1=calloc(W,8), *t2=calloc(W,8);
  long Nst=1L<<60, beta=1L<<60, Jst=1L<<60;
  int *pC=malloc(sizeof(int)*r); long *pn=malloc(sizeof(long)*r), *pb=malloc(sizeof(long)*r), *pj=malloc(sizeof(long)*r);
  // store E_{j} for j in a small window later: recompute per pair in second pass (cheap enough)
  int np=0;
  for(int pass=0;pass<2;pass++){
   double minM=1e300, minO=1e300; int argM=-1, argO=-1;
   for(int C=1;C<r;C++){ if(((C-(D+1))%2+2)%2) continue;
    int L=0; long xs[1]; (void)xs;
    // y_n
    static long *yl=NULL; static int ylcap=0; if(ylcap<maxL+8){ yl=realloc(yl,sizeof(long)*(maxL+8)); ylcap=maxL+8; }
    for(int kk=0;;kk++){ long Z=(long)(kk/2)*2*r+((kk%2==0)?C:2*r-C); if(Z>D+1) break; yl[L++]=(D+1-Z)/2; }
    #define YV(n) (((n)<L)?AT(dl,yl[(n)]):zero)
    int M=L+6;
    memset(AT(E,M),0,8*W); memset(AT(E,M+1),0,8*W);
    for(int j=M-1;j>=0;j--) bn_add(AT(E,j),AT(E,j+2),YV(j));
    for(int j=M+1;j>=M;j--) memset(AT(T,j),0,8*W);
    for(int j=M-1;j>=0;j--) bn_sub(AT(T,j),AT(E,j),AT(E,j+1));
    bn_sub(t1,AT(E,0),AT(E,1)); if(bn_neg(t1)) bn_sub(Aabs,zero,t1); else memcpy(Aabs,t1,8*W);
    if(bn_iszero(Aabs)) continue;   // pair never binds
    // n*: least n == F+1 (mod 2), n>=0 (with a_{-1}=0) such that T_{n+1} < |A|
    long ns=-1; for(long n=((F+1)%2); n<M-1; n+=2){ bn_sub(t1,AT(T,n+1),Aabs); if(bn_neg(t1)){ns=n;break;} }
    if(ns<0) ns=M-1+((M-1-(F+1))%2!=0); // tail: T=0<|A|
    // beta_C: largest b==F+1 with G_b'>=0 for all b'<=b ; G_b = E_{b-1}-E_{b+2}-|A| ; start at b=ns+2
    long b=ns+2; while(1){ long j=b-1; const uint64_t *Ej=(j<M)?AT(E,j):zero, *Ej3=(j+3<M)?AT(E,j+3):zero;
       bn_sub(t1,Ej,Ej3); bn_sub(t1,t1,Aabs); if(bn_neg(t1)) break; b+=2; if(b>M+4) break; }
    long bC=b-2;
    // j0: least J==F (mod2), J>=0 with E_J<|A|
    long j0=-1; for(long J=(F%2); J<M+2; J+=2){ const uint64_t *EJ=(J<M)?AT(E,J):zero; bn_sub(t1,EJ,Aabs); if(bn_neg(t1)){j0=J;break;} }
    if(pass==0){ if(ns<Nst)Nst=ns; if(bC<beta)beta=bC; if(j0<Jst)Jst=j0; }
    else {
      // M margin: log2((E_{J*-2}-|A|)/E_{J*+1})
      long j=Jst-2; const uint64_t *Ej=(j>=0&&j<M)?AT(E,j):zero; bn_sub(t1,Ej,Aabs);
      const uint64_t *Ej3=(j+3<M)?AT(E,j+3):zero;
      double mM; if(bn_neg(t1)) mM=-1e300; else if(bn_iszero(Ej3)) mM=1e300; else mM=slog2(t1)-slog2(Ej3);
      if(mM<minM){minM=mM;argM=C;}
      // O margin: n=J*-5 must have a_n>=0: T_{J*-4}-|A| >= 0 ; margin log2(T_{J*-4}/|A|)
      long jj=Jst-4; double mO;
      if(jj<0) mO=1e300; else { const uint64_t *Tj=(jj<M)?AT(T,jj):zero; bn_sub(t2,Tj,Aabs); if(bn_neg(t2)) mO=-1e300; else mO=slog2(Tj)-slog2(Aabs);} 
      if(mO<minO){minO=mO;argO=C;}
    }
   }
   if(pass==1){ long Bd=Jst-1;
     printf("r=%d k=%d D=%ld F=%ld Nstar=%ld beta=%ld Bd=%ld S2=%s M=%s O=%s minMmarg=%.6g(C=%d) minOmarg=%.6g(C=%d)\n",r,k,D,F,Nst,beta,Bd,
        beta<=Nst+2?"OK":"FAIL", beta==Bd?"OK":"FAIL", Bd<=Nst+2?"OK":"FAIL", minM,argM,minO,argO); }
  }
  return 0;
}
