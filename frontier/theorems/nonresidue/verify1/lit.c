// Literal computation of A112046 and A112051 (streamed), own Jacobi.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>
typedef uint64_t u64;
static int jacobi(u64 a, u64 n){ // n odd positive
  int r=1; a%=n;
  while(a){
    int tz=__builtin_ctzll(a); a>>=tz;
    if((tz&1) && ((n&7)==3||(n&7)==5)) r=-r;
    if((a&3)==3 && (n&3)==3) r=-r;
    u64 t=a; a=n%t; n=t;
  }
  return n==1?r:0;
}
static u64 f(u64 m){ u64 k=1; while(jacobi(k,m)==1) k++; return k; }
int main(int argc,char**argv){
  u64 IMAX=strtoull(argv[1],0,10);
  const u64 CH=50000000ULL;
  uint32_t *buf=malloc(CH*sizeof(uint32_t));
  // value set: values are < 2^32 surely for this range; use bitmap over values up to VMAX
  const u64 VMAX=1ULL<<22; unsigned char *inS=calloc(VMAX,1);
  u64 last=1; // a(1)=1
  u64 nterms=1; FILE*out=fopen(argv[2],"w"); fprintf(out,"1 1\n");
  u64 maxval=0, bigsq=0;
  // S = values at indices 1..a(n-1). Literal scan.
  int started=0;
  for(u64 base=1; base<=IMAX; base+=CH){
    u64 len = (base+CH-1<=IMAX)?CH:(IMAX-base+1);
    #pragma omp parallel for schedule(dynamic,100000)
    for(u64 j=0;j<len;j++){ u64 i=base+j; buf[j]=(uint32_t)f(2*i+1); }
    for(u64 j=0;j<len;j++){
      u64 i=base+j; u64 v=buf[j];
      if(v>maxval) maxval=v;
      if(v*v > 2*i+1){ printf("f(m)^2>m at m=%llu f=%llu\n",(unsigned long long)(2*i+1),(unsigned long long)v); bigsq++; }
      if(v>=VMAX){fprintf(stderr,"value overflow\n");return 1;}
      if(i==1){ inS[v]=1; continue; }      // S = {A112046(1)}
      // i > last always here; scanning for first i>last with value not in S
      if(!inS[v]){ // a(n)=i
        inS[v]=1; last=i; nterms++;
        fprintf(out,"%llu %llu\n",(unsigned long long)nterms,(unsigned long long)i);
      } else {
        // value already in S; S unchanged (adding it is a no-op)
      }
    }
  }
  fclose(out);
  printf("IMAX=%llu nterms=%llu maxval=%llu bigsq=%llu\n",(unsigned long long)IMAX,(unsigned long long)nterms,(unsigned long long)maxval,(unsigned long long)bigsq);
  return 0;
}
