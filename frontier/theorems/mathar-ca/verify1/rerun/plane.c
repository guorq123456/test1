/* Independent plane implementation (no torus): outer-totalistic 5-neighbour CA,
   new state = bit (c + 2*s) of the Wolfram code. Cells outside the box |x|,|y|<=N+1
   are held at the current background value bg (bg_{t+1} = bit (bg + 8*bg) of code).
   Prints, for each stage n=0..N, the x-axis digits x=0..n (right readout) for the given code. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv){
  int code = atoi(argv[1]); int N = atoi(argv[2]);
  int W = 2*N+5, C = N+2;  /* index = coord + C; box |x|,|y|<=N+1 is indices 1..W-2; ring 0 and W-1 */
  unsigned char *a = calloc((size_t)W*W,1), *b = calloc((size_t)W*W,1);
  int bit[10]; for(int v=0;v<10;v++) bit[v]=(code>>v)&1;
  a[(size_t)C*W+C]=1; int bg=0;
  for(int n=0;n<=N;n++){
    /* output right readout at stage n */
    for(int x=0;x<=n;x++) putchar('0'+a[(size_t)C*W+C+x]);
    putchar('\n');
    if(n==N) break;
    int nbg = bit[bg+8*bg];
    for(int i=0;i<W;i++) for(int j=0;j<W;j++){
      if(i==0||j==0||i==W-1||j==W-1){ b[(size_t)i*W+j]=nbg; continue; }
      int c=a[(size_t)i*W+j];
      int s=a[(size_t)(i-1)*W+j]+a[(size_t)(i+1)*W+j]+a[(size_t)i*W+j-1]+a[(size_t)i*W+j+1];
      b[(size_t)i*W+j]=bit[c+2*s];
    }
    unsigned char *t=a; a=b; b=t; bg=nbg;
  }
  return 0;
}
