// Independent brute force of A087125: k>=0 such that hex number 3k(k+1)+1 is triangular m(m+1)/2.
// Two-pointer merge walk over hex numbers and triangular numbers using exact 128-bit integers.
#include <stdio.h>
#include <stdlib.h>
typedef unsigned __int128 u128;
static void pr(u128 x){char b[64];int i=63;b[i]=0;if(!x){printf("0");return;}while(x){b[--i]='0'+(int)(x%10);x/=10;}printf("%s",b+i);}
int main(int argc,char**argv){
  unsigned long long K = strtoull(argv[1],0,10);
  u128 h=1;            // hex(k) = 3k(k+1)+1, k=0
  u128 t=0; unsigned long long m=0; // tri(m) = m(m+1)/2
  for(unsigned long long k=0;k<=K;k++){
    while(t<h){ m++; t+=m; }
    if(t==h){ printf("k=%llu m=%llu hex=",k,m); pr(h); printf("\n"); fflush(stdout);}
    h += 6*(u128)(k+1);  // hex(k+1)-hex(k) = 6(k+1)
  }
  printf("done K=%llu\n",K);
  return 0;
}
