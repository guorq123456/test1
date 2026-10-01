#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
int main(int argc,char**argv){
  int LMAX=(argc>1)?atoi(argv[1]):30;
  static unsigned long long cnt[64];
  for(int L=0;L<=LMAX;L++){
    uint64_t lim=1ULL<<L;
    uint64_t mask = (L>=3)? ((1ULL<<(L-2))-1):0;
    for(uint64_t x=0;x<lim;x++){
      int ones=__builtin_popcountll(x);
      int zeros=L-ones;
      if(zeros>ones) continue;
      if(x & (~(x>>1)) & (x>>2) & mask) continue;
      cnt[ones]++;
    }
  }
  for(int n=0;n<=LMAX/2;n++) printf("%d %llu\n",n,cnt[n]);
  return 0;
}
