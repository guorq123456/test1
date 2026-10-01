// Single-permutation |RP(Grid(w))| via sparse row DP. w is 0-based.
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned long long u64;
static int NMAX=0; static u64 *A,*B; static int *LA,*LB;
static void ensure(int n){ if(n<=NMAX) return; NMAX=n;
  A=realloc(A,sizeof(u64)<<n); B=realloc(B,sizeof(u64)<<n); memset(A,0,sizeof(u64)<<n); memset(B,0,sizeof(u64)<<n);
  LA=realloc(LA,sizeof(int)<<n); LB=realloc(LB,sizeof(int)<<n); }
u64 rp1(int n, const int *w){
  if(n==1) return 1;
  ensure(n);
  u64 *src=A,*dst=B; int *ls=LA,*ld=LB; int nl=1; ls[0]=0; src[0]=1;
  for(int i=0;i<n;i++){ int c0=w[i]; int nd=0;
    for(int t=0;t<nl;t++){ int m=ls[t]; u64 v=src[m]; src[m]=0;
      int mm=m;
      if(i>0){ if(!((mm>>c0)&1)) continue; }
      if(i<n-1) mm&=~(1<<c0); else mm|=(1<<c0);
      if(c0>0){
        for(int a=0;a<c0;a++){ if((mm>>a)&1) continue; int m2=mm|(1<<a);
          if(c0<n-1){ for(int b=c0+1;b<n;b++){ if((m2>>b)&1) continue; int m3=m2|(1<<b);
              if(!dst[m3]) ld[nd++]=m3; dst[m3]+=v; } }
          else { if(!dst[m2]) ld[nd++]=m2; dst[m2]+=v; } }
      } else {
        for(int b=c0+1;b<n;b++){ if((mm>>b)&1) continue; int m3=mm|(1<<b);
          if(!dst[m3]) ld[nd++]=m3; dst[m3]+=v; }
      }
    }
    u64 *tp=src; src=dst; dst=tp; int *tl=ls; ls=ld; ld=tl; nl=nd;
  }
  u64 r=0; int full=(1<<n)-1;
  for(int t=0;t<nl;t++){ if(ls[t]==full) r=src[ls[t]]; src[ls[t]]=0; }
  return r;
}
