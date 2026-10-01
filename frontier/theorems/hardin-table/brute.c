/* Naive brute force: enumerate ALL 0..1 arrays of size (n+1)x(k+1) and test the
   OEIS A253435 condition directly.
   D(i,j) = x[i][j] + x[i+1][j+1] - x[i][j+1] - x[i+1][j]   (diagonal minus antidiagonal)
   horizontally:            D(i,j)   <= D(i,j+1)
   vertically:              D(i,j)   <= D(i+1,j)
   ne-to-sw antidiagonally: D(i,j+1) <= D(i+1,j)
   mode selects variant interpretations (for sanity: only mode 0 should match OEIS).
   usage: brute n k mode */
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){
  int n=atoi(argv[1]),k=atoi(argv[2]),mode=argc>3?atoi(argv[3]):0;
  int R=n+1,C=k+1,cells=R*C; long long cnt=0;
  int x[16][16],D[16][16];
  for(unsigned long long m=0;m<(1ULL<<cells);m++){
    for(int i=0;i<R;i++)for(int j=0;j<C;j++)x[i][j]=(m>>(i*C+j))&1;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++)D[i][j]=x[i][j]+x[i+1][j+1]-x[i][j+1]-x[i+1][j];
    int ok=1;
    for(int i=0;i<n&&ok;i++)for(int j=0;j<k&&ok;j++){
      if(j+1<k && !(D[i][j]<=D[i][j+1]))ok=0;
      if(i+1<n && !(D[i][j]<=D[i+1][j]))ok=0;
      if(i+1<n && j+1<k){
        if(mode==0 && !(D[i][j+1]<=D[i+1][j]))ok=0;   /* ne-to-sw nondecreasing */
        if(mode==1 && !(D[i+1][j]<=D[i][j+1]))ok=0;   /* sw-to-ne (alternative) */
        if(mode==2 && !(D[i][j]<=D[i+1][j+1]))ok=0;   /* nw-to-se (alternative) */
      }
    }
    cnt+=ok;
  }
  printf("%d %d %d %lld\n",n,k,mode,cnt);
  return 0;
}
