// Ryser permanent of a 0/1 square matrix (k<=40) computed modulo 2^64
// (exact when the permanent is < 2^64). Gray-code enumeration, parallel over
// the top T bits of the column subset. Input: k, then k rows of k 0/1 entries.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned long long u64; typedef long long i64;
int main(){
  int k; if(scanf("%d",&k)!=1) return 1; int a[40][40];
  for(int i=0;i<k;i++) for(int j=0;j<k;j++) scanf("%d",&a[i][j]);
  int T = 6; if(T>k) T=k; int L=k-T;      // low L bits by Gray code, high T bits fixed per chunk
  u64 total=0;
  #pragma omp parallel for schedule(dynamic,1) reduction(+:total)
  for(int hi=0; hi<(1<<T); hi++){
    i64 r[40]; int par=0;
    for(int i=0;i<k;i++){ r[i]=0; for(int t=0;t<T;t++) if(hi>>t&1) r[i]+=a[i][L+t]; }
    par=__builtin_popcount(hi);
    u64 acc=0; unsigned long long g=0;
    for(u64 s=0; s < (1ULL<<L); s++){
      if(s){ int j=__builtin_ctzll(s); g ^= 1ULL<<j; int sign = (g>>j&1)? 1 : -1;
        for(int i=0;i<k;i++) r[i]+=sign*a[i][j]; par^=1; }
      u64 p=1; for(int i=0;i<k;i++){ p*= (u64)r[i]; if(!p) break; }
      if(par&1) acc-=p; else acc+=p;
    }
    total+=acc;
  }
  if(k&1) total = (u64)(-(i64)total);
  printf("%llu\n", total);
}
