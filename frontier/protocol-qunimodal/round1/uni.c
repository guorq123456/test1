// Ground truth: is P = prod [a_i]_q * [b]_{q^r} weakly unimodal?
// stdin lines: r k a1 ... ak b   -> stdout: 1 (unimodal) or 0
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef __int128 I;
int main(void){
  int r,k; static int a[512]; static I c[1<<16], d[1<<16];
  while (scanf("%d %d",&r,&k)==2){
    for(int i=0;i<k;i++) if(scanf("%d",&a[i])!=1) return 1;
    int b; if(scanf("%d",&b)!=1) return 1;
    int deg=0; c[0]=1;
    for(int i=0;i<k;i++){ // multiply by [a]_q via sliding window
      int A=a[i], nd=deg+A-1; I s=0;
      for(int t=0;t<=nd;t++){ if(t<=deg) s+=c[t]; if(t-A>=0 && t-A<=deg) s-=c[t-A]; d[t]=s; }
      deg=nd; memcpy(c,d,sizeof(I)*(deg+1));
    }
    // multiply by [b]_{q^r}
    int nd=deg+r*(b-1);
    for(int t=0;t<=nd;t++){ I s=0; for(int y=0;y<b;y++){ int u=t-r*y; if(u>=0&&u<=deg) s+=c[u]; } d[t]=s; }
    deg=nd;
    int i=0; while(i<deg && d[i]<=d[i+1]) i++; while(i<deg && d[i]>=d[i+1]) i++;
    printf("%d\n", i==deg ? 1:0);
  }
  return 0;
}
