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
int main(int argc,char**argv){
  W=atoi(argv[1]); int r=atoi(argv[2]); int k=argc-3; int *a=malloc(sizeof(int)*k); long D=0; long F=0;
  for(int i=0;i<k;i++){a[i]=atoi(argv[3+i]); D+=a[i]-1; F+=a[i]/r; if(a[i]%r==0){printf("RDIV\n");return 0;}}
  long X=(D+1)/2; // need alpha on [0,X]
  uint64_t *al=calloc((size_t)(X+1)*W,8), *pre=calloc((size_t)(X+2)*W,8);
  AT(al,0)[0]=1; long len=1; // current length (degree+1), truncated at X+1
  for(int i=0;i<k;i++){ int ai=a[i]; if(ai<=1) continue;
    long nlen=len+ai-1; if(nlen>X+1) nlen=X+1;
    memset(AT(pre,0),0,8*W);
    for(long j=0;j<nlen;j++){ if(j<len) bn_add(AT(pre,j+1),AT(pre,j),AT(al,j)); else memcpy(AT(pre,j+1),AT(pre,j),8*W);}
    for(long j=0;j<nlen;j++){ long lo=j-ai+1; if(lo<0) lo=0; bn_sub(AT(al,j),AT(pre,j+1),AT(pre,lo)); }
    len=nlen; }
  // delta_x for 0<=x<=X : delta = al[x]-al[x-1]
  uint64_t *dl=calloc((size_t)(X+1)*W,8);
  memcpy(AT(dl,0),AT(al,0),8*W);
  for(long x=1;x<=X;x++) bn_sub(AT(dl,x),AT(al,x),AT(al,x-1));
  free(pre);
  if(bn_neg(AT(al,X))){printf("OVERFLOW\n");return 1;}
  double l2peak=bn_log2(AT(al,X));
  // pairs
  long Nst=1L<<60, beta=1L<<60; int npairs=0;
  int maxL=(int)(2*(D+1)/r+8);
  uint64_t *As=calloc((size_t)(maxL+8)*W,8); uint64_t *tmp=calloc(W*4,8), *tmp2=tmp+W;
  long *ylist=malloc(sizeof(long)*(maxL+8));
  // store per-pair results
  int *pC=malloc(sizeof(int)*r); long *pn=malloc(sizeof(long)*r), *pb=malloc(sizeof(long)*r); int *pki=malloc(sizeof(int)*r); double *pmarg=malloc(sizeof(double)*r);
  uint64_t *zero=calloc(W,8);
  for(int C=1;C<r;C++){ if(((C-(D+1))%2+2)%2) continue;
    int L=0; for(int kk=0;;kk++){ long Z=(long)(kk/2)*2*r+((kk%2==0)?C:2*r-C); if(Z>D+1) break; long x=(D+1-Z)/2; ylist[L++]=x; }
    // y_n = dl[ylist[n]] for n<L else 0
    // A_n
    memset(AT(As,0),0,8*W);
    for(int n=0;n<L+6;n++){ const uint64_t *yv = (n<L)?AT(dl,ylist[n]):zero; uint64_t *prev = n? AT(As,n-1):zero;
      if(n%2==0) bn_add(AT(As,n),prev,yv); else bn_sub(AT(As,n),prev,yv); }
    #define YV(n) (((n)<L)?AT(dl,ylist[(n)]):zero)
    // a_n = (-1)^n A_n ; nstar = first n with a_n<0
    long ns=-1; for(int n=0;n<L+6;n++){ int s=bn_sgn(AT(As,n)); int an_s=(n%2==0)?s:-s; if(an_s<0){ns=n;break;} }
    if(ns<0) continue;
    if(((ns-(F+1))%2+2)%2){printf("PARITY_ANOMALY C=%d n=%ld\n",C,ns);}
    // a_m as bn: am = (m even)? A_m : -A_m ; G_b = a_{b-2}+y_b ; beta_C largest b == ns mod 2 >= ns with G>=0 ... start b=ns+2
    long b=ns+2;
    while(1){ long m=b-2; const uint64_t *Am = (m< L+6)? AT(As,m) : AT(As,L+5);
      if(m%2==0) memcpy(tmp,Am,8*W); else bn_sub(tmp,zero,Am);
      bn_add(tmp2,tmp,YV(b)); if(bn_neg(tmp2)) break; b+=2; if(b>L+20) break; }
    long betaC=b-2;
    // KI margin: |a_n|+y_{n+1}-y_{n+2}-y_{n+4}
    { const uint64_t *An=AT(As,ns); if(bn_neg(An)) bn_sub(tmp,zero,An); else memcpy(tmp,An,8*W);
      bn_add(tmp,tmp,YV(ns+1)); bn_sub(tmp,tmp,YV(ns+2)); bn_sub(tmp,tmp,YV(ns+4));
      pki[npairs]= bn_sgn(tmp)>0; uint64_t *dd=tmp+2*W; bn_add(dd,YV(ns+2),YV(ns+4));
      if(bn_iszero(dd)) pmarg[npairs]=1e300; else { double l=bn_log2(tmp)-bn_log2(dd); pmarg[npairs]=(bn_sgn(tmp)>=0?1:-1)*exp2(l);} }
    pC[npairs]=C; pn[npairs]=ns; pb[npairs]=betaC; npairs++;
    if(ns<Nst) Nst=ns; if(betaC<beta) beta=betaC;
  }
  int kifail=0, kifailbind=0; double minmarg=1e300; int argmin=-1;
  for(int i=0;i<npairs;i++){ if(!pki[i]){kifail++; if(pn[i]==Nst) kifailbind++;} if(pmarg[i]<minmarg){minmarg=pmarg[i];argmin=i;} }
  int cbmin=1<<30,cbmax=-1,cb2=0; for(int i=0;i<npairs;i++) if(pn[i]==Nst){ if(pC[i]<cbmin)cbmin=pC[i]; if(pC[i]>cbmax)cbmax=pC[i]; if(pb[i]<=Nst+2) cb2++; }
  int c2min=1<<30,c2max=-1; for(int i=0;i<npairs;i++) if(pb[i]<=Nst+2){ if(pC[i]<c2min)c2min=pC[i]; if(pC[i]>c2max)c2max=pC[i]; }
  printf("binding C in [%d,%d], pairs with beta<=N*+2: C in [%d,%d] ",cbmin,cbmax,c2min,c2max);
  printf("r=%d k=%d D=%ld F=%ld log2peak=%.1f Nstar=%ld beta=%ld S2=%s pairs=%d KIfail=%d KIfail_binding=%d minmarg=%.3e(C=%d,n=%ld)\n",
     r,k,D,F,l2peak,Nst,beta,(beta<=Nst+2)?"OK":"FAIL",npairs,kifail,kifailbind,minmarg,argmin>=0?pC[argmin]:-1,argmin>=0?pn[argmin]:-1);
  if(argc>0 && getenv("VERB")){ for(int i=0;i<npairs;i++) if(pn[i]<=Nst+2) printf("  C=%d n*=%ld beta=%ld KI=%d marg=%.3e\n",pC[i],pn[i],pb[i],pki[i],pmarg[i]); }
  return 0;
}
