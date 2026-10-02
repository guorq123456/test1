// Exact computation of delta_x = alpha_x - alpha_{x-1}, x=0..X=(D+1)/2 for A=prod[a_i]_q,
// output as doubles scaled by 2^-E where E = floor(log2 alpha_X) (alpha_X ~ central coefficient).
// HEX mode: if env HEX set, prints delta_x exactly as signed hex.
// Usage: dumpdelta W r a1..ak > file ; first line: r k D F E ; then X+1 lines of delta_x*2^-E
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
static double bn_scaled(const uint64_t *x,int E){ uint64_t t[256]; int neg=bn_neg(x);
  if(neg){uint64_t z[256];memset(z,0,8*W);bn_sub(t,z,x);} else memcpy(t,x,8*W);
  int i=W-1; while(i>=0&&t[i]==0) i--; if(i<0) return 0.0;
  long double v=(long double)t[i]; if(i>0) v+=(long double)t[i-1]/18446744073709551616.0L; if(i>1) v+=(long double)t[i-2]/18446744073709551616.0L/18446744073709551616.0L;
  long double r=ldexpl(v,64*i-E); return neg?-(double)r:(double)r;}
#define AT(arr,j) ((arr)+(size_t)(j)*W)
int main(int argc,char**argv){
  W=atoi(argv[1]); int r=atoi(argv[2]); int k=argc-3; int *a=malloc(sizeof(int)*k); long D=0, F=0;
  for(int i=0;i<k;i++){a[i]=atoi(argv[3+i]); D+=a[i]-1; F+=a[i]/r;}
  long X=(D+1)/2;
  uint64_t *al=calloc((size_t)(X+1)*W,8), *pre=calloc((size_t)(X+2)*W,8);
  AT(al,0)[0]=1; long len=1;
  for(int i=0;i<k;i++){ int ai=a[i]; if(ai<=1) continue;
    long nlen=len+ai-1; if(nlen>X+1) nlen=X+1;
    memset(AT(pre,0),0,8*W);
    for(long j=0;j<nlen;j++){ if(j<len) bn_add(AT(pre,j+1),AT(pre,j),AT(al,j)); else memcpy(AT(pre,j+1),AT(pre,j),8*W);}
    for(long j=0;j<nlen;j++){ long lo=j-ai+1; if(lo<0) lo=0; bn_sub(AT(al,j),AT(pre,j+1),AT(pre,lo)); }
    len=nlen; }
  if(bn_neg(AT(al,X))){fprintf(stderr,"OVERFLOW\n");return 1;}
  // E
  int i=W-1; while(i>=0&&AT(al,X)[i]==0) i--; int E=64*i+(63-__builtin_clzll(AT(al,X)[i]));
  printf("%d %d %ld %ld %d\n",r,k,D,F,E);
  uint64_t *d=calloc(W,8);
  if(getenv("HEX")){ uint64_t *t=calloc(W,8),*z=calloc(W,8);
    for(long x=0;x<=X;x++){ if(x==0) memcpy(d,AT(al,0),8*W); else bn_sub(d,AT(al,x),AT(al,x-1));
      int neg=bn_neg(d); if(neg) bn_sub(t,z,d); else memcpy(t,d,8*W);
      int i=W-1; while(i>0&&t[i]==0) i--; if(neg) putchar('-'); printf("%lx",t[i]); for(int j=i-1;j>=0;j--) printf("%016lx",t[j]); putchar('\n'); }
    return 0; }
  printf("%.17g\n",bn_scaled(AT(al,0),E));
  for(long x=1;x<=X;x++){ bn_sub(d,AT(al,x),AT(al,x-1)); printf("%.17g\n",bn_scaled(d,E)); }
  return 0;
}
