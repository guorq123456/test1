#include <stdio.h>
#include <stdint.h>
typedef uint64_t u64;
static int jacobi(u64 a, u64 n){ int r=1; a%=n;
  while(a){ int tz=__builtin_ctzll(a); a>>=tz;
    if((tz&1)&&((n&7)==3||(n&7)==5)) r=-r;
    if((a&3)==3&&(n&3)==3) r=-r;
    u64 t=a; a=n%t; n=t; }
  return n==1?r:0; }
int main(){ printf("%d %d %d %d\n", jacobi(29,31), jacobi(2,7), jacobi(3,7), jacobi(5,23)); 
 int c=0; for(u64 r=1;r<116;r+=2) c+= jacobi(29, r+116000)==1; printf("count1 %d\n",c); return 0;}
