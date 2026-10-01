/* Brute-force A225034 directly from the definition:
   a(n) = #{binary words with exactly n 1's and m 0's, 0<=m<=n, not containing 101}.
   Enumerates every word with exactly n ones of each length n+m (Gosper's hack). */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
int main(int argc,char**argv){
  int N = argc>1?atoi(argv[1]):14;
  printf("0 1\n"); /* n=0: only the empty word */
  for(int n=1;n<=N;n++){
    unsigned long long total=0;
    for(int m=0;m<=n;m++){
      int L=n+m;
      uint64_t w=(1ULL<<n)-1, lim=1ULL<<L;
      while(w<lim){
        uint64_t bad = w & ~(w>>1) & (w>>2); /* bit i set iff positions i,i+1,i+2 read 1,0,1 */
        if(!bad) total++;
        uint64_t c=w&-w, r=w+c; w=(((r^w)>>2)/c)|r;   /* next word with n ones */
      }
    }
    printf("%d %llu\n",n,total); fflush(stdout);
  }
  return 0;
}
