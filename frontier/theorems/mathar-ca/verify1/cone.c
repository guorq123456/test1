/* Exact plane evolution from a single seed via a shrinking light cone.
   Start: box |x|,|y|<=H0=2N+1, all 0 except the origin (exact on the plane).
   Stage t is computed only on |x|,|y|<=H0-t, using stage t-1 values on the
   bigger box, so no boundary condition / background / torus is ever assumed.
   Rule: new = bit_{c+2s}(code).  Prints for n=0..N:
   n R L U D  where R = cells (0,0)..(n,0), L = (-n,0)..(0,0),
   U = (0,0)..(0,n), D = (0,-n)..(0,0)  (as 0/1 strings, leading zeros kept). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
int main(int argc,char**argv){
  int code=atoi(argv[1]); int N=atoi(argv[2]);
  int H0=2*N+1, W=2*H0+1;
  uint8_t *a=calloc((size_t)W*W,1), *b=calloc((size_t)W*W,1);
  #define IX(x,y) ((size_t)((y)+H0)*W + (size_t)((x)+H0))
  a[IX(0,0)]=1;
  char *buf=malloc(N+2);
  for(int t=0;t<=N;t++){
    if(t>0){
      int H=H0-t;
      for(int y=-H;y<=H;y++){
        uint8_t *c=a+IX(0,y), *up=a+IX(0,y+1), *dn=a+IX(0,y-1), *o=b+IX(0,y);
        for(int x=-H;x<=H;x++){
          int v=c[x]+2*(c[x-1]+c[x+1]+up[x]+dn[x]);
          o[x]=(uint8_t)((code>>v)&1);
        }
      }
      uint8_t*tmp=a;a=b;b=tmp;
    }
    printf("%d ",t);
    for(int x=0;x<=t;x++) buf[x]='0'+a[IX(x,0)]; buf[t+1]=0; printf("%s ",buf);
    for(int x=-t;x<=0;x++) buf[x+t]='0'+a[IX(x,0)]; buf[t+1]=0; printf("%s ",buf);
    for(int y=0;y<=t;y++) buf[y]='0'+a[IX(0,y)]; buf[t+1]=0; printf("%s ",buf);
    for(int y=-t;y<=0;y++) buf[y+t]='0'+a[IX(0,y)]; buf[t+1]=0; printf("%s\n",buf);
  }
  return 0;
}
