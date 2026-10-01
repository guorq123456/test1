/* Brute force A087125 from its definition: k >= 0 such that the hex number 3k(k+1)+1 is triangular,
   i.e. 8(3k(k+1)+1)+1 = 24k^2+24k+9 is a perfect square.  Prints all such k <= K. */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
typedef unsigned __int128 u128;
int main(int argc,char**argv){
  unsigned long long K = strtoull(argv[1],0,10);
  for(unsigned long long k=0;k<=K;k++){
    u128 N = (u128)24*k*k + (u128)24*k + 9;
    unsigned long long r = (unsigned long long)sqrtl((long double)N);
    while((u128)r*r > N) r--;
    while((u128)(r+1)*(r+1) <= N) r++;
    if((u128)r*r == N) printf("%llu\n",k);
  }
  return 0;
}
