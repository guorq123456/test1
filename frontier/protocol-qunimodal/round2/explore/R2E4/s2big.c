// Exact S2 evaluator with 512-bit fixed-width signed integers (two's complement, 8 limbs).
// stdin lines: "r k a1 ... ak"   (r divides no a_i; fit box enforced by caller)
// stdout per line: "r k a1..ak | F T6 Bstar shape par pat" where pat = U membership on b=F+1..T6+2,
//   shape 0=interval 1=gap(only B*-1 missing) 2=bad; b<=F taken unimodal (Thm T1). Flags VIOL if S2 fails or B*>T6.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define NL 8
typedef struct { uint64_t w[NL]; } Z;
static inline void zset(Z*x,long long v){ uint64_t f=v<0?~0ULL:0; x->w[0]=(uint64_t)v; for(int i=1;i<NL;i++) x->w[i]=f; }
static inline void zadd(Z*r,const Z*a,const Z*b){ unsigned __int128 c=0; for(int i=0;i<NL;i++){ c+=(unsigned __int128)a->w[i]+b->w[i]; r->w[i]=(uint64_t)c; c>>=64; } }
static inline void zsub(Z*r,const Z*a,const Z*b){ uint64_t br=0; for(int i=0;i<NL;i++){ uint64_t x=a->w[i], y=b->w[i]; uint64_t t=x-y-br; br = (x<y)||(x==y&&br) ? 1:0; if(x<y+br && !(y==~0ULL&&br)) ; r->w[i]=t; } }
static inline int zcmp(const Z*a,const Z*b){ int64_t ta=(int64_t)a->w[NL-1], tb=(int64_t)b->w[NL-1]; if(ta!=tb) return ta<tb?-1:1;
  for(int i=NL-2;i>=0;i--) if(a->w[i]!=b->w[i]) return a->w[i]<b->w[i]?-1:1; return 0; }
static inline int zsign(const Z*a){ if((int64_t)a->w[NL-1]<0) return -1; for(int i=0;i<NL;i++) if(a->w[i]) return 1; return 0; }
static Z A[8192], T[8192], d[16384], ZERO;
int main(void){ int nnmode = getenv("NNEG")!=0;
  int r,k; static int a[128]; zset(&ZERO,0);
  while(scanf("%d %d",&r,&k)==2){
    for(int i=0;i<k;i++) scanf("%d",&a[i]);
    int D=0; zset(&A[0],1);
    for(int i=0;i<k;i++){ int Ai=a[i], nd=D+Ai-1; Z s; zset(&s,0);
      for(int t=0;t<=nd;t++){ if(t<=D) zadd(&s,&s,&A[t]); if(t-Ai>=0&&t-Ai<=D) zsub(&s,&s,&A[t-Ai]); T[t]=s; }
      D=nd; memcpy(A,T,sizeof(Z)*(D+1)); }
    int F=0; for(int i=0;i<k;i++) F+=a[i]/r;
    Z G[64]; for(int t=0;t<r;t++) zset(&G[t],0); for(int i=0;i<=D;i++) zadd(&G[i%r],&G[i%r],&A[i]);
    int mu=r-1; for(int t=r-1;t>=0;t--){ int ok=1; for(int j=t;j<r-1;j++) if(zcmp(&G[j],&G[j+1])<0) ok=0; if(ok) mu=t; else break; }
    int T6=1+(D+1-2*mu)/r;
    int bmax=T6+2; if(bmax<F+2) bmax=F+2; int L=(D+r*(bmax-1))/2+2;
    for(int i=0;i<L;i++){ Z x = i>=r? d[i-r]:ZERO; if(i<=D) zadd(&x,&x,&A[i]); if(i>=1&&i-1<=D) zsub(&x,&x,&A[i-1]); d[i]=x; }
    static char U[8192]; static int NN[8192]; int Bs=0;
    for(int b=1;b<=bmax;b++){
      if(b<=F){U[b]=1;Bs=b;continue;}
      int N=D+r*(b-1), h=N/2, ok=1;
      int nn=0; for(int i=1;i<=h&&(ok||nnmode);i++){ const Z*y = i-r*b>=0? &d[i-r*b] : &ZERO; if(zcmp(&d[i],y)<0){ ok=0; nn++;} }
      U[b]=ok; NN[b]=nn; if(ok) Bs=b; }
    int miss=0,missat=-1,shape; for(int b=1;b<=Bs;b++) if(!U[b]){miss++;missat=b;}
    shape = miss==0?0:((miss==1&&missat==Bs-1)?1:2);
    int par=((Bs-1-F)%2==0);
    printf("%d %d",r,k); for(int i=0;i<k;i++) printf(" %d",a[i]);
    printf(" | %d %d %d %d %d ",F,T6,Bs,shape,par);
    for(int b=F+1;b<=bmax;b++) putchar(U[b]?'1':'0');
    if(nnmode){ putchar(' '); for(int b=F+1;b<=bmax;b++) printf("%d,",NN[b]); }
    if(shape==2||!par||Bs>T6) printf(" VIOL");
    putchar('\n'); if(nnmode) fflush(stdout);
  }
  return 0;
}
